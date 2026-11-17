"""Deterministic Document Validation API Endpoints."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, status

from app.api.v1.cases import _MOCK_CASES_DB, _record_timeline_event
from app.core.errors import NotFoundException
from app.core.security import AuthenticatedUser, enforce_case_access, get_current_user
from app.schemas.validation import (
    DocumentValidationRequest,
    DocumentValidationResponse,
)
from app.services.ocr_service import OCRService
from app.services.validation_engine import ValidationEngine

router = APIRouter(tags=["Validation"])


def _verify_case_and_access(case_id: str, user: AuthenticatedUser) -> dict:
    """Helper to verify that case exists and user has authorized access."""
    case = _MOCK_CASES_DB.get(case_id)
    if not case:
        raise NotFoundException(f"Verification case '{case_id}' not found")

    enforce_case_access(
        case_id=case_id,
        case_owner_id=case["user_id"],
        case_org_id=case.get("organization_id"),
        user=user,
    )
    return case


@router.post(
    "/cases/{case_id}/validate",
    response_model=DocumentValidationResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_case_document(
    case_id: str,
    request: Optional[DocumentValidationRequest] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DocumentValidationResponse:
    """Run deterministic validation rules (completeness, format regex, expiry, MRZ, cross-consistency) on case evidence."""
    case = _verify_case_and_access(case_id, current_user)

    claim_type = (request.claim_type if request and request.claim_type else case.get("claim_type", "SYNTH_NAT_ID_V1"))
    extracted_fields = request.extracted_fields if request and request.extracted_fields else None
    user_profile = request.user_profile if request and request.user_profile else None
    file_id = request.file_id if request else None

    # If extracted fields not explicitly provided in request body, retrieve from OCR extraction store
    if not extracted_fields:
        if file_id:
            file_extractions = OCRService.get_extracted_fields_for_file(file_id)
            extracted_fields = {f["field_key"]: f["field_value"] for f in file_extractions}
        else:
            summary = OCRService.get_case_summary(case_id)
            extracted_fields = summary.get("extracted_fields", {})

    # Execute Deterministic Validation Engine
    result = ValidationEngine.validate(
        case_id=case_id,
        claim_type=claim_type,
        extracted_fields=extracted_fields,
        user_profile=user_profile,
        file_id=file_id,
    )

    # Update case decision indicators based on deterministic outcome
    if result.overall_outcome == "FAIL":
        if "DEC_BLOCK_DOC_EXPIRED" in result.reason_codes:
            case["current_decision"] = "BLOCK"
        elif "DEC_BLOCK_REQUIRED_FIELD_MISSING" in result.reason_codes:
            case["current_decision"] = "BLOCK"
        else:
            case["current_decision"] = "BLOCK"
    elif result.overall_outcome == "FLAGGED":
        case["current_decision"] = "VERIFY"
        if case["status"] in ("Draft", "Submitted", "Processing"):
            case["status"] = "Under Review"

    # Record Timeline Event
    _record_timeline_event(
        case_id=case_id,
        from_status=case["status"],
        to_status=case["status"],
        triggered_by="VALIDATION_ENGINE",
        comment=f"Deterministic validation outcome: {result.overall_outcome}. Flags: {result.flags}. Reasons: {result.reason_codes}",
    )

    return result


@router.get(
    "/cases/{case_id}/validation",
    response_model=DocumentValidationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_latest_case_validation(
    case_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DocumentValidationResponse:
    """Retrieve the latest deterministic validation report for a case."""
    case = _verify_case_and_access(case_id, current_user)

    existing = ValidationEngine.get_latest_validation(case_id)
    if existing:
        return DocumentValidationResponse(**existing)

    # If no prior validation executed, execute on-the-fly
    claim_type = case.get("claim_type", "SYNTH_NAT_ID_V1")
    summary = OCRService.get_case_summary(case_id)
    fields = summary.get("extracted_fields", {})

    result = ValidationEngine.validate(
        case_id=case_id,
        claim_type=claim_type,
        extracted_fields=fields,
    )
    return result
