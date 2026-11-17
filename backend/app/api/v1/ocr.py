"""OCR Extraction Pipeline API Endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.api.v1.cases import _MOCK_CASES_DB, _record_timeline_event
from app.core.errors import EvidenceNotFoundException, NotFoundException
from app.core.security import AuthenticatedUser, enforce_case_access, get_current_user
from app.schemas.ocr import (
    CaseExtractedFieldsSummaryResponse,
    ExtractedFieldItem,
    OCRExtractionRequest,
    OCRExtractionResponse,
)
from app.services.evidence_service import _MOCK_EVIDENCE_DB
from app.services.ocr_service import OCRService
from app.services.synthetic_docs import (
    SYNTHETIC_TEMPLATES,
    generate_synthetic_document_image,
)

router = APIRouter(tags=["OCR"])


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
    "/cases/{case_id}/evidence/{file_id}/ocr",
    response_model=OCRExtractionResponse,
    status_code=status.HTTP_200_OK,
)
async def run_ocr_extraction(
    case_id: str,
    file_id: str,
    request: Optional[OCRExtractionRequest] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> OCRExtractionResponse:
    """Execute OCR text extraction, field parsing, and provenance tracking on evidence file."""
    case = _verify_case_and_access(case_id, current_user)
    evidence = _MOCK_EVIDENCE_DB.get(file_id)
    if not evidence or evidence["case_id"] != case_id:
        raise EvidenceNotFoundException(file_id)

    claim_type = case.get("claim_type", "SYNTH_NAT_ID_V1")
    auto_rotate = request.auto_rotate if request else True

    # Retrieve raw content from synthetic generator or evidence cache
    image_bytes = evidence.get("raw_bytes")
    if not image_bytes:
        # Check if defect simulated in evidence metadata
        is_low_res = evidence.get("metadata", {}).get("is_low_res", False)
        is_blurry = evidence.get("metadata", {}).get("is_blurry", False)
        rotate_deg = evidence.get("metadata", {}).get("rotate_degrees", 0)

        img_w = 150 if is_low_res else 800
        img_h = 100 if is_low_res else 500
        blur_r = 3.5 if is_blurry else 0.0

        image_bytes, _, _ = generate_synthetic_document_image(
            template_key=claim_type,
            width=img_w,
            height=img_h,
            blur_radius=blur_r,
            rotate_degrees=rotate_deg,
        )

    # Execute OCR Pipeline
    result = OCRService.extract_from_bytes(
        image_bytes=image_bytes,
        case_id=case_id,
        file_id=file_id,
        claim_type=claim_type,
        auto_rotate=auto_rotate,
    )

    # If extraction is inconclusive (confidence < 0.60 or unreadable), handle state per FR-05.4
    if not result["is_conclusive"]:
        if case["status"] in ("Submitted", "Processing", "Draft"):
            case["status"] = "Under Review"
            case["current_decision"] = "VERIFY"
            _record_timeline_event(
                case_id=case_id,
                from_status=case["status"],
                to_status="Under Review",
                triggered_by="OCR_PIPELINE",
                comment=f"OCR extraction inconclusive (confidence {result['overall_confidence']:.2f}). Reason: {', '.join(result['reason_codes'])}. Escalated to Under Review.",
            )
    else:
        _record_timeline_event(
            case_id=case_id,
            from_status=case["status"],
            to_status=case["status"],
            triggered_by="OCR_PIPELINE",
            comment=f"OCR extraction succeeded. {len(result['extracted_fields'])} fields extracted with confidence {result['overall_confidence']:.2f}.",
        )

    return OCRExtractionResponse(**result)


@router.get(
    "/cases/{case_id}/evidence/{file_id}/ocr",
    response_model=List[ExtractedFieldItem],
    status_code=status.HTTP_200_OK,
)
async def get_evidence_ocr_fields(
    case_id: str,
    file_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> List[ExtractedFieldItem]:
    """Retrieve all structured extracted fields and bounding boxes for a specific evidence file."""
    _verify_case_and_access(case_id, current_user)
    items = OCRService.get_extracted_fields_for_file(file_id)
    return [ExtractedFieldItem(**item) for item in items]


@router.get(
    "/cases/{case_id}/ocr/fields",
    response_model=CaseExtractedFieldsSummaryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_case_ocr_fields_summary(
    case_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CaseExtractedFieldsSummaryResponse:
    """Retrieve aggregated extracted fields across all evidence files for a verification case."""
    _verify_case_and_access(case_id, current_user)
    summary = OCRService.get_case_summary(case_id)
    return CaseExtractedFieldsSummaryResponse(**summary)


@router.get(
    "/ocr/synthetic-templates",
    tags=["OCR"],
    status_code=status.HTTP_200_OK,
)
async def list_synthetic_templates(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """List available synthetic document templates for safe testing."""
    return {
        "templates": list(SYNTHETIC_TEMPLATES.keys()),
        "description": "Synthetic, watermarked templates for safe offline testing without real PII",
    }
