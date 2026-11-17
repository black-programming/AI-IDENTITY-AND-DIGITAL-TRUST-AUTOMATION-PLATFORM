"""Schemas for Organizations and Employment Claims Verification."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., description="Legal entity name")
    slug: str = Field(..., description="Unique URL/tenant slug")
    verified_domain: Optional[str] = Field(None, description="Corporate verified domain, e.g. acme.org")
    domain: Optional[str] = Field(None, description="Convenience alias for verified_domain")
    jurisdiction: Optional[str] = Field(None, description="Legal jurisdiction, e.g. US-DE")
    registration_number: Optional[str] = None
    country_region: Optional[str] = "GLOBAL"
    tier: Optional[str] = "STANDARD"


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    verified_domain: Optional[str] = None
    registration_number: Optional[str] = None
    country_region: str = "GLOBAL"
    tier: str
    is_active: bool = True
    created_at: datetime


class OrganizationListResponse(BaseModel):
    organizations: List[OrganizationResponse]
    total: int


class MemberItem(BaseModel):
    user_id: str
    role: str
    email: Optional[str] = None
    created_at: datetime


class AddMemberRequest(BaseModel):
    user_id: str = Field(..., description="Target user ID to add to organization")
    role: str = Field("ROLE_ORG_MEMBER", description="Assigned organization role: ROLE_ORG_MEMBER, ROLE_ORG_ADMIN")
    email: Optional[str] = None


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(..., description="New organization role: ROLE_ORG_MEMBER, ROLE_ORG_ADMIN")


class EmploymentClaimCreateRequest(BaseModel):
    """Subject's initial self-asserted employment claim."""
    job_title: str
    department: str
    employee_id: Optional[str] = None
    work_email: str
    start_date: str = Field(..., description="ISO date: YYYY-MM-DD")
    end_date: Optional[str] = None
    evidence_hashes: List[str] = Field(default_factory=list)


class EmploymentClaimVerifyRequest(BaseModel):
    """Organization administrator confirmation or rejection payload."""
    action: str = Field(..., description="CONFIRM or REJECT")
    rejection_reason: Optional[str] = None
    credential_validity_days: Optional[int] = 365


class EmploymentClaimResponse(BaseModel):
    claim_id: str
    user_id: str
    organization_id: str
    organization_name: Optional[str] = None
    job_title: str
    department: str
    employee_id: Optional[str] = None
    employment_status: str
    assertion_type: str = Field(..., description="SELF_ASSERTED, ORGANIZATION_CONFIRMED, INDEPENDENTLY_VERIFIED, REJECTED")
    work_email: str
    start_date: str
    end_date: Optional[str] = None
    credential_expires_at: Optional[datetime] = None
    evidence_hashes: List[str] = Field(default_factory=list)
    confirmed_by_user_id: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
