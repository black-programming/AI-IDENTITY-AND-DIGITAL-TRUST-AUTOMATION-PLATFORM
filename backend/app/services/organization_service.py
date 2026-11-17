"""Organization and Employment Verification Service.

Manages organization registration, multi-tenant memberships, self-asserted vs organization-confirmed
employment claims, credential provenance, and cryptographic audit trail logging.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.core.errors import ConflictException, NotFoundException, PermissionDeniedException, ValidationException
from app.core.security import AuthenticatedUser, ROLE_ORG_ADMIN, ROLE_ORG_MEMBER, ROLE_SYS_ADMIN
from app.schemas.organizations import (
    AddMemberRequest,
    EmploymentClaimCreateRequest,
    EmploymentClaimResponse,
    EmploymentClaimVerifyRequest,
    MemberItem,
    OrganizationCreateRequest,
    OrganizationResponse,
)
from app.services.audit_service import AuditService

# In-Memory Database for Organizations
_MOCK_ORGS_DB: Dict[str, Dict[str, Any]] = {
    "org-acme-111": {
        "id": "org-acme-111",
        "name": "Acme Trust Technologies",
        "slug": "acme-trust",
        "verified_domain": "acme.org",
        "registration_number": "REG-ACME-2024",
        "country_region": "US",
        "tier": "ENTERPRISE",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    },
    "org-globex-222": {
        "id": "org-globex-222",
        "name": "Globex Security Corp",
        "slug": "globex-corp",
        "verified_domain": "globex.com",
        "registration_number": "REG-GLOBEX-2025",
        "country_region": "GB",
        "tier": "STANDARD",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    },
}

# In-Memory Database for Organization Memberships
_MOCK_MEMBERSHIPS_DB: Dict[str, List[Dict[str, Any]]] = {
    "org-acme-111": [
        {
            "user_id": "user-acme-admin",
            "role": ROLE_ORG_ADMIN,
            "email": "admin@acme.org",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "user_id": "user-acme-member",
            "role": ROLE_ORG_MEMBER,
            "email": "employee@acme.org",
            "created_at": datetime.now(timezone.utc),
        },
    ],
    "org-globex-222": [
        {
            "user_id": "user-globex-admin",
            "role": ROLE_ORG_ADMIN,
            "email": "admin@globex.com",
            "created_at": datetime.now(timezone.utc),
        },
    ],
}

# In-Memory Database for Employment Claims
_MOCK_EMPLOYMENT_CLAIMS_DB: Dict[str, Dict[str, Any]] = {
    "claim-acme-seed-001": {
        "claim_id": "claim-acme-seed-001",
        "user_id": "user-acme-member",
        "organization_id": "org-acme-111",
        "job_title": "Security Systems Engineer",
        "department": "Trust & Security",
        "employee_id": "EMP-8821",
        "employment_status": "ACTIVE",
        "assertion_type": "ORGANIZATION_CONFIRMED",
        "work_email": "employee@acme.org",
        "start_date": "2023-01-15",
        "end_date": None,
        "credential_expires_at": datetime.now(timezone.utc) + timedelta(days=365),
        "evidence_hashes": ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
        "confirmed_by_user_id": "user-acme-admin",
        "confirmed_at": datetime.now(timezone.utc),
        "rejection_reason": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
}


class OrganizationService:
    @classmethod
    def register_organization(cls, data: OrganizationCreateRequest, creator: AuthenticatedUser) -> OrganizationResponse:
        """Register a new organization entity and designate creator as initial Organization Administrator."""
        # Check slug uniqueness
        for org in _MOCK_ORGS_DB.values():
            if org["slug"].lower() == data.slug.lower():
                raise ConflictException(f"Organization slug '{data.slug}' is already registered")

        org_id = f"org-{uuid.uuid4()}"
        now_utc = datetime.now(timezone.utc)

        org_dict = {
            "id": org_id,
            "name": data.name,
            "slug": data.slug.lower(),
            "verified_domain": data.verified_domain,
            "registration_number": data.registration_number,
            "country_region": data.country_region or "GLOBAL",
            "tier": data.tier or "STANDARD",
            "is_active": True,
            "created_at": now_utc,
        }
        _MOCK_ORGS_DB[org_id] = org_dict

        # Creator becomes ROLE_ORG_ADMIN
        _MOCK_MEMBERSHIPS_DB[org_id] = [
            {
                "user_id": creator.user_id,
                "role": ROLE_ORG_ADMIN,
                "email": creator.email,
                "created_at": now_utc,
            }
        ]

        # Audit Event
        AuditService.record_event(
            action_type="ORGANIZATION_REGISTERED",
            target_resource=f"organizations/{org_id}",
            actor_id=creator.user_id,
            actor_role=creator.role,
            metadata={"org_name": data.name, "slug": data.slug, "tier": org_dict["tier"]},
        )

        return OrganizationResponse(**org_dict)

    @classmethod
    def get_organization(cls, org_id: str) -> OrganizationResponse:
        """Fetch organization profile by ID."""
        org = _MOCK_ORGS_DB.get(org_id)
        if not org:
            raise NotFoundException(f"Organization '{org_id}' not found")
        return OrganizationResponse(**org)

    @classmethod
    def list_organizations(cls, user: AuthenticatedUser) -> List[OrganizationResponse]:
        """List organizations accessible to the caller."""
        if user.role == ROLE_SYS_ADMIN:
            return [OrganizationResponse(**o) for o in _MOCK_ORGS_DB.values()]

        # Filter by organizations user belongs to
        accessible = []
        for org_id, members in _MOCK_MEMBERSHIPS_DB.items():
            if any(m["user_id"] == user.user_id for m in members):
                if org_id in _MOCK_ORGS_DB:
                    accessible.append(OrganizationResponse(**_MOCK_ORGS_DB[org_id]))
        return accessible

    # -------------------------------------------------------------------------
    # Membership Management
    # -------------------------------------------------------------------------
    @classmethod
    def list_members(cls, org_id: str) -> List[MemberItem]:
        """List active members of an organization."""
        members = _MOCK_MEMBERSHIPS_DB.get(org_id, [])
        return [MemberItem(**m) for m in members]

    @classmethod
    def add_member(cls, org_id: str, request: AddMemberRequest, actor: AuthenticatedUser) -> MemberItem:
        """Add a member to the organization with assigned role."""
        if org_id not in _MOCK_MEMBERSHIPS_DB:
            _MOCK_MEMBERSHIPS_DB[org_id] = []

        members = _MOCK_MEMBERSHIPS_DB[org_id]
        for m in members:
            if m["user_id"] == request.user_id:
                raise ConflictException(f"User '{request.user_id}' is already a member of this organization")

        now_utc = datetime.now(timezone.utc)
        new_m = {
            "user_id": request.user_id,
            "role": request.role,
            "email": request.email,
            "created_at": now_utc,
        }
        members.append(new_m)

        AuditService.record_event(
            action_type="ORG_MEMBER_ADDED",
            target_resource=f"organizations/{org_id}/members/{request.user_id}",
            actor_id=actor.user_id,
            actor_role=actor.role,
            metadata={"assigned_role": request.role, "member_email": request.email},
        )

        return MemberItem(**new_m)

    @classmethod
    def remove_member(cls, org_id: str, target_user_id: str, actor: AuthenticatedUser) -> None:
        """Remove a member from the organization."""
        members = _MOCK_MEMBERSHIPS_DB.get(org_id, [])
        initial_len = len(members)
        _MOCK_MEMBERSHIPS_DB[org_id] = [m for m in members if m["user_id"] != target_user_id]

        if len(_MOCK_MEMBERSHIPS_DB[org_id]) == initial_len:
            raise NotFoundException(f"Member '{target_user_id}' not found in organization '{org_id}'")

        AuditService.record_event(
            action_type="ORG_MEMBER_REMOVED",
            target_resource=f"organizations/{org_id}/members/{target_user_id}",
            actor_id=actor.user_id,
            actor_role=actor.role,
        )

    # -------------------------------------------------------------------------
    # Employment Claims Verification
    # -------------------------------------------------------------------------
    @classmethod
    def create_employment_claim(
        cls,
        org_id: str,
        user: AuthenticatedUser,
        data: EmploymentClaimCreateRequest,
    ) -> EmploymentClaimResponse:
        """Subject creates a self-asserted employment claim with corporate credentials."""
        org = _MOCK_ORGS_DB.get(org_id)
        if not org:
            raise NotFoundException(f"Organization '{org_id}' not found")

        claim_id = f"claim-{uuid.uuid4()}"
        now_utc = datetime.now(timezone.utc)

        claim_dict = {
            "claim_id": claim_id,
            "user_id": user.user_id,
            "organization_id": org_id,
            "organization_name": org["name"],
            "job_title": data.job_title,
            "department": data.department,
            "employee_id": data.employee_id,
            "employment_status": "ACTIVE",
            "assertion_type": "SELF_ASSERTED",  # Always begins as SELF_ASSERTED
            "work_email": data.work_email,
            "start_date": data.start_date,
            "end_date": data.end_date,
            "credential_expires_at": None,
            "evidence_hashes": data.evidence_hashes,
            "confirmed_by_user_id": None,
            "confirmed_at": None,
            "rejection_reason": None,
            "created_at": now_utc,
            "updated_at": now_utc,
        }
        _MOCK_EMPLOYMENT_CLAIMS_DB[claim_id] = claim_dict

        # Audit Event
        AuditService.record_event(
            action_type="EMPLOYMENT_CLAIM_SUBMITTED",
            target_resource=f"organizations/{org_id}/claims/{claim_id}",
            actor_id=user.user_id,
            actor_role=user.role,
            metadata={
                "job_title": data.job_title,
                "work_email": data.work_email,
                "assertion_type": "SELF_ASSERTED",
            },
        )

        return EmploymentClaimResponse(**claim_dict)

    @classmethod
    def get_claim(cls, claim_id: str, user: AuthenticatedUser) -> EmploymentClaimResponse:
        """Fetch employment claim details, enforcing tenant or subject isolation."""
        claim = _MOCK_EMPLOYMENT_CLAIMS_DB.get(claim_id)
        if not claim:
            raise NotFoundException(f"Employment claim '{claim_id}' not found")

        # Isolation check: caller must be subject of claim, member of org, or Sys Admin
        is_owner = claim["user_id"] == user.user_id
        is_org_member = user.has_org_access(claim["organization_id"])
        is_admin = user.role == ROLE_SYS_ADMIN

        if not (is_owner or is_org_member or is_admin):
            raise PermissionDeniedException("Access to employment claim denied")

        return EmploymentClaimResponse(**claim)

    @classmethod
    def list_organization_claims(
        cls,
        org_id: str,
        user: AuthenticatedUser,
        assertion_type: Optional[str] = None,
    ) -> List[EmploymentClaimResponse]:
        """List employment claims for an organization."""
        if not (user.has_org_access(org_id) or user.role == ROLE_SYS_ADMIN):
            raise PermissionDeniedException(f"Access to organization '{org_id}' claims denied")

        claims = [c for c in _MOCK_EMPLOYMENT_CLAIMS_DB.values() if c["organization_id"] == org_id]
        if assertion_type:
            claims = [c for c in claims if c["assertion_type"] == assertion_type]

        return [EmploymentClaimResponse(**c) for c in claims]

    @classmethod
    def list_user_claims(cls, user_id: str) -> List[EmploymentClaimResponse]:
        """List all employment claims submitted by a subject."""
        claims = [c for c in _MOCK_EMPLOYMENT_CLAIMS_DB.values() if c["user_id"] == user_id]
        return [EmploymentClaimResponse(**c) for c in claims]

    @classmethod
    def verify_employment_claim(
        cls,
        org_id: str,
        claim_id: str,
        verifier: AuthenticatedUser,
        request: EmploymentClaimVerifyRequest,
    ) -> EmploymentClaimResponse:
        """Authorize or reject an employment claim. Strictly limited to Organization Administrators or System Admins."""
        claim = _MOCK_EMPLOYMENT_CLAIMS_DB.get(claim_id)
        if not claim or claim["organization_id"] != org_id:
            raise NotFoundException(f"Employment claim '{claim_id}' not found under organization '{org_id}'")

        # Must have org admin role or sys admin
        is_authorized = False
        if verifier.role == ROLE_SYS_ADMIN:
            is_authorized = True
        else:
            members = _MOCK_MEMBERSHIPS_DB.get(org_id, [])
            for m in members:
                if m["user_id"] == verifier.user_id and m["role"] == ROLE_ORG_ADMIN:
                    is_authorized = True
                    break

        if not is_authorized:
            raise PermissionDeniedException(
                "Only Organization Administrators or System Admins can verify employment claims"
            )

        now_utc = datetime.now(timezone.utc)

        if request.action.upper() == "CONFIRM":
            claim["assertion_type"] = "ORGANIZATION_CONFIRMED"
            claim["confirmed_by_user_id"] = verifier.user_id
            claim["confirmed_at"] = now_utc
            validity_days = request.credential_validity_days or 365
            claim["credential_expires_at"] = now_utc + timedelta(days=validity_days)
            claim["rejection_reason"] = None
        elif request.action.upper() == "REJECT":
            claim["assertion_type"] = "REJECTED"
            claim["rejection_reason"] = request.rejection_reason or "Organization declined employment affiliation"
            claim["confirmed_by_user_id"] = verifier.user_id
            claim["confirmed_at"] = now_utc
        else:
            raise ValidationException(f"Invalid verification action '{request.action}'. Expected CONFIRM or REJECT.")

        claim["updated_at"] = now_utc

        AuditService.record_event(
            action_type="EMPLOYMENT_CLAIM_VERIFIED",
            target_resource=f"organizations/{org_id}/claims/{claim_id}",
            actor_id=verifier.user_id,
            actor_role=verifier.role,
            metadata={
                "action": request.action.upper(),
                "assertion_type": claim["assertion_type"],
                "expires_at": claim["credential_expires_at"].isoformat() if claim.get("credential_expires_at") else None,
            },
        )

        return EmploymentClaimResponse(**claim)
