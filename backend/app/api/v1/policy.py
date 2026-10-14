"""Policy evaluation API endpoint."""

from fastapi import APIRouter, Depends
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.policy import PolicyEvaluationRequest, PolicyEvaluationResponse
from app.services.policy_engine import PolicyEngine

router = APIRouter()


@router.post("/policy/evaluate", response_model=PolicyEvaluationResponse, tags=["Policy"])
async def evaluate_policy(
    request: PolicyEvaluationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PolicyEvaluationResponse:
    return PolicyEngine.evaluate(request)
