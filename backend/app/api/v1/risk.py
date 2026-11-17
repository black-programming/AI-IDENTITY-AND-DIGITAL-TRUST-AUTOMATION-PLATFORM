"""API Endpoints for Phase 16 AI/ML Risk Evaluation, Benchmark Metrics, and Model Cards."""

from fastapi import APIRouter, Depends, status

from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.risk import (
    DatasetCardResponse,
    ModelCardResponse,
    RiskBenchmarkResponse,
    RiskEvaluationRequest,
    RiskEvaluationResponse,
)
from app.services.risk_evaluation_service import RiskEvaluationService

router = APIRouter(prefix="/risk", tags=["AI/ML Risk Evaluation"])


@router.post("/predict", response_model=RiskEvaluationResponse)
async def predict_risk(
    request: RiskEvaluationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RiskEvaluationResponse:
    """Evaluate calibrated risk probability and explainability factors for a feature vector."""
    return RiskEvaluationService.evaluate_features(request)


@router.post("/evaluate-case/{case_id}", response_model=RiskEvaluationResponse)
async def evaluate_case_risk(
    case_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RiskEvaluationResponse:
    """Assess risk score for a verification case and log evaluation to the tamper-evident audit ledger."""
    return RiskEvaluationService.evaluate_case(case_id, current_user)


@router.get("/benchmark", response_model=RiskBenchmarkResponse)
async def get_benchmark_comparison(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RiskBenchmarkResponse:
    """Retrieve comprehensive benchmark comparison between rule-based baseline and calibrated ML classifier."""
    return RiskEvaluationService.get_benchmark_comparison()


@router.get("/dataset-card", response_model=DatasetCardResponse)
async def get_dataset_card() -> DatasetCardResponse:
    """Retrieve standardized Dataset Card documenting evaluation dataset characteristics and slices."""
    return RiskEvaluationService.get_dataset_card()


@router.get("/model-card", response_model=ModelCardResponse)
async def get_model_card() -> ModelCardResponse:
    """Retrieve standardized Model Card documenting model architecture, performance, and ethical safeguards."""
    return RiskEvaluationService.get_model_card()
