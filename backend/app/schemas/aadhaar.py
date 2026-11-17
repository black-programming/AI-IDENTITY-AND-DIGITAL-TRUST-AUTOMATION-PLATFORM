"""Pydantic Schemas for Aadhaar Card Entity Detection, Extraction, and Verhoeff Validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AadhaarValidateRequest(BaseModel):
    """Request payload to validate a 12-digit Aadhaar number."""
    aadhar_number: str = Field(..., description="12-digit Aadhaar number with optional spaces or hyphens")


class AadhaarValidateResponse(BaseModel):
    """Validation response with Verhoeff checksum result and UIDAI privacy masking."""
    is_valid: bool
    error_code: Optional[str] = None
    message: str
    cleaned_number: str
    masked_number: str
    sha256_hash: str


class EntityBoundingBox(BaseModel):
    """Bounding box coordinates for detected Aadhaar card entity."""
    label: str = Field(..., description="Entity label: 'name', 'dob', 'address', 'aadhar_number'")
    confidence: float = Field(..., ge=0.0, le=1.0)
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    width: int
    height: int


class DetectedEntityItem(BaseModel):
    """Single detected entity with extracted text and bounding box provenance."""
    text: str
    confidence: float
    bbox: EntityBoundingBox


class AadhaarDetectionResponse(BaseModel):
    """Complete response model for Aadhaar entity detection and parsing."""
    status: str = Field(..., description="'SUCCESS', 'PARTIAL', 'FAILED'")
    case_id: Optional[str] = None
    file_id: Optional[str] = None
    detected_entities: Dict[str, Any] = Field(default_factory=dict)
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    bounding_boxes: List[EntityBoundingBox] = Field(default_factory=list)
    verhoeff_valid: bool
    masked_number: str
    detection_method: str = Field(..., description="'YOLOv8' or 'HEURISTIC_SYNTHETIC_DETECTOR'")
    extracted_at: datetime
