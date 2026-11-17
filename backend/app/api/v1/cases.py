"""Verification Case Management Endpoints (Phase 6)."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.errors import (
    InvalidStateTransitionException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from app.core.security import (
    AuthenticatedUser,
    ROLE_ORG_ADMIN,
    ROLE_ORG_MEMBER,
    ROLE_SUBJECT,
    ROLE_SYS_ADMIN,
    ROLE_VERIFIER,
    enforce_case_access,
    get_current_user,
    require_reviewer_or_admin,
)
from app.schemas.cases import (
    CaseAssignRequest,
    CaseCreateRequest,
    CaseDetailResponse,
    CaseListResponse,
    CaseResponse,
    CaseSubmitRequest,
    CaseTimelineEvent,
    CaseTransitionRequest,
    EvidenceUploadUrlRequest,
    EvidenceUploadUrlResponse,
)

router = APIRouter()

# Formal state machine transitions
VALID_TRANSITIONS: Dict[str, List[str]] = {
    "Draft": ["Submitted", "Cancelled"],
    "Submitted": ["Processing", "Under Review", "Cancelled"],
    "Processing": ["Under Review", "Verified", "Action Required", "Restricted", "Rejected"],
    "Under Review": ["Verified", "Rejected", "Action Required", "Restricted"],
    "Action Required": ["Submitted", "Rejected", "Cancelled"],
    "Restricted": ["Under Review", "Rejected"],
    "Verified": [],   # Terminal state (requires formal appeal)
    "Rejected": [],   # Terminal state (requires formal appeal)
    "Cancelled": [],  # Terminal state
}

# In-memory database of cases and timeline events
_MOCK_CASES_DB: Dict[str, Dict[str, Any]] = {
    "00000000-0000-0000-0000-000000000001": {
        "case_id": "00000000-0000-0000-0000-000000000001",
        "user_id": "a0000000-0000-0000-0000-000000000001",
        "organization_id": None,
        "claim_type": "SYNTH_NAT_ID_V1",
        "purpose": "identity_verification",
        "status": "Draft",
        "priority": "NORMAL",
        "assigned_reviewer_id": None,
        "current_decision": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    "00000000-0000-0000-0000-000000000002": {
        "case_id": "00000000-0000-0000-0000-000000000002",
        "user_id": "a0000000-0000-0000-0000-000000000001",
        "organization_id": None,
        "claim_type": "SYNTH_DL_V1",
        "purpose": "employment_check",
        "status": "Under Review",
        "priority": "HIGH",
        "assigned_reviewer_id": None,
        "current_decision": "VERIFY",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    "case-user-b-999": {
        "case_id": "case-user-b-999",
        "user_id": "user-b-target-uuid",
        "organization_id": "org-b-uuid",
        "claim_type": "SYNTH_PASSPORT_V1",
        "purpose": "corporate_onboarding",
        "status": "Submitted",
        "priority": "NORMAL",
        "assigned_reviewer_id": None,
        "current_decision": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
}

_MOCK_TIMELINE_DB: Dict[str, List[Dict[str, Any]]] = {
    "00000000-0000-0000-0000-000000000001": [
        {
            "event_id": "evt-seed-001",
            "case_id": "00000000-0000-0000-0000-000000000001",
            "from_status": None,
            "to_status": "Draft",
            "triggered_by": "a0000000-0000-0000-0000-000000000001",
            "comment": "Case initiated in Draft mode",
            "created_at": datetime.now(timezone.utc),
        }
    ],
    "00000000-0000-0000-0000-000000000002": [
        {
            "event_id": "evt-seed-002",
            "case_id": "00000000-0000-0000-0000-000000000002",
            "from_status": "Draft",
            "to_status": "Submitted",
            "triggered_by": "a0000000-0000-0000-0000-000000000001",
            "comment": "Documents submitted for identity check",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "event_id": "evt-seed-003",
            "case_id": "00000000-0000-0000-0000-000000000002",
            "from_status": "Submitted",
            "to_status": "Under Review",
            "triggered_by": "system_policy_engine",
            "comment": "Escalated for human verification: OCR confidence low",
            "created_at": datetime.now(timezone.utc),
        },
    ],
}


def _record_timeline_event(
    case_id: str,
    from_status: Optional[str],
    to_status: str,
    triggered_by: str,
    comment: Optional[str] = None,
) -> CaseTimelineEvent:
    event = {
        "event_id": f"evt-{uuid.uuid4()}",
        "case_id": case_id,
        "from_status": from_status,
        "to_status": to_status,
        "triggered_by": triggered_by,
        "comment": comment,
        "created_at": datetime.now(timezone.utc),
    }
    _MOCK_TIMELINE_DB.setdefault(case_id, []).append(event)
    return CaseTimelineEvent(**event)


@router.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED, tags=["Cases"])
async def create_case(
    request: CaseCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CaseResponse:
    """Create a new verification case in Draft status."""
    if not request.claim_type or len(request.claim_type.strip()) == 0:
        raise ValidationException("claim_type is required")

    now = datetime.now(timezone.utc)
    case_id = str(uuid.uuid4())
    case_record = {
        "case_id": case_id,
        "user_id": current_user.user_id,
        "organization_id": request.organization_id,
        "claim_type": request.claim_type.strip(),
        "title": request.title,
        "description": request.description,
        "purpose": request.purpose,
        "status": "Draft",
        "priority": request.priority,
        "assigned_reviewer_id": None,
        "current_decision": None,
        "created_at": now,
        "updated_at": now,
    }
    _MOCK_CASES_DB[case_id] = case_record
    _record_timeline_event(
        case_id=case_id,
        from_status=None,
        to_status="Draft",
        triggered_by=current_user.user_id,
        comment=f"Case initialized for purpose: {request.purpose}",
    )

    return CaseResponse(**case_record)


@router.get("/cases", response_model=CaseListResponse, tags=["Cases"])
async def list_cases(
    status: Optional[str] = Query(None, description="Filter by case status"),
    claim_type: Optional[str] = Query(None, description="Filter by claim type"),
    priority: Optional[str] = Query(None, description="Filter by priority level"),
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    limit: int = Query(20, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CaseListResponse:
    """List verification cases scoped to the caller's role and organization memberships."""
    all_cases = list(_MOCK_CASES_DB.values())
    filtered: List[Dict[str, Any]] = []

    for case in all_cases:
        # 1. Role-based visibility check
        if current_user.is_reviewer() or current_user.is_auditor():
            # Reviewers, auditors, and sys admins can view all cases
            pass
        elif current_user.user_id == case["user_id"]:
            # User owns this case
            pass
        elif case.get("organization_id") and current_user.has_org_access(case["organization_id"]):
            # User belongs to case's organization
            pass
        else:
            # Not authorized to see this case in list
            continue

        # 2. Query filters
        if status and case["status"].lower() != status.lower():
            continue
        if claim_type and case["claim_type"].lower() != claim_type.lower():
            continue
        if priority and case["priority"].lower() != priority.lower():
            continue
        if organization_id and case.get("organization_id") != organization_id:
            continue

        filtered.append(case)

    # Sort descending by updated_at
    filtered.sort(key=lambda c: str(c["updated_at"]), reverse=True)
    total = len(filtered)
    page_items = filtered[offset : offset + limit]

    return CaseListResponse(
        cases=[CaseResponse(**c) for c in page_items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/cases/{case_id}", response_model=CaseDetailResponse, tags=["Cases"])
async def get_case(
    case_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CaseDetailResponse:
    """Retrieve full case details, timeline history, and permitted state transitions."""
    case = _MOCK_CASES_DB.get(case_id)
    if not case:
        raise NotFoundException(f"Verification case '{case_id}' not found")

    # Enforce strict cross-user and cross-org access boundaries
    enforce_case_access(
        case_id=case_id,
        case_owner_id=case["user_id"],
        case_org_id=case.get("organization_id"),
        user=current_user,
    )

    current_status = case["status"]
    allowed_transitions = VALID_TRANSITIONS.get(current_status, [])
    timeline_records = _MOCK_TIMELINE_DB.get(case_id, [])

    return CaseDetailResponse(
        **case,
        timeline=[CaseTimelineEvent(**t) for t in timeline_records],
        allowed_next_transitions=allowed_transitions,
    )


@router.post("/cases/{case_id}/submit", tags=["Cases"])
async def submit_case(
    case_id: str,
    request: CaseSubmitRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Submit a Draft or Action Required verification case for processing."""
    case = _MOCK_CASES_DB.get(case_id)
    if not case:
        raise NotFoundException(f"Verification case '{case_id}' not found")

    # Cross-user authorization check: only case owner or permitted org member can submit
    enforce_case_access(
        case_id=case_id,
        case_owner_id=case["user_id"],
        case_org_id=case.get("organization_id"),
        user=current_user,
    )

    current_status = case["status"]
    if current_status not in ("Draft", "Action Required"):
        raise InvalidStateTransitionException(
            f"Cannot submit case in status '{current_status}'. Allowed initial statuses: ['Draft', 'Action Required']"
        )

    now = datetime.now(timezone.utc)
    case["status"] = "Submitted"
    case["updated_at"] = now

    _record_timeline_event(
        case_id=case_id,
        from_status=current_status,
        to_status="Submitted",
        triggered_by=current_user.user_id,
        comment=f"Case submitted with idempotency key: {request.idempotency_key}",
    )

    return {
        "case_id": case_id,
        "status": "Submitted",
        "idempotency_key": request.idempotency_key,
        "submitted_at": now.isoformat(),
    }


@router.post("/cases/{case_id}/transition", response_model=CaseResponse, tags=["Cases"])
async def transition_case(
    case_id: str,
    request: CaseTransitionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CaseResponse:
    """Transition a verification case to a new status governed by the state machine."""
    case = _MOCK_CASES_DB.get(case_id)
    if not case:
        raise NotFoundException(f"Verification case '{case_id}' not found")

    current_status = case["status"]
    target_status = request.to_status

    # 1. State machine validation
    allowed_transitions = VALID_TRANSITIONS.get(current_status, [])
    if target_status not in allowed_transitions:
        raise InvalidStateTransitionException(
            f"Invalid transition from '{current_status}' to '{target_status}'. Allowed next transitions: {allowed_transitions}"
        )

    # 2. Role and privilege checks for transitions
    if target_status in ("Verified", "Rejected", "Action Required", "Restricted", "Under Review"):
        if not current_user.is_reviewer():
            raise PermissionDeniedException(
                f"User with role '{current_user.role}' is not authorized to transition cases to '{target_status}'. Requires ROLE_VERIFIER or ROLE_SYS_ADMIN."
            )
    elif target_status == "Submitted":
        enforce_case_access(
            case_id=case_id,
            case_owner_id=case["user_id"],
            case_org_id=case.get("organization_id"),
            user=current_user,
        )

    # 3. Apply state transition
    now = datetime.now(timezone.utc)
    case["status"] = target_status
    case["updated_at"] = now
    if target_status == "Verified":
        case["current_decision"] = "ALLOW"
    elif target_status == "Rejected":
        case["current_decision"] = "BLOCK"
    elif target_status == "Restricted":
        case["current_decision"] = "RESTRICT"

    _record_timeline_event(
        case_id=case_id,
        from_status=current_status,
        to_status=target_status,
        triggered_by=current_user.user_id,
        comment=request.comment or f"Status transitioned to {target_status}",
    )

    return CaseResponse(**case)


@router.post("/cases/{case_id}/assign", response_model=CaseResponse, tags=["Cases"])
async def assign_reviewer(
    case_id: str,
    request: CaseAssignRequest,
    current_user: AuthenticatedUser = Depends(require_reviewer_or_admin()),
) -> CaseResponse:
    """Assign or reassign a verification reviewer to a case. Restricted to reviewers and administrators."""
    case = _MOCK_CASES_DB.get(case_id)
    if not case:
        raise NotFoundException(f"Verification case '{case_id}' not found")

    current_status = case["status"]
    if current_status in ("Verified", "Rejected", "Cancelled"):
        raise InvalidStateTransitionException(
            f"Cannot assign reviewer to terminal case with status '{current_status}'"
        )

    now = datetime.now(timezone.utc)
    case["assigned_reviewer_id"] = request.reviewer_id
    case["updated_at"] = now

    _record_timeline_event(
        case_id=case_id,
        from_status=current_status,
        to_status=current_status,
        triggered_by=current_user.user_id,
        comment=f"Assigned reviewer to {request.reviewer_id}. {request.comment or ''}".strip(),
    )

    return CaseResponse(**case)

