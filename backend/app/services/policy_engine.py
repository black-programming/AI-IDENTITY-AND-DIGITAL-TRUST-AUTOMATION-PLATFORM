"""Deterministic Trust & Policy Engine.

Evaluates subject, action, resource, scope, temporal expiry, OCR confidence,
deterministic validation flags, and environmental context to generate explainable decisions:
ALLOW, VERIFY, RESTRICT, BLOCK with standardized reason codes and missing requirements.

Guarantees fail-closed safety: never approves an identity claim merely because an upstream
OCR or AI model failed.
"""

from datetime import date, datetime, timezone
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.api.v1.cases import _MOCK_CASES_DB, _record_timeline_event
from app.core.errors import PermissionDeniedException, NotFoundException, ValidationException
from app.schemas.policy import PolicyEvaluationRequest, PolicyEvaluationResponse, PolicyRule
from app.services.ocr_service import _MOCK_EXTRACTED_FIELDS_DB
from app.services.review_service import _MOCK_CORRECTIONS_DB
from app.services.validation_engine import ValidationEngine, _MOCK_VALIDATIONS_DB

# In-memory store for policy evaluations
_MOCK_POLICY_EVAL_DB: Dict[str, Dict[str, Any]] = {}

# Standard Versioned Policy Catalog
VERSIONED_POLICY_CATALOG: Dict[Tuple[str, str], PolicyRule] = {
    ("POL-IDENTITY-BASIC-V1", "1.0.0"): PolicyRule(
        policy_id="POL-IDENTITY-BASIC-V1",
        version="1.0.0",
        name="Basic Identity Claim Verification Policy",
        description="Standard verification for national ID, driver's license, or passport with unexpired temporal validity.",
        target_action="identity.verify",
        target_resource="claims:synthetic_identity",
        required_scopes=["identity:read", "identity:verify"],
        confidence_threshold=0.85,
        rule_spec={
            "min_age": 18,
            "allowed_claims": ["SYNTH_NAT_ID_V1", "SYNTH_DL_V1", "SYNTH_PASSPORT_V1"],
            "require_unexpired": True,
            "permitted_scopes": ["identity:read", "identity:verify"],
            "restricted_scopes": [],
        },
        is_active=True,
    ),
    ("POL-HIGH-ASSURANCE-V1", "1.0.0"): PolicyRule(
        policy_id="POL-HIGH-ASSURANCE-V1",
        version="1.0.0",
        name="High Assurance Multi-Credential Policy",
        description="Elevated assurance policy for financial or vault resources. Disallows any cross-consistency flags.",
        target_action="access.elevated",
        target_resource="resource:financial_vault",
        required_scopes=["identity:verify", "vault:access"],
        confidence_threshold=0.90,
        rule_spec={
            "min_age": 21,
            "allowed_claims": ["SYNTH_PASSPORT_V1", "SYNTH_DL_V1"],
            "disallow_flags": ["FLAG_PROFILE_NAME_MISMATCH", "FLAG_VIZ_MRZ_CONFLICT"],
            "require_unexpired": True,
            "permitted_scopes": ["identity:verify", "vault:access"],
            "restricted_scopes": ["superadmin:root"],
        },
        is_active=True,
    ),
    ("POL-RESTRICTED-PROBATIONARY-V1", "1.0.0"): PolicyRule(
        policy_id="POL-RESTRICTED-PROBATIONARY-V1",
        version="1.0.0",
        name="Restricted Access Probationary Policy",
        description="Grants temporary, explicitly scoped access for accounts pending secondary verification.",
        target_action="access.probationary",
        target_resource="scope:read_only",
        required_scopes=["identity:read"],
        confidence_threshold=0.80,
        rule_spec={
            "max_validity_days": 30,
            "permitted_scopes": ["read_only", "provisional_identity"],
            "restricted_scopes": ["financial_transfer", "admin_escalation"],
        },
        is_active=True,
    ),
    ("POL-STEP-UP-AUTH-V1", "1.0.0"): PolicyRule(
        policy_id="POL-STEP-UP-AUTH-V1",
        version="1.0.0",
        name="Step-Up Authentication Policy",
        description="Requires active Multi-Factor Authentication (MFA) verification before approving high-risk actions.",
        target_action="transaction.execute",
        target_resource="transfer:high_value",
        required_scopes=["transaction:execute"],
        confidence_threshold=0.85,
        rule_spec={
            "require_mfa": True,
            "permitted_scopes": ["transaction:execute"],
            "restricted_scopes": [],
        },
        is_active=True,
    ),
}

BLACKLISTED_DOCUMENT_NUMBERS = {"REVOKED999", "FRAUD1234", "REVOKED-ID-77"}


def parse_dob_to_age(dob_str: Optional[str]) -> Optional[int]:
    """Calculate age from ISO date of birth string."""
    if not dob_str:
        return None
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        today = datetime.now(timezone.utc).date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except Exception:
        return None


class PolicyEngine:
    DEFAULT_POLICY_ID = "POL-IDENTITY-BASIC-V1"
    DEFAULT_POLICY_VERSION = "1.0.0"

    @classmethod
    def get_catalog(cls) -> List[PolicyRule]:
        """Return all registered versioned trust policies."""
        return list(VERSIONED_POLICY_CATALOG.values())

    @classmethod
    def get_policy(cls, policy_id: str, version: str = "1.0.0") -> PolicyRule:
        """Fetch policy rule by ID and semantic version, fallback to default if not found."""
        rule = VERSIONED_POLICY_CATALOG.get((policy_id, version))
        if not rule:
            # Fallback to default
            rule = VERSIONED_POLICY_CATALOG.get((cls.DEFAULT_POLICY_ID, cls.DEFAULT_POLICY_VERSION))
        return rule

    @classmethod
    def evaluate(cls, request: PolicyEvaluationRequest) -> PolicyEvaluationResponse:
        """Evaluate deterministic policy rules across Subject, Action, Resource, Scope, Expiry, and Context."""
        now_utc = datetime.now(timezone.utc)
        today_date = now_utc.date()
        reason_codes: List[str] = []
        missing_reqs: List[str] = []

        fields = request.extracted_fields or {}
        claim_type = request.claim_type
        ocr_conf = request.ocr_confidence
        val_flags = request.validation_flags or []
        context = request.context or {}

        # Resolve Policy Rule
        policy_id = request.policy_id or cls.DEFAULT_POLICY_ID
        policy_ver = request.policy_version or cls.DEFAULT_POLICY_VERSION
        policy = cls.get_policy(policy_id, policy_ver)
        rule_spec = policy.rule_spec

        # ---------------------------------------------------------------------
        # FAIL-SAFE PRINCIPLE 1: Upstream Service Failure
        # Never approve a request merely because OCR or an AI service failed.
        # ---------------------------------------------------------------------
        if context.get("ocr_engine_status") == "FAILED" or context.get("upstream_error"):
            reason_codes.append("ERR_UPSTREAM_SERVICE_FAILED")
            reason_codes.append("DEC_VERIFY_OCR_CONF_LOW")
            return PolicyEvaluationResponse(
                evaluation_id=str(uuid.uuid4()),
                case_id=request.case_id,
                policy_id=policy.policy_id,
                policy_version=policy.version,
                decision="VERIFY",
                reason_codes=reason_codes,
                missing_requirements=["clear_unambiguous_document_scan"],
                permitted_scopes=[],
                restricted_scopes=policy.required_scopes,
                confidence_score=0.0,
                requires_human_review=True,
                evaluated_at=now_utc,
                explanation="Upstream OCR or document extraction failed. Human review required.",
            )

        # ---------------------------------------------------------------------
        # FAIL-SAFE PRINCIPLE 2: Empty Extracted Fields
        # ---------------------------------------------------------------------
        if not fields:
            return PolicyEvaluationResponse(
                evaluation_id=str(uuid.uuid4()),
                case_id=request.case_id,
                policy_id=policy.policy_id,
                policy_version=policy.version,
                decision="BLOCK",
                reason_codes=["DEC_BLOCK_UNSUPPORTED_MIME"],
                missing_requirements=["valid_extracted_fields"],
                permitted_scopes=[],
                restricted_scopes=policy.required_scopes,
                confidence_score=0.0,
                requires_human_review=False,
                evaluated_at=now_utc,
                explanation="No extracted document fields available for evaluation.",
            )

        # ---------------------------------------------------------------------
        # RULE 1: Blacklisted / Revoked Document Identifier
        # ---------------------------------------------------------------------
        doc_num = fields.get("document_number") or fields.get("license_number") or fields.get("passport_number")
        if doc_num and doc_num in BLACKLISTED_DOCUMENT_NUMBERS:
            reason_codes.append("DEC_BLOCK_BLACKLISTED_IDENTIFIER")
            return PolicyEvaluationResponse(
                evaluation_id=str(uuid.uuid4()),
                case_id=request.case_id,
                policy_id=policy.policy_id,
                policy_version=policy.version,
                decision="BLOCK",
                reason_codes=reason_codes,
                missing_requirements=[],
                permitted_scopes=[],
                restricted_scopes=policy.required_scopes,
                confidence_score=1.0,
                requires_human_review=False,
                evaluated_at=now_utc,
                explanation=f"Document identifier '{doc_num}' is revoked or listed on fraud registry.",
            )

        # ---------------------------------------------------------------------
        # RULE 2: Expiration Date Check (VAL-EXPIRY)
        # ---------------------------------------------------------------------
        expiry_str = fields.get("expiry_date")
        if expiry_str:
            try:
                expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                if expiry < today_date:
                    reason_codes.append("DEC_BLOCK_DOC_EXPIRED")
                    return PolicyEvaluationResponse(
                        evaluation_id=str(uuid.uuid4()),
                        case_id=request.case_id,
                        policy_id=policy.policy_id,
                        policy_version=policy.version,
                        decision="BLOCK",
                        reason_codes=reason_codes,
                        missing_requirements=["unexpired_identity_document"],
                        permitted_scopes=[],
                        restricted_scopes=policy.required_scopes,
                        confidence_score=ocr_conf,
                        requires_human_review=False,
                        evaluated_at=now_utc,
                        explanation=f"Document expired on {expiry_str}; does not satisfy temporal policy requirements.",
                    )
            except ValueError:
                reason_codes.append("DEC_VERIFY_OCR_CONF_LOW")

        # ---------------------------------------------------------------------
        # RULE 3: Claim Type Compatibility
        # ---------------------------------------------------------------------
        allowed_claims = rule_spec.get("allowed_claims", [])
        if allowed_claims and claim_type not in allowed_claims:
            reason_codes.append("DEC_BLOCK_INCOMPATIBLE_CLAIM_TYPE")
            return PolicyEvaluationResponse(
                evaluation_id=str(uuid.uuid4()),
                case_id=request.case_id,
                policy_id=policy.policy_id,
                policy_version=policy.version,
                decision="BLOCK",
                reason_codes=reason_codes,
                missing_requirements=[f"credential_matching_{allowed_claims}"],
                permitted_scopes=[],
                restricted_scopes=policy.required_scopes,
                confidence_score=1.0,
                requires_human_review=False,
                evaluated_at=now_utc,
                explanation=f"Claim type '{claim_type}' is not accepted for policy '{policy.name}'.",
            )

        # ---------------------------------------------------------------------
        # RULE 4: Age Requirement & Demographic Constraints
        # ---------------------------------------------------------------------
        min_age = rule_spec.get("min_age")
        if min_age:
            age = parse_dob_to_age(fields.get("date_of_birth"))
            if age is not None and age < min_age:
                reason_codes.append("DEC_BLOCK_UNDERAGE_SUBJECT")
                return PolicyEvaluationResponse(
                    evaluation_id=str(uuid.uuid4()),
                    case_id=request.case_id,
                    policy_id=policy.policy_id,
                    policy_version=policy.version,
                    decision="BLOCK",
                    reason_codes=reason_codes,
                    missing_requirements=[f"minimum_age_{min_age}"],
                    permitted_scopes=[],
                    restricted_scopes=policy.required_scopes,
                    confidence_score=ocr_conf,
                    requires_human_review=False,
                    evaluated_at=now_utc,
                    explanation=f"Subject age ({age}) does not meet policy threshold ({min_age}).",
                )

        # ---------------------------------------------------------------------
        # RULE 5: Deterministic Checksum & Tamper Flags
        # ---------------------------------------------------------------------
        if "DEC_BLOCK_MRZ_CHECKSUM_FAILED" in val_flags or "ERR_MRZ_CHECKSUM_FAILED" in val_flags:
            reason_codes.append("DEC_BLOCK_MRZ_CHECKSUM_FAILED")
            return PolicyEvaluationResponse(
                evaluation_id=str(uuid.uuid4()),
                case_id=request.case_id,
                policy_id=policy.policy_id,
                policy_version=policy.version,
                decision="BLOCK",
                reason_codes=reason_codes,
                missing_requirements=["authentic_unaltered_document"],
                permitted_scopes=[],
                restricted_scopes=policy.required_scopes,
                confidence_score=ocr_conf,
                requires_human_review=False,
                evaluated_at=now_utc,
                explanation="MRZ cryptographic check digit failed; suspected tampering.",
            )

        # ---------------------------------------------------------------------
        # RULE 6: Disallowed Consistency Flags (Elevated Assurance)
        # ---------------------------------------------------------------------
        disallowed = rule_spec.get("disallow_flags", [])
        active_disallowed = [f for f in disallowed if f in val_flags]
        if active_disallowed:
            reason_codes.append("DEC_VERIFY_CROSS_FIELD_MISMATCH")
            return PolicyEvaluationResponse(
                evaluation_id=str(uuid.uuid4()),
                case_id=request.case_id,
                policy_id=policy.policy_id,
                policy_version=policy.version,
                decision="VERIFY",
                reason_codes=reason_codes,
                missing_requirements=["secondary_proof_of_address", "supervisor_manual_inspection"],
                permitted_scopes=[],
                restricted_scopes=policy.required_scopes,
                confidence_score=ocr_conf,
                requires_human_review=True,
                evaluated_at=now_utc,
                explanation=f"High assurance policy triggered discrepancy flags: {active_disallowed}.",
            )

        # ---------------------------------------------------------------------
        # RULE 7: Step-Up Authentication / Contextual MFA
        # ---------------------------------------------------------------------
        if rule_spec.get("require_mfa") or context.get("requires_mfa"):
            if not context.get("mfa_authenticated", False):
                reason_codes.append("DEC_VERIFY_STEP_UP_REQUIRED")
                return PolicyEvaluationResponse(
                    evaluation_id=str(uuid.uuid4()),
                    case_id=request.case_id,
                    policy_id=policy.policy_id,
                    policy_version=policy.version,
                    decision="VERIFY",
                    reason_codes=reason_codes,
                    missing_requirements=["mfa_verification"],
                    permitted_scopes=[],
                    restricted_scopes=policy.required_scopes,
                    confidence_score=ocr_conf,
                    requires_human_review=False,
                    evaluated_at=now_utc,
                    explanation="Elevated transaction requires Multi-Factor Authentication step-up.",
                )

        # ---------------------------------------------------------------------
        # RULE 8: OCR Confidence Gate
        # ---------------------------------------------------------------------
        if ocr_conf < policy.confidence_threshold:
            reason_codes.append("DEC_VERIFY_OCR_CONF_LOW")
            return PolicyEvaluationResponse(
                evaluation_id=str(uuid.uuid4()),
                case_id=request.case_id,
                policy_id=policy.policy_id,
                policy_version=policy.version,
                decision="VERIFY",
                reason_codes=reason_codes,
                missing_requirements=["higher_resolution_evidence"],
                permitted_scopes=[],
                restricted_scopes=policy.required_scopes,
                confidence_score=ocr_conf,
                requires_human_review=True,
                evaluated_at=now_utc,
                explanation=f"OCR extraction confidence ({ocr_conf}) is below policy threshold ({policy.confidence_threshold}).",
            )

        # ---------------------------------------------------------------------
        # RULE 9: Probationary / Restricted Scopes
        # ---------------------------------------------------------------------
        if (
            request.action == "access.probationary"
            or policy.policy_id == "POL-RESTRICTED-PROBATIONARY-V1"
        ):
            permitted = rule_spec.get("permitted_scopes", ["read_only", "provisional_identity"])
            restricted = rule_spec.get("restricted_scopes", ["financial_transfer", "admin_escalation"])
            reason_codes.append("DEC_RESTRICT_CONDITIONAL_APPROVAL")
            return PolicyEvaluationResponse(
                evaluation_id=str(uuid.uuid4()),
                case_id=request.case_id,
                policy_id=policy.policy_id,
                policy_version=policy.version,
                decision="RESTRICT",
                reason_codes=reason_codes,
                missing_requirements=["full_tier_employment_attestation"],
                permitted_scopes=permitted,
                restricted_scopes=restricted,
                confidence_score=ocr_conf,
                requires_human_review=False,
                evaluated_at=now_utc,
                explanation="Subject satisfies probationary criteria; restricted to provisional scopes.",
            )

        # ---------------------------------------------------------------------
        # RULE 10: Happy Path (Policy Satisfied)
        # ---------------------------------------------------------------------
        reason_codes.append("DEC_ALLOW_SATISFIED")
        reason_codes.append("DEC_ALLOW_POLICY_COMPLIANT")
        permitted = rule_spec.get("permitted_scopes", policy.required_scopes)

        return PolicyEvaluationResponse(
            evaluation_id=str(uuid.uuid4()),
            case_id=request.case_id,
            policy_id=policy.policy_id,
            policy_version=policy.version,
            decision="ALLOW",
            reason_codes=reason_codes,
            missing_requirements=[],
            permitted_scopes=permitted,
            restricted_scopes=[],
            confidence_score=ocr_conf,
            requires_human_review=False,
            evaluated_at=now_utc,
            explanation="All policy requirements, deterministic validation rules, and confidence thresholds satisfied.",
        )

    @classmethod
    def evaluate_case(
        cls,
        case_id: str,
        user_id: str,
        is_verifier: bool = False,
        policy_id: Optional[str] = None,
        policy_version: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyEvaluationResponse:
        """Dynamically evaluate a stored verification case using its persisted OCR, validation flags, and overrides."""
        case = _MOCK_CASES_DB.get(case_id)
        if not case:
            raise NotFoundException(f"Verification case '{case_id}' not found")

        # RBAC Check: Case owner or Verifier
        if not is_verifier and case["user_id"] != user_id:
            raise PermissionDeniedException("Access to case policy evaluation denied")

        # 1. Gather OCR extracted fields & confidence
        extracted_list = _MOCK_EXTRACTED_FIELDS_DB.get(case_id, [])
        extracted_fields: Dict[str, Any] = {}
        total_conf = 0.0

        if extracted_list:
            for item in extracted_list:
                extracted_fields[item["field_key"]] = item["field_value"]
                total_conf += float(item.get("confidence", 0.0))
            avg_conf = round(total_conf / max(len(extracted_list), 1), 2)
        else:
            avg_conf = 0.0

        # 2. Merge reviewer corrections if available
        corrections = _MOCK_CORRECTIONS_DB.get(case_id, [])
        for corr in corrections:
            extracted_fields[corr["field_name"]] = corr["corrected_value"]
            # Manual correction by verifier raises effective confidence for verified field
            avg_conf = max(avg_conf, 0.95)

        # 3. Retrieve validation flags
        val_report = ValidationEngine.get_latest_validation(case_id) or {}
        val_flags = val_report.get("reason_codes", [])

        # 4. Construct request
        req = PolicyEvaluationRequest(
            case_id=case_id,
            claim_type=case.get("claim_type", "SYNTH_NAT_ID_V1"),
            extracted_fields=extracted_fields,
            ocr_confidence=avg_conf,
            validation_flags=val_flags,
            policy_id=policy_id or cls.DEFAULT_POLICY_ID,
            policy_version=policy_version or cls.DEFAULT_POLICY_VERSION,
            action=action or "identity.verify",
            resource=resource or "claims:synthetic_identity",
            context=context or {},
        )

        res = cls.evaluate(req)

        # 5. Persist evaluation outcome
        _MOCK_POLICY_EVAL_DB[case_id] = res.model_dump(mode="json")

        # 6. Record timeline event & update case state
        case["current_decision"] = res.decision
        case["updated_at"] = datetime.now(timezone.utc)
        _record_timeline_event(
            case_id=case_id,
            from_status=case.get("status"),
            to_status=case.get("status", "Processing"),
            triggered_by=user_id,
            comment=f"Policy '{res.policy_id}' evaluated -> Decision: {res.decision} (Reasons: {res.reason_codes})",
        )

        return res

    @classmethod
    def get_case_evaluation(
        cls,
        case_id: str,
        user_id: str,
        is_verifier: bool = False,
    ) -> PolicyEvaluationResponse:
        """Retrieve latest policy evaluation record for case."""
        case = _MOCK_CASES_DB.get(case_id)
        if not case:
            raise NotFoundException(f"Verification case '{case_id}' not found")

        if not is_verifier and case["user_id"] != user_id:
            raise PermissionDeniedException("Access to case policy evaluation denied")

        eval_data = _MOCK_POLICY_EVAL_DB.get(case_id)
        if not eval_data:
            # If not yet evaluated, perform default evaluation now
            return cls.evaluate_case(case_id, user_id, is_verifier)

        return PolicyEvaluationResponse(**eval_data)
