"""Secure Evidence Ingestion & Quarantine API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.v1.cases import _MOCK_CASES_DB, _record_timeline_event
from app.core.errors import (
    CaseNotFoundException,
    EvidenceNotFoundException,
    NotFoundException,
    QuarantineViolationException,
)
from app.core.security import AuthenticatedUser, enforce_case_access, get_current_user
from app.schemas.evidence import (
    EvidenceDownloadUrlResponse,
    EvidenceFileResponse,
    EvidenceListResponse,
    EvidenceUploadUrlRequest,
    EvidenceUploadUrlResponse,
    EvidenceVerifyRequest,
    EvidenceVerifyResponse,
)
from app.services.evidence_service import EvidenceService, _MOCK_EVIDENCE_DB

router = APIRouter(tags=["Evidence"])


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


# -----------------------------------------------------------------------------
# 1. Pre-Signed Upload URL Endpoints
# -----------------------------------------------------------------------------
@router.post(
    "/cases/{case_id}/evidence/upload-url",
    response_model=EvidenceUploadUrlResponse,
    status_code=status.HTTP_200_OK,
)
async def create_case_upload_url(
    case_id: str,
    request: EvidenceUploadUrlRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvidenceUploadUrlResponse:
    """Generate pre-signed upload URL for evidence ingestion into private quarantine bucket."""
    # Ensure URL path case_id matches request body or override
    target_case_id = case_id or request.case_id
    _verify_case_and_access(target_case_id, current_user)

    result = EvidenceService.create_upload_url(
        case_id=target_case_id,
        file_name=request.file_name,
        mime_type=request.mime_type,
        file_size_bytes=request.file_size_bytes or 0,
        sha256_hash=request.sha256_hash,
    )
    return EvidenceUploadUrlResponse(**result)


@router.post(
    "/evidence/upload-url",
    response_model=EvidenceUploadUrlResponse,
    status_code=status.HTTP_200_OK,
)
async def create_upload_url_root(
    request: EvidenceUploadUrlRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvidenceUploadUrlResponse:
    """Generate pre-signed upload URL via root evidence endpoint."""
    _verify_case_and_access(request.case_id, current_user)

    result = EvidenceService.create_upload_url(
        case_id=request.case_id,
        file_name=request.file_name,
        mime_type=request.mime_type,
        file_size_bytes=request.file_size_bytes or 0,
        sha256_hash=request.sha256_hash,
    )
    return EvidenceUploadUrlResponse(**result)


# -----------------------------------------------------------------------------
# 2. Direct Evidence Upload (Multipart / Form-Data)
# -----------------------------------------------------------------------------
@router.post(
    "/cases/{case_id}/evidence/upload",
    response_model=EvidenceFileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_evidence_direct(
    case_id: str,
    file: UploadFile = File(...),
    sha256_hash: Optional[str] = Form(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvidenceFileResponse:
    """Directly upload evidence file with magic byte inspection and checksum enforcement."""
    case = _verify_case_and_access(case_id, current_user)

    content = await file.read()
    evidence = EvidenceService.validate_and_ingest_file(
        case_id=case_id,
        file_name=file.filename or "unknown_file",
        content=content,
        declared_mime_type=file.content_type,
        client_sha256=sha256_hash,
    )

    # Record timeline event in the verification case
    _record_timeline_event(
        case_id=case_id,
        from_status=case.get("status"),
        to_status=case.get("status"),
        triggered_by=current_user.user_id,
        comment=f"Evidence uploaded: '{evidence['file_name']}' (SHA-256: {evidence['sha256_hash'][:8]}...). Status: {evidence['quarantine_status']}",
    )

    return EvidenceFileResponse(**evidence)


# -----------------------------------------------------------------------------
# 3. List Evidence for Case
# -----------------------------------------------------------------------------
@router.get(
    "/cases/{case_id}/evidence",
    response_model=EvidenceListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_case_evidence(
    case_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvidenceListResponse:
    """List all evidence files associated with a case with their quarantine statuses."""
    _verify_case_and_access(case_id, current_user)
    items = EvidenceService.list_evidence_for_case(case_id)
    return EvidenceListResponse(
        evidence=[EvidenceFileResponse(**item) for item in items],
        total=len(items),
    )


# -----------------------------------------------------------------------------
# 4. Evidence Record Detail
# -----------------------------------------------------------------------------
@router.get(
    "/cases/{case_id}/evidence/{file_id}",
    response_model=EvidenceFileResponse,
    status_code=status.HTTP_200_OK,
)
async def get_evidence_detail(
    case_id: str,
    file_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvidenceFileResponse:
    """Retrieve full metadata of an evidence record."""
    _verify_case_and_access(case_id, current_user)
    evidence = EvidenceService.get_evidence(file_id)
    if not evidence or evidence["case_id"] != case_id:
        raise EvidenceNotFoundException(file_id)
    return EvidenceFileResponse(**evidence)


# -----------------------------------------------------------------------------
# 5. Pre-Signed Download URL Endpoints
# -----------------------------------------------------------------------------
@router.get(
    "/cases/{case_id}/evidence/{file_id}/download-url",
    response_model=EvidenceDownloadUrlResponse,
    status_code=status.HTTP_200_OK,
)
async def get_evidence_download_url(
    case_id: str,
    file_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvidenceDownloadUrlResponse:
    """Generate short-lived signed download URL with quarantine security check."""
    _verify_case_and_access(case_id, current_user)
    is_reviewer = current_user.is_reviewer() or current_user.is_auditor()

    result = EvidenceService.create_download_url(
        file_id=file_id,
        case_id=case_id,
        is_reviewer=is_reviewer,
    )
    if not result:
        raise EvidenceNotFoundException(file_id)

    return EvidenceDownloadUrlResponse(**result)


@router.get(
    "/evidence/{file_id}/download-url",
    response_model=EvidenceDownloadUrlResponse,
    status_code=status.HTTP_200_OK,
)
async def get_download_url_root(
    file_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvidenceDownloadUrlResponse:
    """Root endpoint for short-lived signed download URL."""
    evidence = EvidenceService.get_evidence(file_id)
    if not evidence:
        raise EvidenceNotFoundException(file_id)

    _verify_case_and_access(evidence["case_id"], current_user)
    is_reviewer = current_user.is_reviewer() or current_user.is_auditor()

    result = EvidenceService.create_download_url(
        file_id=file_id,
        case_id=evidence["case_id"],
        is_reviewer=is_reviewer,
    )
    return EvidenceDownloadUrlResponse(**result)


# -----------------------------------------------------------------------------
# 6. Verify Upload Checksum / Quarantine Confirmation
# -----------------------------------------------------------------------------
@router.post(
    "/cases/{case_id}/evidence/{file_id}/verify",
    response_model=EvidenceVerifyResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_evidence_upload(
    case_id: str,
    file_id: str,
    request: EvidenceVerifyRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvidenceVerifyResponse:
    """Confirm upload completion and verify checksum against quarantine record."""
    _verify_case_and_access(case_id, current_user)
    evidence = EvidenceService.get_evidence(file_id)
    if not evidence or evidence["case_id"] != case_id:
        raise EvidenceNotFoundException(file_id)

    # Check checksum match
    stored_hash = evidence.get("sha256_hash", "")
    client_hash = request.sha256_hash.strip().lower()

    if stored_hash and stored_hash != client_hash:
        evidence["quarantine_status"] = "REJECTED"
        return EvidenceVerifyResponse(
            file_id=file_id,
            sha256_verified=False,
            quarantine_status="REJECTED",
            message="SHA-256 checksum mismatch. File flagged as REJECTED in quarantine.",
        )

    evidence["quarantine_status"] = "CLEARED"
    if not stored_hash:
        evidence["sha256_hash"] = client_hash

    return EvidenceVerifyResponse(
        file_id=file_id,
        sha256_verified=True,
        quarantine_status="CLEARED",
        message="SHA-256 checksum verified. File cleared from quarantine for processing.",
    )
