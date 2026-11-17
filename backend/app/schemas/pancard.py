"""Pydantic Schemas for PAN Card Entity Detection, Extraction, and Regulatory Validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PANValidateRequest(BaseModel):
    """Request payload to validate a 10-character Indian PAN number."""
    pan_number: str = Field(..., description="10-character PAN number (e.g. ABCPS1234F)")
    applicant_surname: Optional[str] = Field(None, description="Optional applicant surname to cross-verify against 5th character")


class PANValidateResponse(BaseModel):
    """Validation response with structural check, entity type decoding, and surname consistency."""
    is_valid: bool
    error_code: Optional[str] = None
    message: str
    cleaned_number: str
    masked_number: str
    holder_type_code: Optional[str] = None
    holder_type_description: Optional[str] = None
    surname_match: Optional[bool] = None
    sha256_hash: str


class PANEntityBoundingBox(BaseModel):
    """Bounding box coordinates for detected PAN card entity."""
    label: str = Field(..., description="Entity label: 'pan_number', 'name', 'father_name', 'dob'")
    confidence: float = Field(..., ge=0.0, le=1.0)
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    width: int
    height: int


class PANDetectionResponse(BaseModel):
    """Complete response model for PAN card entity detection and parsing."""
    status: str = Field(..., description="'SUCCESS', 'PARTIAL', 'FAILED'")
    case_id: Optional[str] = None
    file_id: Optional[str] = None
    detected_entities: Dict[str, Any] = Field(default_factory=dict)
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    bounding_boxes: List[PANEntityBoundingBox] = Field(default_factory=list)
    pan_valid: bool
    masked_number: str
    detection_method: str = Field(..., description="'YOLOv8' or 'HEURISTIC_SYNTHETIC_DETECTOR'")
    extracted_at: datetime
