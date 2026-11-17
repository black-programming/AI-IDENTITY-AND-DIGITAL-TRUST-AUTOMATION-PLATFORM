"""Aadhaar Card Processing API Endpoints.

Provides:
- 12-digit Verhoeff Checksum & Structure Validation
- YOLOv8 Entity Detection (bounding boxes for name, dob, address, aadhar_number)
- Direct image and case evidence extraction
- Privacy masking per UIDAI and GDPR standards
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from fastapi.responses import JSONResponse

from app.api.v1.cases import _MOCK_CASES_DB
from app.core.errors import EvidenceNotFoundException, NotFoundException, ValidationException
from app.core.security import AuthenticatedUser, enforce_case_access, get_current_user
from app.schemas.aadhaar import (
    AadhaarDetectionResponse,
    AadhaarValidateRequest,
    AadhaarValidateResponse,
)
from app.services.aadhaar_service import (
    AadhaarEntityDetectionService,
    validate_aadhaar_number,
)
from app.services.evidence_service import _MOCK_EVIDENCE_DB
from app.services.synthetic_docs import generate_synthetic_document_image

router = APIRouter(prefix="/aadhaar", tags=["Aadhaar Processing"])


@router.post(
    "/validate-number",
    response_model=AadhaarValidateResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_aadhaar(
    payload: AadhaarValidateRequest,
) -> AadhaarValidateResponse:
    """Validate an Aadhaar number using the cryptographic Verhoeff algorithm.
    
    Verifies length, non-zero/non-one initial digit, and dihedral D5 checksum.
    Returns UIDAI-compliant privacy masked representation (e.g. 'XXXX XXXX 4152').
    """
    res = validate_aadhaar_number(payload.aadhar_number)
    return AadhaarValidateResponse(
        is_valid=res["is_valid"],
        error_code=res.get("error_code"),
        message=res["message"],
        cleaned_number=res.get("cleaned_number", ""),
        masked_number=res.get("masked_number", ""),
        sha256_hash=res.get("sha256_hash", ""),
    )


@router.post(
    "/detect-and-extract",
    response_model=AadhaarDetectionResponse,
    status_code=status.HTTP_200_OK,
)
async def detect_and_extract_aadhaar(
    file: Optional[UploadFile] = File(None),
    case_id: Optional[str] = Form(None),
) -> AadhaarDetectionResponse:
    """Detect Aadhaar card entities (name, dob, address, aadhar_number), crop, OCR, and validate.
    
    If no file is uploaded, a synthetic test Aadhaar document is processed automatically.
    """
    if file:
        image_bytes = await file.read()
    else:
        # Default to synthetic watermarked Aadhaar sample
        image_bytes, _, _ = generate_synthetic_document_image("SYNTH_AADHAAR_V1")

    res = AadhaarEntityDetectionService.detect_and_extract(
        image_bytes=image_bytes,
        case_id=case_id,
        file_id="upload_direct",
    )

    return AadhaarDetectionResponse(
        status=res["status"],
        case_id=res.get("case_id"),
        file_id=res.get("file_id"),
        detected_entities=res.get("detected_entities", {}),
        extracted_fields=res.get("extracted_fields", {}),
        bounding_boxes=res.get("bounding_boxes", []),
        verhoeff_valid=res.get("verhoeff_valid", False),
        masked_number=res.get("masked_number", ""),
        detection_method=res.get("detection_method", "HEURISTIC_SYNTHETIC_DETECTOR"),
        extracted_at=res["extracted_at"],
    )


@router.post(
    "/cases/{case_id}/evidence/{file_id}/extract",
    response_model=AadhaarDetectionResponse,
    status_code=status.HTTP_200_OK,
)
async def extract_aadhaar_from_case_evidence(
    case_id: str,
    file_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AadhaarDetectionResponse:
    """Run Aadhaar entity detection and Verhoeff validation on an existing case evidence file."""
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

    # Use synthetic Aadhaar bytes for mock pipeline or loaded bytes
    image_bytes, _, _ = generate_synthetic_document_image("SYNTH_AADHAAR_V1")

    res = AadhaarEntityDetectionService.detect_and_extract(
        image_bytes=image_bytes,
        case_id=case_id,
        file_id=file_id,
    )

    return AadhaarDetectionResponse(
        status=res["status"],
        case_id=case_id,
        file_id=file_id,
        detected_entities=res.get("detected_entities", {}),
        extracted_fields=res.get("extracted_fields", {}),
        bounding_boxes=res.get("bounding_boxes", []),
        verhoeff_valid=res.get("verhoeff_valid", False),
        masked_number=res.get("masked_number", ""),
        detection_method=res.get("detection_method", "HEURISTIC_SYNTHETIC_DETECTOR"),
        extracted_at=res["extracted_at"],
    )


@router.get(
    "/sample-image",
    status_code=status.HTTP_200_OK,
)
async def get_sample_aadhaar_image():
    """Return synthetic watermarked Aadhaar card PNG for testing and UI demonstration."""
    image_bytes, _, _ = generate_synthetic_document_image("SYNTH_AADHAAR_V1")
    return Response(content=image_bytes, media_type="image/png")
