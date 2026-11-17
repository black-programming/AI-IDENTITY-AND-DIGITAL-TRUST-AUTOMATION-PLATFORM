"""Schemas for Phase 15 Delegated Authorization and Scoped Capability Grants."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


VALID_DELEGATION_ACTIONS = {
    "read:evidence",
    "write:evidence",
    "submit:claim",
    "execute:ocr",
    "extract:ocr",
    "validate:rules",
    "evaluate:policy",
    "request:review",
    "audit:read",
    "task:execute",
}


class DelegationGrantCreateRequest(BaseModel):
    """Request payload to create a scoped capability delegation grant."""
    grantee_id: str = Field(..., description="Target user ID or AI agent slug/ID receiving the delegation")
    grantee_type: str = Field("AI_AGENT", description="AI_AGENT or HUMAN_DELEGATE")
    actions: List[str] = Field(..., description="Permitted capability actions (e.g. read:evidence, evaluate:policy)")
    resources: List[str] = Field(default_factory=lambda: ["*"], description="Permitted resource patterns (e.g. case:*, org:org-acme-111, case:case-123)")
    audiences: List[str] = Field(default_factory=lambda: ["https://api.trustplatform.internal"], description="Permitted audience/service identifiers (e.g. https://api.trustplatform.internal)")
    scope: Optional[str] = Field(None, description="Optional OAuth-style scope string")
    validity_hours: Optional[int] = Field(24, ge=1, le=720, description="Validity duration in hours (1-720)")
    notes: Optional[str] = Field(None, max_length=500, description="Optional delegation description or business purpose")

    @field_validator("actions")
    @classmethod
    def validate_actions(cls, actions: List[str]) -> List[str]:
        if not actions:
            raise ValueError("Delegation must specify at least one action")
        for act in actions:
            if act not in VALID_DELEGATION_ACTIONS and not act.startswith("custom:"):
                raise ValueError(f"Unsupported action '{act}'. Allowed: {sorted(VALID_DELEGATION_ACTIONS)} or 'custom:*'")
        return actions

    @field_validator("resources")
    @classmethod
    def validate_resources(cls, resources: List[str]) -> List[str]:
        if not resources:
            raise ValueError("Delegation must specify at least one target resource or pattern")
        return resources

    @field_validator("audiences")
    @classmethod
    def validate_audiences(cls, audiences: List[str]) -> List[str]:
        if not audiences:
            raise ValueError("Delegation must specify at least one audience target")
        return audiences

    @field_validator("grantee_type")
    @classmethod
    def validate_grantee_type(cls, g_type: str) -> str:
        if g_type.upper() not in ("AI_AGENT", "HUMAN_DELEGATE"):
            raise ValueError("grantee_type must be either 'AI_AGENT' or 'HUMAN_DELEGATE'")
        return g_type.upper()


class DelegationGrantRevokeRequest(BaseModel):
    """Payload to revoke an active capability delegation grant."""
    reason: str = Field(..., min_length=5, max_length=500, description="Formal revocation reason for audit logging")


class DelegationGrantResponse(BaseModel):
    """Complete response representation of a scoped delegation grant."""
    id: str
    grantor_id: str
    grantee_id: str
    grantee_type: str
    actions: List[str]
    resources: List[str]
    audiences: List[str]
    status: str = Field(..., description="ACTIVE, REVOKED, EXPIRED")
    delegation_token: str
    token_fingerprint: str
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revocation_reason: Optional[str] = None
    created_at: datetime
    is_active: bool


class DelegationVerifyRequest(BaseModel):
    """Request payload to verify and evaluate an in-flight delegated capability request."""
    delegation_token: str = Field(..., description="Signed cryptographic delegation token or grant ID")
    requested_action: str = Field(..., description="Action requested to be performed (e.g. read:evidence)")
    requested_resource: str = Field(..., description="Resource target (e.g. case:case-123)")
    audience: str = Field(..., description="Receiving service audience identifier")
    nonce: Optional[str] = Field(None, description="One-time cryptographically unique nonce for replay protection")


class DelegationVerifyResponse(BaseModel):
    """Evaluation response assessing delegated authorization validity and scope matching."""
    is_valid: bool
    decision: str = Field(..., description="ALLOW or DENIED")
    reason_code: str = Field(..., description="Decision code: e.g. AUTHORIZED, ACTION_OUT_OF_SCOPE, RESOURCE_OUT_OF_SCOPE, AUDIENCE_MISMATCH, GRANT_EXPIRED, GRANT_REVOKED, NONCE_ALREADY_USED, GRANTEE_AGENT_INACTIVE")
    grantor_id: Optional[str] = None
    grantee_id: Optional[str] = None
    grantee_type: Optional[str] = None
    granted_actions: List[str] = Field(default_factory=list)
    granted_resources: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    message: str


class DelegationGrantListResponse(BaseModel):
    """List response for delegation grants."""
    grants: List[DelegationGrantResponse]
    total: int
