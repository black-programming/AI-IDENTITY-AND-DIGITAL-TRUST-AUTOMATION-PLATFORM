"""Deterministic Trust & Policy Engine.

Evaluates claims, deterministic validation rules, and OCR confidence to produce
contextual decisions: ALLOW, VERIFY, RESTRICT, BLOCK with standardized reason codes.
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Tuple

from app.schemas.policy import PolicyEvaluationRequest, PolicyEvaluationResponse


class PolicyEngine:
    POLICY_VERSION = "v1.0.0"
    CONFIDENCE_THRESHOLD = 0.85

    @classmethod
    def evaluate(cls, request: PolicyEvaluationRequest) -> PolicyEvaluationResponse:
        """Execute deterministic policy rules against extracted evidence."""
        reason_codes: List[str] = []
        now_utc = datetime.now(timezone.utc)
        today_date = now_utc.date()

        fields = request.extracted_fields
        claim_type = request.claim_type
        ocr_conf = request.ocr_confidence

        # Rule 1: Fail-Closed Check on Empty Fields
        if not fields:
            return PolicyEvaluationResponse(
                case_id=request.case_id,
                decision="BLOCK",
                reason_codes=["DEC_BLOCK_UNSUPPORTED_MIME"],
                confidence_score=0.0,
                policy_version=cls.POLICY_VERSION,
                evaluated_at=now_utc,
                requires_human_review=False,
            )

        # Rule 2: Expiration Date Check (Deterministic Rule VAL-EXPIRY)
        expiry_str = fields.get("expiry_date")
        if expiry_str:
            try:
                expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                if expiry < today_date:
                    reason_codes.append("DEC_BLOCK_DOC_EXPIRED")
                    return PolicyEvaluationResponse(
                        case_id=request.case_id,
                        decision="BLOCK",
                        reason_codes=reason_codes,
                        confidence_score=ocr_conf,
                        policy_version=cls.POLICY_VERSION,
                        evaluated_at=now_utc,
                        requires_human_review=False,
                    )
            except ValueError:
                reason_codes.append("DEC_VERIFY_OCR_CONF_LOW")

        # Rule 3: Blacklisted Document Check
        doc_num = fields.get("document_number") or fields.get("license_number") or fields.get("passport_number")
        if doc_num and doc_num in ["REVOKED999", "FRAUD1234"]:
            reason_codes.append("DEC_BLOCK_BLACKLISTED_IDENTIFIER")
            return PolicyEvaluationResponse(
                case_id=request.case_id,
                decision="BLOCK",
                reason_codes=reason_codes,
                confidence_score=1.0,
                policy_version=cls.POLICY_VERSION,
                evaluated_at=now_utc,
                requires_human_review=False,
            )

        # Rule 4: OCR Confidence Gate
        if ocr_conf < cls.CONFIDENCE_THRESHOLD:
            reason_codes.append("DEC_VERIFY_OCR_CONF_LOW")
            return PolicyEvaluationResponse(
                case_id=request.case_id,
                decision="VERIFY",
                reason_codes=reason_codes,
                confidence_score=ocr_conf,
                policy_version=cls.POLICY_VERSION,
                evaluated_at=now_utc,
                requires_human_review=True,
            )

        # Rule 5: Happy Path (Policy Satisfied)
        reason_codes.append("DEC_ALLOW_SATISFIED")
        return PolicyEvaluationResponse(
            case_id=request.case_id,
            decision="ALLOW",
            reason_codes=reason_codes,
            confidence_score=ocr_conf,
            policy_version=cls.POLICY_VERSION,
            evaluated_at=now_utc,
            requires_human_review=False,
        )
