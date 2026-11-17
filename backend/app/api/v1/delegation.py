"""API Endpoints for Phase 15 Delegated Authorization and Scoped Capability Grants."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.delegation import (
    DelegationGrantCreateRequest,
    DelegationGrantResponse,
    DelegationGrantRevokeRequest,
    DelegationVerifyRequest,
    DelegationVerifyResponse,
)
from app.services.delegation_service import DelegationService

router = APIRouter(prefix="/delegation", tags=["Delegated Authorization"])


@router.post("/grants", response_model=DelegationGrantResponse, status_code=status.HTTP_201_CREATED)
async def create_delegation_grant(
    request: DelegationGrantCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DelegationGrantResponse:
    """Create a scoped capability delegation grant and return signed delegation token."""
    return DelegationService.create_grant(request, current_user)


@router.get("/grants", response_model=List[DelegationGrantResponse])
async def list_delegation_grants(
    role_type: Optional[str] = Query("all", description="Filter by role: 'all', 'grantor', 'grantee'"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> List[DelegationGrantResponse]:
    """List capability delegation grants visible to the caller."""
    return DelegationService.list_grants(current_user, role_type)


@router.get("/grants/{grant_id}", response_model=DelegationGrantResponse)
async def get_delegation_grant(
    grant_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DelegationGrantResponse:
    """Retrieve details and active status of a specific delegation grant."""
    return DelegationService.get_grant(grant_id, current_user)


@router.post("/grants/{grant_id}/revoke", response_model=DelegationGrantResponse)
async def revoke_delegation_grant(
    grant_id: str,
    request: DelegationGrantRevokeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DelegationGrantResponse:
    """Revoke an active delegation grant immediately with an audit reason."""
    return DelegationService.revoke_grant(grant_id, request.reason, current_user)


@router.post("/verify", response_model=DelegationVerifyResponse)
async def verify_delegated_capability(
    request: DelegationVerifyRequest,
) -> DelegationVerifyResponse:
    """Verify an in-flight delegated capability request against scopes, audience, expiry, replay, and agent status."""
    return DelegationService.verify_delegated_request(request)
