"""Pydantic schemas for deterministic document validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ValidationRuleResult(BaseModel):
    rule_id: str = Field(..., description="Unique rule code, e.g. VAL-REQUIRED-FIELDS")
    rule_name: str = Field(..., description="Human-readable rule name")
    passed: bool
    details: str
    reason_codes: List[str] = Field(default_factory=list)


class DocumentValidationRequest(BaseModel):
    claim_type: Optional[str] = Field(None, description="Document type claim override (defaults to case claim_type)")
    extracted_fields: Optional[Dict[str, Any]] = Field(None, description="Extracted fields dictionary (defaults to OCR output if omitted)")
    user_profile: Optional[Dict[str, Any]] = Field(None, description="Optional profile assertions for cross-field consistency checks")
    file_id: Optional[str] = Field(None, description="Evidence file ID to validate")


class DocumentValidationResponse(BaseModel):
    validation_id: str
    case_id: str
    file_id: Optional[str] = None
    validation_passed: bool
    overall_outcome: str = Field(..., description="Overall validation outcome: 'PASS', 'FAIL', or 'FLAGGED'")
    flags: List[str] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    rule_results: List[ValidationRuleResult] = Field(default_factory=list)
    validated_at: datetime
