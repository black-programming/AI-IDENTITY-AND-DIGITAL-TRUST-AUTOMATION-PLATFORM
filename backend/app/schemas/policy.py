"""Schemas for Trust Policy Evaluation."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PolicyEvaluationRequest(BaseModel):
    case_id: str
    claim_type: str
    extracted_fields: Dict[str, Any]
    ocr_confidence: float = Field(..., ge=0.0, le=1.0)
    context: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluationResponse(BaseModel):
    case_id: str
    decision: str = Field(..., description="ALLOW, VERIFY, RESTRICT, or BLOCK")
    reason_codes: List[str]
    confidence_score: float
    policy_version: str = "v1.0.0"
    evaluated_at: datetime
    requires_human_review: bool
