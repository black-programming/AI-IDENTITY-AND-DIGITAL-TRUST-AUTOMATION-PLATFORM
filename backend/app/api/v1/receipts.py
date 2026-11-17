"""Evidence Receipts API — Generation, Retrieval, and Public Cryptographic Verification."""

from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.v1.cases import _MOCK_CASES_DB
from app.core.errors import NotFoundException
from app.core.security import AuthenticatedUser, enforce_case_access, get_current_user
from app.schemas.receipts import (
    EvidenceReceiptResponse,
    ReceiptVerifyRequest,
    ReceiptVerifyResponse,
)
from app.services.audit_service import AuditService

router = APIRouter(tags=["Evidence Receipts"])


@router.get("/receipts/{case_id}", response_model=EvidenceReceiptResponse)
async def get_receipt(
    case_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvidenceReceiptResponse:
    """Retrieve cryptographic evidence receipt for a verification case."""
    case = _MOCK_CASES_DB.get(case_id)
    if case:
        # Enforce cross-user and cross-org access boundaries
        enforce_case_access(
            case_id=case_id,
            case_owner_id=case["user_id"],
            case_org_id=case.get("organization_id"),
            user=current_user,
        )
    else:
        raise NotFoundException(f"Case '{case_id}' not found")

    return AuditService.generate_receipt(case_id=case_id, actor_id=current_user.user_id)


@router.post("/receipts/cases/{case_id}/issue", response_model=EvidenceReceiptResponse)
async def issue_receipt(
    case_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvidenceReceiptResponse:
    """Issue or re-issue a verifiable evidence receipt for a verified or evaluated case."""
    case = _MOCK_CASES_DB.get(case_id)
    if not case:
        raise NotFoundException(f"Case '{case_id}' not found")

    enforce_case_access(
        case_id=case_id,
        case_owner_id=case["user_id"],
        case_org_id=case.get("organization_id"),
        user=current_user,
    )

    return AuditService.generate_receipt(case_id=case_id, actor_id=current_user.user_id)


@router.post("/receipts/verify", response_model=ReceiptVerifyResponse)
async def verify_receipt(
    request: ReceiptVerifyRequest,
) -> ReceiptVerifyResponse:
    """Public cryptographic verification barrier for an evidence receipt token or JSON payload."""
    return AuditService.verify_receipt(
        receipt_token=request.receipt_token,
        payload=request.receipt_payload,
    )
