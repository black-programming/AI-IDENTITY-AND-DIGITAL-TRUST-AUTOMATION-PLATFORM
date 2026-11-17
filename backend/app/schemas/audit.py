"""Schemas for Immutable Audit Trail and Tamper-Evident Hash Chain."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AuditEventCreate(BaseModel):
    """Payload to record a new security-relevant action."""
    case_id: Optional[str] = None
    actor_id: Optional[str] = None
    actor_role: str = "ROLE_SYSTEM"
    action_type: str = Field(..., description="Action identifier, e.g. CASE_CREATED, POLICY_EVALUATION")
    target_resource: str = Field(..., description="Target URI, e.g. cases/c1, evidence/e1")
    outcome: str = Field(default="SUCCESS", description="SUCCESS, DENIED, or ERROR")
    correlation_id: Optional[str] = None
    event_metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditEventItem(BaseModel):
    """Immutable audit record with cryptographic hash link."""
    event_id: str
    case_id: Optional[str] = None
    actor_id: Optional[str] = None
    actor_role: str
    action_type: str
    target_resource: str
    outcome: str
    correlation_id: str
    event_metadata: Dict[str, Any]
    timestamp_utc: datetime
    record_hash: str
    previous_record_hash: str


class AuditEventListResponse(BaseModel):
    """Paginated collection of audit records."""
    total: int
    events: List[AuditEventItem]


class AuditChainVerifyResponse(BaseModel):
    """Result of cryptographic audit chain integrity verification."""
    is_valid: bool
    total_records_checked: int
    last_verified_hash: str
    tampered_record_id: Optional[str] = None
    message: str
