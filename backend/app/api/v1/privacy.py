"""API Endpoints for Phase 17 Privacy & Data Governance (GDPR/CCPA/Retention)."""

from fastapi import APIRouter, Depends, status

from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.privacy import (
    DataCorrectionRequest,
    DataCorrectionResponse,
    DataErasureRequest,
    DataErasureResponse,
    DataExportResponse,
    RetentionPolicyListResponse,
)
from app.services.privacy_service import PrivacyService

router = APIRouter(prefix="/privacy", tags=["Privacy & Data Governance"])


@router.get("/retention-policy", response_model=RetentionPolicyListResponse)
async def get_retention_policies() -> RetentionPolicyListResponse:
    """Retrieve statutory data retention schedules for evidence, cases, and logs."""
    return PrivacyService.get_retention_policies()


@router.post("/erasure-request", response_model=DataErasureResponse, status_code=status.HTTP_200_OK)
async def request_data_erasure(
    request: DataErasureRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DataErasureResponse:
    """Execute Right-to-be-Forgotten data deletion with cryptographic tombstone audit proof."""
    return PrivacyService.execute_data_erasure(current_user.user_id, request, current_user)


@router.post("/correction-request", response_model=DataCorrectionResponse, status_code=status.HTTP_200_OK)
async def request_data_correction(
    request: DataCorrectionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DataCorrectionResponse:
    """Submit request to rectify incorrect personal identity assertions."""
    return PrivacyService.record_data_correction(current_user.user_id, request, current_user)


@router.get("/export-data", response_model=DataExportResponse)
async def export_my_data(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DataExportResponse:
    """Export complete machine-readable bundle of subject identity assertions, cases, and evidence (GDPR Art. 20)."""
    return PrivacyService.export_subject_data(current_user.user_id, current_user)
