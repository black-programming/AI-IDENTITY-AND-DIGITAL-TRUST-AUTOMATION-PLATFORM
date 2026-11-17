"""Audit Trail API Endpoints — Immutable Log Queries and Cryptographic Chain Verification."""

from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.v1.cases import _MOCK_CASES_DB
from app.core.errors import NotFoundException, PermissionDeniedException
from app.core.security import AuthenticatedUser, enforce_case_access, get_current_user, require_role
from app.schemas.audit import AuditChainVerifyResponse, AuditEventListResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("/events", response_model=AuditEventListResponse)
async def list_audit_events(
    case_id: Optional[str] = Query(default=None, description="Filter by case ID"),
    actor_id: Optional[str] = Query(default=None, description="Filter by actor ID"),
    action_type: Optional[str] = Query(default=None, description="Filter by action type"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuditEventListResponse:
    """Query immutable audit events with role-based visibility rules."""
    is_privileged = current_user.role in ("ROLE_AUDITOR", "ROLE_VERIFIER", "ROLE_SYS_ADMIN")

    if not is_privileged:
        # Non-privileged subjects can only query events for cases they own
        if case_id:
            case = _MOCK_CASES_DB.get(case_id)
            if not case:
                raise NotFoundException(f"Case '{case_id}' not found")
            enforce_case_access(
                case_id=case_id,
                case_owner_id=case["user_id"],
                case_org_id=case.get("organization_id"),
                user=current_user,
            )
        else:
            # Default to filtering only events where current_user was the actor
            actor_id = current_user.user_id

    events, total = AuditService.get_events(
        case_id=case_id,
        actor_id=actor_id,
        action_type=action_type,
        limit=limit,
        offset=offset,
    )
    return AuditEventListResponse(total=total, events=events)


@router.get("/cases/{case_id}", response_model=AuditEventListResponse)
async def get_case_audit_history(
    case_id: str,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuditEventListResponse:
    """Retrieve complete immutable audit history for a specific verification case."""
    case = _MOCK_CASES_DB.get(case_id)
    if not case:
        raise NotFoundException(f"Case '{case_id}' not found")

    enforce_case_access(
        case_id=case_id,
        case_owner_id=case["user_id"],
        case_org_id=case.get("organization_id"),
        user=current_user,
    )

    events, total = AuditService.get_events(case_id=case_id, limit=limit, offset=offset)
    return AuditEventListResponse(total=total, events=events)


@router.post("/verify-chain", response_model=AuditChainVerifyResponse)
async def verify_audit_hash_chain(
    current_user: AuthenticatedUser = Depends(require_role(["ROLE_AUDITOR", "ROLE_SYS_ADMIN", "ROLE_VERIFIER"])),
) -> AuditChainVerifyResponse:
    """Cryptographically verify the SHA-256 hash chaining of all recorded audit events."""
    return AuditService.verify_audit_chain()
