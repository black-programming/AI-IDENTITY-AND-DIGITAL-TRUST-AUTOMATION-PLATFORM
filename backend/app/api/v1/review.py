"""Human Reviewer Queue & Actions API."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import AuthenticatedUser, require_role

router = APIRouter()


class ReviewDecisionRequest(BaseModel):
    decision: str
    reason_code: str
    corrections: List[Dict[str, Any]] = []
    comment: str = ""


@router.get("/review/queue", tags=["Review"])
async def get_review_queue(
    current_user: AuthenticatedUser = Depends(require_role(["ROLE_VERIFIER", "ROLE_SYS_ADMIN"])),
):
    """Fetch pending verification cases requiring manual review."""
    return {
        "pending_cases": [
            {
                "case_id": "00000000-0000-0000-0000-000000000002",
                "claim_type": "SYNTH_NAT_ID_V1",
                "status": "Under Review",
                "reason_code": "DEC_VERIFY_OCR_CONF_LOW",
                "priority": "HIGH",
            }
        ],
        "queue_length": 1,
    }


@router.post("/review/cases/{case_id}/decision", tags=["Review"])
async def submit_review_decision(
    case_id: str,
    request: ReviewDecisionRequest,
    current_user: AuthenticatedUser = Depends(require_role(["ROLE_VERIFIER", "ROLE_SYS_ADMIN"])),
):
    """Submit reviewer manual decision with mandatory reason code."""
    return {
        "case_id": case_id,
        "reviewer_id": current_user.user_id,
        "decision": request.decision,
        "reason_code": request.reason_code,
        "status": "Verified" if request.decision == "ALLOW" else "Rejected",
    }
