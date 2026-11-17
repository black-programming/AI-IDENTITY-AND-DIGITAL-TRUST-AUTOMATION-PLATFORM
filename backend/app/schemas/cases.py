"""Schemas for verification case management."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CaseCreateRequest(BaseModel):
    claim_type: str = Field(..., description="Document claim type, e.g., SYNTH_NAT_ID_V1")
    title: Optional[str] = Field(None, description="Optional case title or claim summary")
    description: Optional[str] = Field(None, description="Detailed case description or business rationale")
    purpose: str = Field("identity_verification", description="Verification purpose / reason")
    priority: str = Field("NORMAL", description="Priority level: LOW, NORMAL, HIGH, URGENT")
    organization_id: Optional[str] = Field(None, description="Optional corporate/enterprise organization scope")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom contextual metadata")


class CaseResponse(BaseModel):
    case_id: str
    user_id: str
    organization_id: Optional[str] = None
    claim_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    purpose: str = "identity_verification"
    status: str
    priority: str = "NORMAL"
    assigned_reviewer_id: Optional[str] = None
    current_decision: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CaseTimelineEvent(BaseModel):
    event_id: str
    case_id: str
    from_status: Optional[str] = None
    to_status: str
    triggered_by: str
    comment: Optional[str] = None
    created_at: datetime


class CaseDetailResponse(CaseResponse):
    timeline: List[CaseTimelineEvent] = Field(default_factory=list, description="Audit timeline of case state transitions")
    allowed_next_transitions: List[str] = Field(default_factory=list, description="Permitted state machine transitions from current state")


class CaseListResponse(BaseModel):
    cases: List[CaseResponse]
    total: int
    limit: int
    offset: int


class CaseSubmitRequest(BaseModel):
    idempotency_key: str = Field(..., description="Client-generated unique UUID to prevent replay")


class CaseTransitionRequest(BaseModel):
    to_status: str = Field(..., description="Target status transition")
    comment: Optional[str] = Field(None, description="Explanation or reviewer reason for state transition")


class CaseAssignRequest(BaseModel):
    reviewer_id: str = Field(..., description="Target reviewer user ID (UUID)")
    comment: Optional[str] = Field(None, description="Assignment notes")


from app.schemas.evidence import (  # noqa: F401
    EvidenceUploadUrlRequest,
    EvidenceUploadUrlResponse,
)
