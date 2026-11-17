"""Pydantic schemas for OCR extraction pipeline, field provenance, and confidence scoring."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    width: int
    height: int


class ExtractedFieldItem(BaseModel):
    field_key: str
    field_value: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence score from 0.00 to 1.00")
    bounding_box: Optional[BoundingBox] = None
    ocr_engine: str
    engine_version: str
    extracted_at: datetime


class OCRExtractionRequest(BaseModel):
    file_id: Optional[str] = Field(None, description="Target evidence file ID; defaults to latest evidence if omitted")
    engine_preference: Optional[str] = Field(None, description="Preferred OCR engine ('Tesseract', 'PaddleOCR', 'Auto')")
    auto_rotate: bool = Field(True, description="Attempt image orientation detection and auto-correction")


class OCRExtractionResponse(BaseModel):
    case_id: str
    file_id: str
    ocr_engine: str
    engine_version: str
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    is_conclusive: bool
    status: str = Field(..., description="Extraction outcome: 'SUCCESS', 'INCONCLUSIVE', 'FAILED'")
    reason_codes: List[str] = Field(default_factory=list)
    extracted_fields: Dict[str, Any] = Field(default_factory=dict, description="Key-value mapping of extracted fields")
    fields_detail: List[ExtractedFieldItem] = Field(default_factory=list, description="Structured fields with provenance metadata")
    raw_text: Optional[str] = None
    image_metadata: Dict[str, Any] = Field(default_factory=dict)
    extracted_at: datetime


class CaseExtractedFieldsSummaryResponse(BaseModel):
    case_id: str
    total_fields: int
    average_confidence: float
    is_conclusive: bool
    extracted_fields: Dict[str, Any]
    fields_detail: List[ExtractedFieldItem]
