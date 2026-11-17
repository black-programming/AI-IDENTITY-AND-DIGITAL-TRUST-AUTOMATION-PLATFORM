"""Schemas for Phase 16 AI/ML Risk Evaluation, Model Cards, and Benchmark Metrics."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FeatureContributionItem(BaseModel):
    """Local explainability factor indicating feature impact on risk score."""
    feature_name: str
    feature_value: float
    contribution: float = Field(..., description="Directional impact on risk score: positive increases risk, negative decreases")
    description: str


class SubgroupMetricItem(BaseModel):
    """Evaluation metrics computed across a specific subpopulation slice."""
    subgroup_dimension: str = Field(..., description="E.g. document_type, image_quality, age_band")
    subgroup_value: str = Field(..., description="E.g. PASSPORT, BLURRY, UNDER_18")
    sample_count: int
    accuracy: float
    false_positive_rate: float
    false_negative_rate: float
    f1_score: float


class RiskEvaluationRequest(BaseModel):
    """Request payload for direct feature-based risk evaluation."""
    ocr_confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall OCR confidence score")
    mrz_checksum_valid: bool = Field(..., description="Whether ICAO 9303 MRZ check digits matched")
    days_until_expiry: int = Field(..., description="Days until document expires (negative if already expired)")
    subject_age: int = Field(..., ge=0, le=125, description="Computed age of subject based on date of birth")
    document_resolution_ratio: float = Field(1.0, ge=0.1, le=5.0, description="Aspect/resolution quality multiplier")
    image_blur_metric: float = Field(0.0, ge=0.0, le=100.0, description="Laplacian blur metric (higher is sharper)")
    num_field_mismatches: int = Field(0, ge=0, description="Number of discrepancies between OCR and user assertion")
    document_type: Optional[str] = Field("NATIONAL_ID", description="NATIONAL_ID, DRIVERS_LICENSE, PASSPORT")


class RiskEvaluationResponse(BaseModel):
    """Calibrated risk prediction with explainability factors and human safety recommendations."""
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated risk probability between 0.0 (safe) and 1.0 (high risk)")
    risk_tier: str = Field(..., description="LOW, MODERATE, HIGH, CRITICAL")
    recommendation: str = Field(..., description="APPROVE_ELIGIBLE, ROUTE_TO_HUMAN_REVIEW, STEP_UP_MFA, REJECT_SUSPICIOUS")
    is_safe_fallback_triggered: bool = Field(..., description="True if uncertainty triggers human review fail-safe")
    feature_contributions: List[FeatureContributionItem] = Field(default_factory=list)
    model_version: str
    evaluated_at: datetime


class ModelCardResponse(BaseModel):
    """Standardized Model Card documenting model details, intended use, and limitations."""
    model_name: str
    model_version: str
    model_type: str
    intended_use: str
    training_dataset_summary: str
    evaluation_factors: List[str]
    metrics: Dict[str, float]
    subgroup_performance: List[SubgroupMetricItem]
    ethical_considerations: List[str]
    caveats_and_limitations: List[str]
    updated_at: datetime


class DatasetCardResponse(BaseModel):
    """Standardized Dataset Card documenting evaluation dataset characteristics."""
    dataset_name: str
    dataset_version: str
    total_samples: int
    class_distribution: Dict[str, int]
    slice_distribution: Dict[str, Dict[str, int]]
    synthetic_generation_parameters: List[str]
    pii_safeguards: str
    created_at: datetime


class RiskBenchmarkResponse(BaseModel):
    """Comprehensive benchmark comparison between rule-based baseline and ML model."""
    rule_baseline_metrics: Dict[str, float]
    ml_model_metrics: Dict[str, float]
    confusion_matrices: Dict[str, Dict[str, int]]
    subgroup_comparisons: List[SubgroupMetricItem]
    calibration_metrics: Dict[str, float]
    evaluation_summary: str
    evaluated_at: datetime
