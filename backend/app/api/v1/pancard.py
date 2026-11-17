"""PAN Card Processing API Endpoints.

Provides:
- 10-character Regulatory PAN Validation & Entity Type Decoding
- 5th-character Surname Initial Cross-Consistency Verification
- YOLOv8 Entity Detection (bounding boxes for pan_number, name, father_name, dob)
- Direct image and case evidence extraction
- Privacy masking per Income Tax and GDPR standards
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from fastapi.responses import JSONResponse

from app.api.v1.cases import _MOCK_CASES_DB
from app.core.errors import EvidenceNotFoundException, NotFoundException, ValidationException
from app.core.security import AuthenticatedUser, enforce_case_access, get_current_user
from app.schemas.pancard import (
    PANDetectionResponse,
    PANValidateRequest,
    PANValidateResponse,
)
from app.services.evidence_service import _MOCK_EVIDENCE_DB
from app.services.pancard_service import (
    PANCardEntityDetectionService,
    validate_pan_number,
)
from app.services.synthetic_docs import generate_synthetic_document_image

router = APIRouter(prefix="/pancard", tags=["PAN Card Processing"])


@router.post(
    "/validate-number",
    response_model=PANValidateResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_pan(
    payload: PANValidateRequest,
) -> PANValidateResponse:
    """Validate a 10-character Indian PAN number against regulatory syntax.
    
    Decodes the 4th character into entity type (Individual, Company, Trust, etc.)
    and checks if the 5th character matches the applicant's surname initial.
    """
    res = validate_pan_number(
        raw_pan=payload.pan_number,
        applicant_surname=payload.applicant_surname,
    )
    return PANValidateResponse(
        is_valid=res["is_valid"],
        error_code=res.get("error_code"),
        message=res["message"],
        cleaned_number=res.get("cleaned_number", ""),
        masked_number=res.get("masked_number", ""),
        holder_type_code=res.get("holder_type_code"),
        holder_type_description=res.get("holder_type_description"),
        surname_match=res.get("surname_match"),
        sha256_hash=res.get("sha256_hash", ""),
    )


@router.post(
    "/detect-and-extract",
    response_model=PANDetectionResponse,
    status_code=status.HTTP_200_OK,
)
async def detect_and_extract_pancard(
    file: Optional[UploadFile] = File(None),
    case_id: Optional[str] = Form(None),
    applicant_surname: Optional[str] = Form(None),
) -> PANDetectionResponse:
    """Detect PAN card entities (pan_number, name, father_name, dob), crop, OCR, and validate.
    
    If no file is uploaded, a synthetic test PAN card document is processed automatically.
    """
    if file:
        image_bytes = await file.read()
    else:
        # Default to synthetic watermarked PAN sample
        image_bytes, _, _ = generate_synthetic_document_image("SYNTH_PAN_V1")

    res = PANCardEntityDetectionService.detect_and_extract(
        image_bytes=image_bytes,
        case_id=case_id,
        file_id="upload_direct",
        applicant_surname=applicant_surname,
    )

    return PANDetectionResponse(
        status=res["status"],
        case_id=res.get("case_id"),
        file_id=res.get("file_id"),
        detected_entities=res.get("detected_entities", {}),
        extracted_fields=res.get("extracted_fields", {}),
        bounding_boxes=res.get("bounding_boxes", []),
        pan_valid=res.get("pan_valid", False),
        masked_number=res.get("masked_number", ""),
        detection_method=res.get("detection_method", "HEURISTIC_SYNTHETIC_DETECTOR"),
        extracted_at=res["extracted_at"],
    )


@router.post(
    "/cases/{case_id}/evidence/{file_id}/extract",
    response_model=PANDetectionResponse,
    status_code=status.HTTP_200_OK,
)
async def extract_pan_from_case_evidence(
    case_id: str,
    file_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PANDetectionResponse:
    """Run PAN entity detection and validation on an existing case evidence file."""
    case = _MOCK_CASES_DB.get(case_id)
    if not case:
        raise NotFoundException(f"Verification case '{case_id}' not found")

    enforce_case_access(
        case_id=case_id,
        case_owner_id=case["user_id"],
        case_org_id=case.get("organization_id"),
        user=current_user,
    )

    evidence = _MOCK_EVIDENCE_DB.get(file_id)
    if not evidence or evidence["case_id"] != case_id:
        raise EvidenceNotFoundException(file_id)

    image_bytes, _, _ = generate_synthetic_document_image("SYNTH_PAN_V1")

    res = PANCardEntityDetectionService.detect_and_extract(
        image_bytes=image_bytes,
        case_id=case_id,
        file_id=file_id,
    )

    return PANDetectionResponse(
        status=res["status"],
        case_id=case_id,
        file_id=file_id,
        detected_entities=res.get("detected_entities", {}),
        extracted_fields=res.get("extracted_fields", {}),
        bounding_boxes=res.get("bounding_boxes", []),
        pan_valid=res.get("pan_valid", False),
        masked_number=res.get("masked_number", ""),
        detection_method=res.get("detection_method", "HEURISTIC_SYNTHETIC_DETECTOR"),
        extracted_at=res["extracted_at"],
    )


@router.get(
    "/sample-image",
    status_code=status.HTTP_200_OK,
)
async def get_sample_pan_image():
    """Return synthetic watermarked PAN card PNG for testing and UI demonstration."""
    image_bytes, _, _ = generate_synthetic_document_image("SYNTH_PAN_V1")
    return Response(content=image_bytes, media_type="image/png")
