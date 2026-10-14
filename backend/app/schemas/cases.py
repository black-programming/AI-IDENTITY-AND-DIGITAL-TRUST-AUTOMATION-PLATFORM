"""Schemas for verification case management."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CaseCreateRequest(BaseModel):
    claim_type: str = Field(..., description="Document claim type, e.g., SYNTH_NAT_ID_V1")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CaseResponse(BaseModel):
    case_id: str
    user_id: str
    claim_type: str
    status: str
    priority: str = "NORMAL"
    current_decision: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CaseSubmitRequest(BaseModel):
    idempotency_key: str = Field(..., description="Client-generated unique UUID to prevent replay")


class EvidenceUploadUrlRequest(BaseModel):
    case_id: str
    file_name: str
    mime_type: str
    sha256_hash: str


class EvidenceUploadUrlResponse(BaseModel):
    upload_url: str
    file_id: str
    bucket: str
    expires_in_seconds: int = 900
