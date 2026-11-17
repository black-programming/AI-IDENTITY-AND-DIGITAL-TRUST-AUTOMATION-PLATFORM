"""Schemas for Phase 17 Privacy Hardening — GDPR/CCPA Erasure, Correction, and Data Retention."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RetentionPolicyItem(BaseModel):
    """Retention policy governing evidence, cases, logs, and biometric derivatives."""
    category: str = Field(..., description="E.g. QUARANTINE_EVIDENCE, VERIFIED_CREDENTIALS, AUDIT_LOGS")
    retention_days: int = Field(..., description="Statutory or regulatory retention window in days")
    auto_purge_enabled: bool = Field(..., description="Whether expired assets are automatically purged")
    legal_basis: str = Field(..., description="Regulatory framework: GDPR Art 5(1)(e), ISO 27001, etc.")
    description: str


class RetentionPolicyListResponse(BaseModel):
    """List of configured data retention policies."""
    policies: List[RetentionPolicyItem]
    enforced_at: datetime


class DataErasureRequest(BaseModel):
    """Request by subject to execute right-to-be-forgotten / data deletion."""
    user_id: Optional[str] = Field(None, description="Optional target user ID if requested by admin")
    reason: str = Field("SUBJECT_REQUESTED_DELETION", description="Reason for erasure request")
    confirm_irreversible: bool = Field(..., description="Subject acknowledgment that erasure is permanent")


class DataErasureResponse(BaseModel):
    """Confirmation of completed data erasure and cryptographic tombstone."""
    request_id: str
    user_id: str
    status: str = Field("COMPLETED", description="COMPLETED, REJECTED")
    erased_categories: List[str]
    tombstone_hash: str = Field(..., description="SHA-256 hash anchoring erasure in audit ledger")
    audit_event_id: str
    erased_at: datetime


class DataCorrectionRequest(BaseModel):
    """Request by subject to rectify incorrect personal identity claims."""
    target_field: str = Field(..., description="Field to correct: full_name, email, date_of_birth")
    proposed_value: str = Field(..., description="Corrected value")
    correction_justification: str = Field(..., description="Reason for correction")


class DataCorrectionResponse(BaseModel):
    """Confirmation of recorded identity claim correction."""
    correction_id: str
    user_id: str
    target_field: str
    status: str = Field("RECORDED", description="RECORDED, PENDING_REVIEW")
    recorded_at: datetime


class DataExportResponse(BaseModel):
    """Machine-readable portable export of all subject data (GDPR Art. 20)."""
    user_id: str
    exported_at: datetime
    profile_assertions: Dict[str, Any]
    verification_cases: List[Dict[str, Any]]
    evidence_files_count: int
    delegated_grants_count: int
