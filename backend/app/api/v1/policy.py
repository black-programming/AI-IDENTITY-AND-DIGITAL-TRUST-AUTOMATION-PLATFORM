"""Trust & Policy Engine API Endpoints.

Provides versioned policy catalog inspection, direct multi-dimensional policy evaluation,
dynamic case-level policy evaluation with OCR/validation integration, and explainable decision queries.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.policy import (
    CasePolicyEvaluationRequest,
    PolicyCatalogResponse,
    PolicyEvaluationRequest,
    PolicyEvaluationResponse,
    PolicyRule,
)
from app.services.policy_engine import PolicyEngine

router = APIRouter(prefix="/policy", tags=["Trust & Policy Engine"])


@router.get("/catalog", response_model=PolicyCatalogResponse)
async def get_policy_catalog(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PolicyCatalogResponse:
    """Retrieve catalog of all active versioned trust and policy rules."""
    catalog = PolicyEngine.get_catalog()
    return PolicyCatalogResponse(policies=catalog, total=len(catalog))


@router.get("/rules/{policy_id}", response_model=PolicyRule)
async def get_policy_rule(
    policy_id: str,
    version: str = Query(default="1.0.0", description="Semantic version of policy"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PolicyRule:
    """Inspect full specification and thresholds for a specific policy rule."""
    return PolicyEngine.get_policy(policy_id, version)


@router.post("/evaluate", response_model=PolicyEvaluationResponse)
async def evaluate_policy_direct(
    request: PolicyEvaluationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PolicyEvaluationResponse:
    """Directly evaluate trust policy against provided claims and extracted fields."""
    return PolicyEngine.evaluate(request)


@router.post("/cases/{case_id}/evaluate", response_model=PolicyEvaluationResponse)
async def evaluate_case_policy(
    case_id: str,
    request: Optional[CasePolicyEvaluationRequest] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PolicyEvaluationResponse:
    """Dynamically evaluate policy for an active verification case using stored OCR, validations, and corrections."""
    is_verifier = current_user.role in ("ROLE_VERIFIER", "ROLE_SYS_ADMIN")
    req = request or CasePolicyEvaluationRequest()

    return PolicyEngine.evaluate_case(
        case_id=case_id,
        user_id=current_user.user_id,
        is_verifier=is_verifier,
        policy_id=req.policy_id,
        policy_version=req.policy_version,
        action=req.action,
        resource=req.resource,
        context=req.context,
    )


@router.get("/cases/{case_id}/evaluation", response_model=PolicyEvaluationResponse)
async def get_case_policy_evaluation(
    case_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PolicyEvaluationResponse:
    """Retrieve the latest policy evaluation decision and explanation for a verification case."""
    is_verifier = current_user.role in ("ROLE_VERIFIER", "ROLE_SYS_ADMIN")
    return PolicyEngine.get_case_evaluation(
        case_id=case_id,
        user_id=current_user.user_id,
        is_verifier=is_verifier,
    )
