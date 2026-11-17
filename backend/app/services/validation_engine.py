"""Deterministic Document Validation Engine — Field Completeness, Temporal Checks, MRZ, and Cross-Consistency."""

from datetime import date, datetime, timezone
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.schemas.validation import DocumentValidationResponse, ValidationRuleResult

# Regex patterns for supported document types
DOCUMENT_FORMAT_REGEXES = {
    "SYNTH_NAT_ID_V1": r"^NAT-\d{8}$",
    "SYNTH_DL_V1": r"^DL-[A-Z]{2}-\d{4}-\d{6}$",
    "SYNTH_PASSPORT_V1": r"^[A-Z]\d{7,8}$",
    "SYNTH_AADHAAR_V1": r"^(\d{4}\s\d{4}\s\d{4}|\d{12})$",
    "AADHAAR_CARD": r"^(\d{4}\s\d{4}\s\d{4}|\d{12})$",
    "aadhaar": r"^(\d{4}\s\d{4}\s\d{4}|\d{12})$",
    "SYNTH_PAN_V1": r"^[A-Z]{3}[PCHABTLJGF][A-Z]\d{4}[A-Z]$",
    "PAN_CARD": r"^[A-Z]{3}[PCHABTLJGF][A-Z]\d{4}[A-Z]$",
    "pan": r"^[A-Z]{3}[PCHABTLJGF][A-Z]\d{4}[A-Z]$",
    "pancard": r"^[A-Z]{3}[PCHABTLJGF][A-Z]\d{4}[A-Z]$",
}

# Mandatory fields required per document claim type
MANDATORY_FIELDS = {
    "SYNTH_NAT_ID_V1": ["document_number", "full_name", "date_of_birth", "expiry_date"],
    "SYNTH_DL_V1": ["document_number", "full_name", "date_of_birth", "vehicle_classes", "expiry_date"],
    "SYNTH_PASSPORT_V1": ["document_number", "full_name", "date_of_birth", "expiry_date", "mrz_line1", "mrz_line2"],
    "SYNTH_AADHAAR_V1": ["document_number", "full_name", "date_of_birth"],
    "AADHAAR_CARD": ["document_number", "full_name", "date_of_birth"],
    "aadhaar": ["document_number", "full_name", "date_of_birth"],
    "SYNTH_PAN_V1": ["document_number", "full_name", "date_of_birth"],
    "PAN_CARD": ["document_number", "full_name", "date_of_birth"],
    "pan": ["document_number", "full_name", "date_of_birth"],
    "pancard": ["document_number", "full_name", "date_of_birth"],
}

# In-memory store of validation outcomes
_MOCK_VALIDATIONS_DB: Dict[str, Dict[str, Any]] = {}


def calculate_icao9303_check_digit(data_str: str) -> int:
    """Compute ICAO 9303 7-3-1 weight check digit over standard MRZ alphanumeric string."""
    weights = [7, 3, 1]
    total = 0
    for i, ch in enumerate(data_str):
        if ch.isdigit():
            val = int(ch)
        elif ch.isalpha():
            val = ord(ch.upper()) - ord("A") + 10
        elif ch == "<":
            val = 0
        else:
            val = 0
        total += val * weights[i % 3]
    return total % 10


def parse_date_safe(date_str: Optional[str]) -> Optional[date]:
    """Safely parse ISO 8601 YYYY-MM-DD date."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except Exception:
        return None


class ValidationEngine:
    @classmethod
    def validate(
        cls,
        case_id: str,
        claim_type: str,
        extracted_fields: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None,
        file_id: Optional[str] = None,
    ) -> DocumentValidationResponse:
        """Run all deterministic validation rules against extracted evidence fields."""
        now_utc = datetime.now(timezone.utc)
        today = now_utc.date()

        rule_results: List[ValidationRuleResult] = []
        all_flags: List[str] = []
        all_reasons: List[str] = []

        # ---------------------------------------------------------------------
        # 1. Rule: Required Field Completeness (VAL-REQUIRED-FIELDS)
        # ---------------------------------------------------------------------
        required = MANDATORY_FIELDS.get(claim_type, ["document_number", "full_name"])
        missing = [f for f in required if not extracted_fields.get(f)]

        if missing:
            rule_results.append(
                ValidationRuleResult(
                    rule_id="VAL-REQUIRED-FIELDS",
                    rule_name="Required Field Completeness",
                    passed=False,
                    details=f"Missing required fields: {missing}",
                    reason_codes=["ERR_MISSING_REQUIRED_FIELDS", "DEC_BLOCK_REQUIRED_FIELD_MISSING"],
                )
            )
            all_flags.append("FLAG_INCOMPLETE_FIELDS")
            all_reasons.extend(["ERR_MISSING_REQUIRED_FIELDS", "DEC_BLOCK_REQUIRED_FIELD_MISSING"])
        else:
            rule_results.append(
                ValidationRuleResult(
                    rule_id="VAL-REQUIRED-FIELDS",
                    rule_name="Required Field Completeness",
                    passed=True,
                    details=f"All {len(required)} mandatory fields present",
                    reason_codes=[],
                )
            )

        # ---------------------------------------------------------------------
        # 2. Rule: Format & Regular Expression Validation (VAL-FORMAT-REGEX)
        # ---------------------------------------------------------------------
        doc_num = str(extracted_fields.get("document_number", "")).strip()
        expected_regex = DOCUMENT_FORMAT_REGEXES.get(claim_type)
        format_passed = True
        format_details = "Document format valid"

        if expected_regex and doc_num:
            if not re.match(expected_regex, doc_num):
                format_passed = False
                format_details = f"Document number '{doc_num}' does not match standard pattern '{expected_regex}'"

        if not format_passed:
            rule_results.append(
                ValidationRuleResult(
                    rule_id="VAL-FORMAT-REGEX",
                    rule_name="Document Identifier Format Check",
                    passed=False,
                    details=format_details,
                    reason_codes=["ERR_INVALID_FIELD_FORMAT", "VAL_FORMAT_MISMATCH"],
                )
            )
            all_flags.append("FLAG_INVALID_FORMAT")
            all_reasons.extend(["ERR_INVALID_FIELD_FORMAT", "VAL_FORMAT_MISMATCH"])
        else:
            rule_results.append(
                ValidationRuleResult(
                    rule_id="VAL-FORMAT-REGEX",
                    rule_name="Document Identifier Format Check",
                    passed=True,
                    details=format_details,
                    reason_codes=[],
                )
            )

        # ---------------------------------------------------------------------
        # 3. Rule: Temporal Validity & Expiry Checks (VAL-TEMPORAL-EXPIRY)
        # ---------------------------------------------------------------------
        temporal_passed = True
        temporal_reasons: List[str] = []
        temporal_details = "Document dates temporally valid"

        expiry_date = parse_date_safe(extracted_fields.get("expiry_date"))
        issue_date = parse_date_safe(extracted_fields.get("issue_date"))
        dob = parse_date_safe(extracted_fields.get("date_of_birth"))

        if expiry_date and expiry_date < today:
            temporal_passed = False
            temporal_reasons.extend(["DEC_BLOCK_DOC_EXPIRED", "ERR_DOCUMENT_EXPIRED"])
            temporal_details = f"Document expired on {expiry_date} (current UTC date is {today})"
            all_flags.append("FLAG_EXPIRED_DOCUMENT")

        if issue_date and issue_date > today:
            temporal_passed = False
            temporal_reasons.extend(["ERR_FUTURE_ISSUE_DATE", "ERR_CHRONOLOGICAL_INCONSISTENCY"])
            temporal_details = f"Document issue date {issue_date} is in the future"
            all_flags.append("FLAG_CHRONOLOGICAL_ANOMALY")

        if issue_date and expiry_date and issue_date >= expiry_date:
            temporal_passed = False
            if "ERR_CHRONOLOGICAL_INCONSISTENCY" not in temporal_reasons:
                temporal_reasons.append("ERR_CHRONOLOGICAL_INCONSISTENCY")
            temporal_details = f"Issue date ({issue_date}) cannot be on or after expiry date ({expiry_date})"
            all_flags.append("FLAG_CHRONOLOGICAL_ANOMALY")

        if dob:
            age_years = (today - dob).days / 365.25
            if age_years < 18:
                all_flags.append("FLAG_UNDERAGE_SUBJECT")
                temporal_reasons.append("ERR_UNDERAGE_SUBJECT")
                temporal_passed = False
                temporal_details = f"Subject age ({age_years:.1f} years) is under minimum legal threshold (18)"

        rule_results.append(
            ValidationRuleResult(
                rule_id="VAL-TEMPORAL-EXPIRY",
                rule_name="Temporal Validity and Expiration Verification",
                passed=temporal_passed,
                details=temporal_details,
                reason_codes=temporal_reasons,
            )
        )
        all_reasons.extend(temporal_reasons)

        # ---------------------------------------------------------------------
        # 4. Rule: ICAO 9303 MRZ Checksums (VAL-MRZ-CHECKSUM)
        # ---------------------------------------------------------------------
        mrz_line1 = extracted_fields.get("mrz_line1")
        mrz_line2 = extracted_fields.get("mrz_line2")

        if mrz_line2 and len(mrz_line2) >= 28:
            mrz_passed = True
            mrz_details = "ICAO 9303 MRZ checksums verified"
            mrz_reasons: List[str] = []

            # Check digit 1: Document number (first 9 chars vs char 9)
            doc_str = mrz_line2[0:9]
            expected_doc_check = int(mrz_line2[9]) if mrz_line2[9].isdigit() else -1
            actual_doc_check = calculate_icao9303_check_digit(doc_str)
            if expected_doc_check != actual_doc_check:
                mrz_passed = False
                mrz_reasons.append("ERR_MRZ_CHECKSUM_FAILED")
                mrz_details = f"MRZ document check digit mismatch: expected {expected_doc_check}, computed {actual_doc_check}"

            # Check digit 2: DOB (chars 13..18 vs char 19)
            dob_str = mrz_line2[13:19]
            expected_dob_check = int(mrz_line2[19]) if mrz_line2[19].isdigit() else -1
            actual_dob_check = calculate_icao9303_check_digit(dob_str)
            if expected_dob_check != actual_dob_check:
                mrz_passed = False
                mrz_reasons.append("ERR_MRZ_CHECKSUM_FAILED")
                mrz_details = f"MRZ DOB check digit mismatch: expected {expected_dob_check}, computed {actual_dob_check}"

            # Check digit 3: Expiry (chars 21..26 vs char 27)
            exp_str = mrz_line2[21:27]
            expected_exp_check = int(mrz_line2[27]) if mrz_line2[27].isdigit() else -1
            actual_exp_check = calculate_icao9303_check_digit(exp_str)
            if expected_exp_check != actual_exp_check:
                mrz_passed = False
                mrz_reasons.append("ERR_MRZ_CHECKSUM_FAILED")
                mrz_details = f"MRZ expiry check digit mismatch: expected {expected_exp_check}, computed {actual_exp_check}"

            if not mrz_passed:
                all_flags.append("FLAG_MRZ_CHECKSUM_FAILED")
                all_reasons.extend(mrz_reasons)

            rule_results.append(
                ValidationRuleResult(
                    rule_id="VAL-MRZ-CHECKSUM",
                    rule_name="ICAO 9303 MRZ Algorithmic Checksum Validation",
                    passed=mrz_passed,
                    details=mrz_details,
                    reason_codes=mrz_reasons,
                )
            )

        # ---------------------------------------------------------------------
        # 4b. Rule: Aadhaar 12-Digit Verhoeff Checksum (VAL-AADHAAR-VERHOEFF)
        # ---------------------------------------------------------------------
        is_aadhaar_claim = (
            claim_type in ("SYNTH_AADHAAR_V1", "AADHAAR_CARD", "aadhaar", "AADHAAR")
            or "aadhaar" in str(claim_type).lower()
        )
        if is_aadhaar_claim and doc_num:
            from app.services.aadhaar_service import validate_aadhaar_number
            aadhaar_val = validate_aadhaar_number(doc_num)
            aadhaar_passed = aadhaar_val["is_valid"]
            aadhaar_reasons: List[str] = []

            if not aadhaar_passed:
                err_code = aadhaar_val.get("error_code") or "ERR_AADHAAR_CHECKSUM_FAILED"
                aadhaar_reasons.append(err_code)
                all_flags.append("FLAG_INVALID_AADHAAR_CHECKSUM")
                all_reasons.append(err_code)
                aadhaar_details = aadhaar_val.get("message", "Aadhaar number validation failed")
            else:
                aadhaar_details = f"Aadhaar number Verhoeff checksum valid ({aadhaar_val['masked_number']})"

            rule_results.append(
                ValidationRuleResult(
                    rule_id="VAL-AADHAAR-VERHOEFF",
                    rule_name="Aadhaar 12-Digit Verhoeff Checksum & Structure Validation",
                    passed=aadhaar_passed,
                    details=aadhaar_details,
                    reason_codes=aadhaar_reasons,
                )
            )

        # ---------------------------------------------------------------------
        # 4c. Rule: PAN Card Structure & Surname Verification (VAL-PAN-FORMAT)
        # ---------------------------------------------------------------------
        is_pan_claim = (
            claim_type in ("SYNTH_PAN_V1", "PAN_CARD", "pan", "pancard", "PAN")
            or "pan" in str(claim_type).lower()
        )
        if is_pan_claim and doc_num:
            from app.services.pancard_service import validate_pan_number
            applicant_surname = None
            if user_profile and user_profile.get("full_name"):
                name_parts = user_profile.get("full_name", "").strip().split()
                if len(name_parts) > 1:
                    applicant_surname = name_parts[-1]
                elif name_parts:
                    applicant_surname = name_parts[0]

            pan_val = validate_pan_number(doc_num, applicant_surname=applicant_surname)
            pan_passed = pan_val["is_valid"]
            pan_reasons: List[str] = []

            if not pan_passed:
                err_code = pan_val.get("error_code") or "ERR_PAN_FORMAT_MISMATCH"
                pan_reasons.append(err_code)
                all_flags.append("FLAG_INVALID_PAN_STRUCTURE")
                all_reasons.append(err_code)
                pan_details = pan_val.get("message", "PAN format validation failed")
            else:
                pan_details = f"PAN format valid ({pan_val['holder_type_description']}, {pan_val['masked_number']})"
                if pan_val.get("surname_match") is False:
                    pan_reasons.append("WARN_PAN_SURNAME_INITIAL_MISMATCH")
                    all_flags.append("FLAG_PAN_SURNAME_INITIAL_MISMATCH")
                    pan_details += f" | Warning: 5th character '{pan_val['cleaned_number'][4]}' does not match applicant surname initial"

            rule_results.append(
                ValidationRuleResult(
                    rule_id="VAL-PAN-FORMAT",
                    rule_name="PAN Card Structure, Entity Type & Surname Verification",
                    passed=pan_passed,
                    details=pan_details,
                    reason_codes=pan_reasons,
                )
            )

        # ---------------------------------------------------------------------
        # 5. Rule: Cross-Field & Profile Consistency (VAL-CROSS-CONSISTENCY)
        # ---------------------------------------------------------------------
        cross_passed = True
        cross_reasons: List[str] = []
        cross_details = "Cross-field consistency verified"

        # Check internal VIZ vs MRZ consistency
        if mrz_line2 and doc_num:
            mrz_clean_doc = mrz_line2[0:9].replace("<", "")
            if mrz_clean_doc and mrz_clean_doc != doc_num:
                cross_passed = False
                cross_reasons.append("ERR_VIZ_MRZ_MISMATCH")
                cross_details = f"VIZ document number '{doc_num}' does not match MRZ document number '{mrz_clean_doc}'"
                all_flags.append("FLAG_VIZ_MRZ_CONFLICT")

        # Check extracted fields against user profile assertions
        if user_profile:
            profile_name = user_profile.get("full_name", "").strip().lower()
            doc_name = str(extracted_fields.get("full_name", "")).strip().lower()

            if profile_name and doc_name:
                p_tokens = set(profile_name.split())
                d_tokens = set(doc_name.split())
                # If zero overlapping tokens
                if not (p_tokens & d_tokens):
                    cross_passed = False
                    cross_reasons.extend(["ERR_CROSS_FIELD_CONFLICT", "DEC_VERIFY_CROSS_FIELD_MISMATCH"])
                    cross_details = f"Profile name '{profile_name}' shows no token match with document name '{doc_name}'"
                    all_flags.append("FLAG_PROFILE_NAME_MISMATCH")

            profile_dob = user_profile.get("date_of_birth")
            doc_dob = extracted_fields.get("date_of_birth")
            if profile_dob and doc_dob and profile_dob != doc_dob:
                cross_passed = False
                if "ERR_CROSS_FIELD_CONFLICT" not in cross_reasons:
                    cross_reasons.append("ERR_CROSS_FIELD_CONFLICT")
                cross_details = f"Profile DOB '{profile_dob}' does not match document DOB '{doc_dob}'"
                all_flags.append("FLAG_PROFILE_DOB_MISMATCH")

        if not cross_passed:
            all_reasons.extend(cross_reasons)

        rule_results.append(
            ValidationRuleResult(
                rule_id="VAL-CROSS-CONSISTENCY",
                rule_name="Cross-Field & Profile Identity Consistency Check",
                passed=cross_passed,
                details=cross_details,
                reason_codes=cross_reasons,
            )
        )

        # ---------------------------------------------------------------------
        # 6. Overall Outcome Synthesis
        # ---------------------------------------------------------------------
        critical_failed = any(
            not r.passed for r in rule_results
            if r.rule_id in ("VAL-REQUIRED-FIELDS", "VAL-TEMPORAL-EXPIRY", "VAL-MRZ-CHECKSUM", "VAL-AADHAAR-VERHOEFF", "VAL-PAN-FORMAT")
        )
        any_failed = any(not r.passed for r in rule_results)

        if critical_failed:
            overall_outcome = "FAIL"
            validation_passed = False
        elif any_failed:
            overall_outcome = "FLAGGED"
            validation_passed = False
        else:
            overall_outcome = "PASS"
            validation_passed = True
            all_reasons.append("VAL_PASSED_ALL_CHECKS")

        # Deduplicate reason codes & flags while preserving order
        unique_reasons = list(dict.fromkeys(all_reasons))
        unique_flags = list(dict.fromkeys(all_flags))

        validation_id = str(uuid.uuid4())
        response = DocumentValidationResponse(
            validation_id=validation_id,
            case_id=case_id,
            file_id=file_id,
            validation_passed=validation_passed,
            overall_outcome=overall_outcome,
            flags=unique_flags,
            reason_codes=unique_reasons,
            rule_results=rule_results,
            validated_at=now_utc,
        )

        _MOCK_VALIDATIONS_DB[case_id] = response.model_dump()
        return response

    @classmethod
    def get_latest_validation(cls, case_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the latest validation record for a case."""
        return _MOCK_VALIDATIONS_DB.get(case_id)
