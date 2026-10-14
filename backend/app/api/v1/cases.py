"""Verification Case Management Endpoints."""

import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, status

from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.cases import (
    CaseCreateRequest,
    CaseResponse,
    CaseSubmitRequest,
    EvidenceUploadUrlRequest,
    EvidenceUploadUrlResponse,
)

router = APIRouter()


@router.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED, tags=["Cases"])
async def create_case(
    request: CaseCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CaseResponse:
    now = datetime.now(timezone.utc)
    return CaseResponse(
        case_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        claim_type=request.claim_type,
        status="Draft",
        priority="NORMAL",
        current_decision=None,
        created_at=now,
        updated_at=now,
    )


@router.post("/cases/{case_id}/submit", tags=["Cases"])
async def submit_case(
    case_id: str,
    request: CaseSubmitRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    return {
        "case_id": case_id,
        "status": "Submitted",
        "idempotency_key": request.idempotency_key,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/evidence/upload-url", response_model=EvidenceUploadUrlResponse, tags=["Evidence"])
async def get_upload_url(
    request: EvidenceUploadUrlRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvidenceUploadUrlResponse:
    file_id = str(uuid.uuid4())
    # Mock pre-signed URL generator pointing to Supabase private storage
    mock_signed_url = f"https://mock.storage.supabase.co/upload/{request.case_id}/{file_id}?token=temp"
    return EvidenceUploadUrlResponse(
        upload_url=mock_signed_url,
        file_id=file_id,
        bucket="evidence-quarantine",
        expires_in_seconds=900,
    )
