"""Human Reviewer Queue & Actions API Endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.security import AuthenticatedUser, require_role
from app.schemas.review import (
    FieldCorrectionRequest,
    FieldCorrectionResponse,
    RequestEvidenceRequest,
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    ReviewQueueResponse,
    ReviewWorkbenchResponse,
)
from app.services.review_service import ReviewService

router = APIRouter(tags=["Review"])


@router.get(
    "/review/queue",
    response_model=ReviewQueueResponse,
    status_code=status.HTTP_200_OK,
)
async def get_review_queue(
    assigned_to_me: bool = Query(False, description="Filter queue to cases assigned to caller"),
    current_user: AuthenticatedUser = Depends(require_role(["ROLE_VERIFIER", "ROLE_SYS_ADMIN"])),
) -> ReviewQueueResponse:
    """Fetch pending verification cases requiring manual review, sorted by priority and FIFO."""
    reviewer_filter = current_user.user_id if assigned_to_me else None
    pending = ReviewService.get_review_queue(assigned_to_reviewer_id=reviewer_filter)
    return ReviewQueueResponse(
        pending_cases=pending,
        queue_length=len(pending),
    )


@router.get(
    "/review/cases/{case_id}/workbench",
    response_model=ReviewWorkbenchResponse,
    status_code=status.HTTP_200_OK,
)
async def get_case_workbench(
    case_id: str,
    current_user: AuthenticatedUser = Depends(require_role(["ROLE_VERIFIER", "ROLE_SYS_ADMIN"])),
) -> ReviewWorkbenchResponse:
    """Retrieve full workbench data: case metadata, side-by-side evidence preview, fields with bounding boxes, and validation flags."""
    data = ReviewService.get_workbench_data(case_id=case_id)
    return ReviewWorkbenchResponse(**data)


@router.post(
    "/review/cases/{case_id}/corrections",
    response_model=FieldCorrectionResponse,
    status_code=status.HTTP_200_OK,
)
async def apply_field_corrections(
    case_id: str,
    request: FieldCorrectionRequest,
    current_user: AuthenticatedUser = Depends(require_role(["ROLE_VERIFIER", "ROLE_SYS_ADMIN"])),
) -> FieldCorrectionResponse:
    """Override and correct extracted OCR fields with mandatory justification audit trail."""
    corrections_dicts = [c.model_dump() for c in request.corrections]
    result = ReviewService.apply_corrections(
        case_id=case_id,
        reviewer_id=current_user.user_id,
        corrections=corrections_dicts,
    )
    return FieldCorrectionResponse(**result)


@router.post(
    "/review/cases/{case_id}/request-evidence",
    status_code=status.HTTP_200_OK,
)
async def request_additional_evidence(
    case_id: str,
    request: RequestEvidenceRequest,
    current_user: AuthenticatedUser = Depends(require_role(["ROLE_VERIFIER", "ROLE_SYS_ADMIN"])),
) -> Dict[str, Any]:
    """Flag a case as Action Required with specific guidance prompting the subject for new evidence."""
    return ReviewService.request_additional_evidence(
        case_id=case_id,
        reviewer_id=current_user.user_id,
        reason_code=request.reason_code,
        guidance=request.guidance,
    )


@router.post(
    "/review/cases/{case_id}/decision",
    response_model=ReviewDecisionResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_review_decision(
    case_id: str,
    request: ReviewDecisionRequest,
    current_user: AuthenticatedUser = Depends(require_role(["ROLE_VERIFIER", "ROLE_SYS_ADMIN"])),
) -> ReviewDecisionResponse:
    """Submit reviewer manual decision (ALLOW, VERIFY, RESTRICT, BLOCK) with mandatory reason code."""
    # Apply corrections if included in decision bundle
    if request.corrections:
        corrections_dicts = [c.model_dump() for c in request.corrections]
        ReviewService.apply_corrections(
            case_id=case_id,
            reviewer_id=current_user.user_id,
            corrections=corrections_dicts,
        )

    result = ReviewService.record_decision(
        case_id=case_id,
        reviewer_id=current_user.user_id,
        decision=request.decision,
        reason_code=request.reason_code,
        notes=request.notes,
    )
    return ReviewDecisionResponse(**result)
