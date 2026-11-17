"""Schemas for Trust & Policy Engine.

Covers versioned policy catalogs, multi-dimensional evaluation requests/responses,
reason codes, scope restrictions, and explainable decision outputs.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PolicyRule(BaseModel):
    """Specification of an active versioned policy rule."""
    policy_id: str = Field(..., description="Unique policy identifier, e.g. POL-IDENTITY-BASIC-V1")
    version: str = Field(..., description="Semantic version string, e.g. 1.0.0")
    name: str = Field(..., description="Human-readable policy title")
    description: Optional[str] = None
    target_action: str = Field(..., description="Action evaluated by this policy, e.g. identity.verify")
    target_resource: str = Field(..., description="Resource protected, e.g. claims:synthetic_identity")
    required_scopes: List[str] = Field(default_factory=list)
    confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    rule_spec: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class PolicyCatalogResponse(BaseModel):
    """Catalog of registered versioned policies."""
    policies: List[PolicyRule]
    total: int


class PolicyEvaluationRequest(BaseModel):
    """Direct request to evaluate policy rules against extracted evidence."""
    case_id: str
    claim_type: str
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    ocr_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    validation_flags: List[str] = Field(default_factory=list)
    policy_id: Optional[str] = "POL-IDENTITY-BASIC-V1"
    policy_version: Optional[str] = "1.0.0"
    action: Optional[str] = "identity.verify"
    resource: Optional[str] = "claims:synthetic_identity"
    context: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluationResponse(BaseModel):
    """Structured, explainable trust policy evaluation output."""
    evaluation_id: Optional[str] = None
    case_id: str
    policy_id: str = "POL-IDENTITY-BASIC-V1"
    policy_version: str = "1.0.0"
    decision: str = Field(..., description="Contextual outcome: ALLOW, VERIFY, RESTRICT, or BLOCK")
    reason_codes: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    permitted_scopes: List[str] = Field(default_factory=list)
    restricted_scopes: List[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    requires_human_review: bool = False
    evaluated_at: datetime
    explanation: Optional[str] = None


class CasePolicyEvaluationRequest(BaseModel):
    """Request to evaluate a case dynamically using persisted OCR and validation findings."""
    policy_id: Optional[str] = "POL-IDENTITY-BASIC-V1"
    policy_version: Optional[str] = "1.0.0"
    action: Optional[str] = "identity.verify"
    resource: Optional[str] = "claims:synthetic_identity"
    context: Dict[str, Any] = Field(default_factory=dict)
