"""Organization and Employment Verification API.

Handles multi-tenant organization onboarding, membership access control, self-asserted
employment claim submission, administrator confirmations, and provenance tracking.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.errors import NotFoundException, PermissionDeniedException
from app.core.security import (
    AuthenticatedUser,
    ROLE_ORG_ADMIN,
    ROLE_ORG_MEMBER,
    ROLE_SYS_ADMIN,
    get_current_user,
    require_role,
)
from app.schemas.organizations import (
    AddMemberRequest,
    EmploymentClaimCreateRequest,
    EmploymentClaimResponse,
    EmploymentClaimVerifyRequest,
    MemberItem,
    OrganizationCreateRequest,
    OrganizationResponse,
)
from app.services.organization_service import (
    _MOCK_MEMBERSHIPS_DB,
    _MOCK_ORGS_DB,
    OrganizationService,
)

router = APIRouter(prefix="/organizations", tags=["Organizations & Employment"])
claims_router = APIRouter(prefix="/claims", tags=["Employment Claims"])


# -----------------------------------------------------------------------------
# 1. Organization Management
# -----------------------------------------------------------------------------
def user_has_org_access(user: AuthenticatedUser, org_id: str) -> bool:
    if user.has_org_access(org_id):
        return True
    members = _MOCK_MEMBERSHIPS_DB.get(org_id, [])
    return any(m["user_id"] == user.user_id for m in members)


def user_is_org_admin(user: AuthenticatedUser, org_id: str) -> bool:
    if user.role == ROLE_SYS_ADMIN:
        return True
    members = _MOCK_MEMBERSHIPS_DB.get(org_id, [])
    for m in members:
        if m["user_id"] == user.user_id and m["role"] == ROLE_ORG_ADMIN:
            return True
    return False


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    request: OrganizationCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> OrganizationResponse:
    """Register a new organization and grant creator Organization Administrator role."""
    return OrganizationService.register_organization(request, current_user)


@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> List[OrganizationResponse]:
    """List organizations accessible to the caller."""
    return OrganizationService.list_organizations(current_user)


@router.get("/claims/me", response_model=List[EmploymentClaimResponse])
@claims_router.get("/me", response_model=List[EmploymentClaimResponse])
async def list_my_employment_claims(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> List[EmploymentClaimResponse]:
    """Retrieve all employment claims submitted by the current subject."""
    return OrganizationService.list_user_claims(current_user.user_id)


@router.get("/claims/{claim_id}", response_model=EmploymentClaimResponse)
@claims_router.get("/{claim_id}", response_model=EmploymentClaimResponse)
async def get_employment_claim(
    claim_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EmploymentClaimResponse:
    """Inspect employment claim details, enforcing tenant or subject isolation."""
    return OrganizationService.get_claim(claim_id, current_user)


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> OrganizationResponse:
    """Retrieve organization profile with multi-tenant boundary check."""
    org = _MOCK_ORGS_DB.get(org_id)
    if not org:
        raise NotFoundException(f"Organization '{org_id}' not found")

    if not user_has_org_access(current_user, org_id):
        raise PermissionDeniedException(
            f"Cross-organization access denied: user '{current_user.user_id}' does not belong to organization '{org_id}'"
        )

    return OrganizationResponse(**org)


# -----------------------------------------------------------------------------
# 2. Membership Management
# -----------------------------------------------------------------------------
@router.get("/{org_id}/members", response_model=List[MemberItem])
async def list_organization_members(
    org_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> List[MemberItem]:
    """List members of an organization. Restricted to org members and system admins."""
    if not user_has_org_access(current_user, org_id):
        raise PermissionDeniedException(
            f"Cross-organization access denied: user '{current_user.user_id}' does not belong to organization '{org_id}'"
        )

    return OrganizationService.list_members(org_id)


@router.post("/{org_id}/members", response_model=MemberItem, status_code=status.HTTP_201_CREATED)
async def add_organization_member(
    org_id: str,
    request: AddMemberRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MemberItem:
    """Add a member to an organization. Restricted strictly to ROLE_ORG_ADMIN of that org or ROLE_SYS_ADMIN."""
    org = _MOCK_ORGS_DB.get(org_id)
    if not org:
        raise NotFoundException(f"Organization '{org_id}' not found")

    if not user_has_org_access(current_user, org_id):
        raise PermissionDeniedException(
            f"Cross-organization access denied: user '{current_user.user_id}' does not belong to organization '{org_id}'"
        )

    if not user_is_org_admin(current_user, org_id):
        raise PermissionDeniedException("Only Organization Administrators can add members to this organization")

    return OrganizationService.add_member(org_id, request, current_user)


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    org_id: str,
    user_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> None:
    """Remove a member from an organization. Restricted to Organization Admins and System Admins."""
    if not user_has_org_access(current_user, org_id):
        raise PermissionDeniedException(f"Access to organization '{org_id}' denied")

    if not user_is_org_admin(current_user, org_id):
        raise PermissionDeniedException("Only Organization Administrators can remove members")

    OrganizationService.remove_member(org_id, user_id, current_user)


# -----------------------------------------------------------------------------
# 3. Employment Claims Verification
# -----------------------------------------------------------------------------
@router.post("/{org_id}/claims", response_model=EmploymentClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_employment_claim(
    org_id: str,
    request: EmploymentClaimCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EmploymentClaimResponse:
    """Subject submits a self-asserted employment claim for an organization."""
    return OrganizationService.create_employment_claim(org_id, current_user, request)


@router.get("/{org_id}/claims", response_model=List[EmploymentClaimResponse])
async def list_organization_claims(
    org_id: str,
    assertion_type: Optional[str] = Query(default=None, description="Filter: SELF_ASSERTED, ORGANIZATION_CONFIRMED, REJECTED"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> List[EmploymentClaimResponse]:
    """List employment claims for an organization. Restricted to org members and system admins."""
    return OrganizationService.list_organization_claims(org_id, current_user, assertion_type)



@router.post("/{org_id}/claims/{claim_id}/verify", response_model=EmploymentClaimResponse)
async def verify_employment_claim(
    org_id: str,
    claim_id: str,
    request: EmploymentClaimVerifyRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EmploymentClaimResponse:
    """Organization Administrator confirms or rejects a pending employment claim."""
    return OrganizationService.verify_employment_claim(org_id, claim_id, current_user, request)
