"""Pydantic schemas for Human Reviewer Queue, Workbench, Field Corrections, and Decisions."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReviewQueueItem(BaseModel):
    case_id: str
    user_id: str
    claim_type: str
    status: str
    priority: str
    reason_codes: List[str] = Field(default_factory=list)
    validation_outcome: Optional[str] = None
    assigned_reviewer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ReviewQueueResponse(BaseModel):
    pending_cases: List[ReviewQueueItem]
    queue_length: int


class WorkbenchEvidenceItem(BaseModel):
    file_id: str
    file_name: str
    mime_type: str
    sha256_hash: str
    quarantine_status: str
    download_url: Optional[str] = None


class ReviewWorkbenchResponse(BaseModel):
    case_id: str
    user_id: str
    claim_type: str
    status: str
    priority: str
    assigned_reviewer_id: Optional[str] = None
    created_at: datetime
    evidence: List[WorkbenchEvidenceItem] = Field(default_factory=list)
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    fields_detail: List[Dict[str, Any]] = Field(default_factory=list)
    validation_report: Optional[Dict[str, Any]] = None
    corrections_history: List[Dict[str, Any]] = Field(default_factory=list)
    permitted_decisions: List[str] = Field(default_factory=lambda: ["ALLOW", "VERIFY", "RESTRICT", "BLOCK"])


class FieldCorrectionItem(BaseModel):
    field_key: str = Field(..., description="Target extracted field key to correct")
    corrected_value: str = Field(..., description="New corrected value")
    justification: str = Field(..., description="Mandatory audit justification for manual override")


class FieldCorrectionRequest(BaseModel):
    corrections: List[FieldCorrectionItem] = Field(..., min_length=1, description="List of field overrides")


class FieldCorrectionResponse(BaseModel):
    case_id: str
    reviewer_id: str
    corrections_applied: List[Dict[str, Any]]
    updated_fields: Dict[str, Any]
    corrected_at: datetime


class RequestEvidenceRequest(BaseModel):
    reason_code: str = Field(..., description="Standard reason code, e.g. DEC_VERIFY_OCR_CONF_LOW, ERR_BLUR_DETECTED")
    guidance: str = Field(..., description="Actionable instruction to citizen explaining required new document")


class ReviewDecisionRequest(BaseModel):
    decision: str = Field(..., description="Manual review outcome: 'ALLOW', 'VERIFY', 'RESTRICT', 'BLOCK'")
    reason_code: str = Field(default="MANUAL_REVIEW_COMPLETED", description="Standardized reason code")
    notes: Optional[str] = Field("", description="Reviewer notes or comments")
    corrections: Optional[List[FieldCorrectionItem]] = Field(default_factory=list)


class ReviewDecisionResponse(BaseModel):
    case_id: str
    reviewer_id: str
    decision: str
    reason_code: str
    new_status: str
    decided_at: datetime
