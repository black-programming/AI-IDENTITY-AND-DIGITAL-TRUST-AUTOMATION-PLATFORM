"""Delegated Authorization Service.

Manages scoped capability delegation grants, audience validation, finite validity enforcement,
replay-prevention nonces, AI-agent status linkage, and tamper-evident audit logging.
"""

from datetime import datetime, timedelta, timezone
import hashlib
from typing import Any, Dict, List, Optional
import uuid
import jwt

from app.core.config import settings
from app.core.errors import ConflictException, NotFoundException, PermissionDeniedException, ValidationException
from app.core.security import AuthenticatedUser, ROLE_AUDITOR, ROLE_SYS_ADMIN, ROLE_VERIFIER
from app.schemas.delegation import (
    DelegationGrantCreateRequest,
    DelegationGrantResponse,
    DelegationVerifyRequest,
    DelegationVerifyResponse,
)
from app.services.agent_registry_service import _MOCK_AGENTS_DB
from app.services.audit_service import AuditService


def compute_token_fingerprint(token_str: str) -> str:
    """Generate SHA-256 fingerprint for a signed delegation token."""
    clean_bytes = token_str.strip().encode("utf-8")
    return f"SHA256:{hashlib.sha256(clean_bytes).hexdigest().upper()}"


def match_resource_pattern(permitted_pattern: str, requested_resource: str) -> bool:
    """Evaluate whether requested_resource matches permitted_pattern."""
    p = permitted_pattern.strip()
    r = requested_resource.strip()

    if p == "*" or p == r:
        return True

    if p.endswith(":*"):
        prefix = p[:-1]  # keep the colon, e.g. "case:"
        return r.startswith(prefix)

    if p.endswith("*"):
        prefix = p[:-1]
        return r.startswith(prefix)

    return False


# In-Memory Store for Delegation Grants
_MOCK_GRANTS_DB: Dict[str, Dict[str, Any]] = {
    "grant-copilot-01": {
        "id": "grant-copilot-01",
        "grantor_id": "user-org-admin-1",
        "grantee_id": "agent-ocr-extractor-01",
        "grantee_type": "AI_AGENT",
        "actions": ["extract:ocr", "read:evidence"],
        "resources": ["case:*", "evidence:*"],
        "audiences": ["https://api.trustplatform.internal"],
        "status": "ACTIVE",
        "delegation_token": "mock-token-grant-copilot-01",
        "token_fingerprint": "SHA256:1A2B3C4D5E6F7A8B9C0D1E2F3A4B5C6D7E8F9A0B1C2D3E4F5A6B7C8D9E0F1A2B",
        "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
        "revoked_at": None,
        "revoked_by": None,
        "revocation_reason": None,
        "created_at": datetime.now(timezone.utc) - timedelta(days=1),
    }
}

# In-Memory Store for Consumed Replay Nonces: nonce -> dict(grant_id, consumed_at, expires_at)
_MOCK_NONCES_DB: Dict[str, Dict[str, Any]] = {}


class DelegationService:
    """Core domain logic for Phase 15 Delegated Authorization."""

    @classmethod
    def _user_can_access_grant(cls, user: AuthenticatedUser, grant: Dict[str, Any]) -> bool:
        """Grantor, Grantee, or Platform Reviewer/Auditor/Admin can inspect grant."""
        if user.role in (ROLE_SYS_ADMIN, ROLE_AUDITOR, ROLE_VERIFIER):
            return True
        if grant["grantor_id"] == user.user_id:
            return True
        if grant["grantee_id"] == user.user_id:
            return True
        return False

    @classmethod
    def _user_can_manage_grant(cls, user: AuthenticatedUser, grant: Dict[str, Any]) -> bool:
        """Strictly Grantor or System Administrator can revoke grant."""
        if user.role == ROLE_SYS_ADMIN:
            return True
        return grant["grantor_id"] == user.user_id

    @classmethod
    def _build_response(cls, grant: Dict[str, Any]) -> DelegationGrantResponse:
        """Construct full DelegationGrantResponse evaluating dynamic time-based expiration."""
        now = datetime.now(timezone.utc)
        status = grant["status"]

        if status == "ACTIVE" and grant["expires_at"] < now:
            status = "EXPIRED"

        return DelegationGrantResponse(
            id=grant["id"],
            grantor_id=grant["grantor_id"],
            grantee_id=grant["grantee_id"],
            grantee_type=grant["grantee_type"],
            actions=grant["actions"],
            resources=grant["resources"],
            audiences=grant["audiences"],
            status=status,
            delegation_token=grant["delegation_token"],
            token_fingerprint=grant["token_fingerprint"],
            expires_at=grant["expires_at"],
            revoked_at=grant.get("revoked_at"),
            revoked_by=grant.get("revoked_by"),
            revocation_reason=grant.get("revocation_reason"),
            created_at=grant["created_at"],
            is_active=(status == "ACTIVE"),
        )

    @classmethod
    def create_grant(
        cls,
        request: DelegationGrantCreateRequest,
        caller: AuthenticatedUser,
    ) -> DelegationGrantResponse:
        """Create a scoped capability delegation grant and mint signed delegation token."""
        # 1. If grantee is an AI Agent, verify agent existence and active status
        if request.grantee_type == "AI_AGENT":
            # Search by agent id or slug
            agent = _MOCK_AGENTS_DB.get(request.grantee_id)
            if not agent:
                agent = next((a for a in _MOCK_AGENTS_DB.values() if a["agent_slug"] == request.grantee_id), None)
            if not agent:
                raise NotFoundException(f"AI Agent '{request.grantee_id}' not found in registry")
            if agent["status"] != "ACTIVE":
                raise ValidationException(f"Cannot delegate to inactive AI Agent (current status: '{agent['status']}')")

        now = datetime.now(timezone.utc)
        grant_id = f"grant-{uuid.uuid4()}"
        expires_at = now + timedelta(hours=request.validity_hours or 24)

        # 2. Mint Signed Delegation JWT
        jwt_payload = {
            "iss": getattr(settings, "SUPABASE_URL", "https://mock.supabase.co"),
            "sub": caller.user_id,
            "aud": request.audiences,
            "grant_id": grant_id,
            "grantee": request.grantee_id,
            "grantee_type": request.grantee_type,
            "actions": request.actions,
            "resources": request.resources,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        delegation_token = jwt.encode(
            jwt_payload,
            settings.SUPABASE_JWT_SECRET,
            algorithm="HS256",
        )
        token_fingerprint = compute_token_fingerprint(delegation_token)

        grant_dict = {
            "id": grant_id,
            "grantor_id": caller.user_id,
            "grantee_id": request.grantee_id,
            "grantee_type": request.grantee_type,
            "actions": request.actions,
            "resources": request.resources,
            "audiences": request.audiences,
            "status": "ACTIVE",
            "delegation_token": delegation_token,
            "token_fingerprint": token_fingerprint,
            "expires_at": expires_at,
            "revoked_at": None,
            "revoked_by": None,
            "revocation_reason": None,
            "created_at": now,
        }

        _MOCK_GRANTS_DB[grant_id] = grant_dict

        # 3. Audit trail
        AuditService.record_event(
            action_type="DELEGATION_GRANT_CREATED",
            target_resource=f"delegation/{grant_id}",
            actor_id=caller.user_id,
            actor_role=caller.role,
            metadata={
                "grant_id": grant_id,
                "grantee_id": request.grantee_id,
                "grantee_type": request.grantee_type,
                "actions": request.actions,
                "resources": request.resources,
                "audiences": request.audiences,
                "expires_at": expires_at.isoformat(),
            },
        )

        return cls._build_response(grant_dict)

    @classmethod
    def get_grant(cls, grant_id: str, caller: AuthenticatedUser) -> DelegationGrantResponse:
        """Inspect a capability delegation grant."""
        grant = _MOCK_GRANTS_DB.get(grant_id)
        if not grant:
            raise NotFoundException(f"Delegation grant '{grant_id}' not found")

        if not cls._user_can_access_grant(caller, grant):
            raise PermissionDeniedException(f"Access to delegation grant '{grant_id}' denied")

        return cls._build_response(grant)

    @classmethod
    def list_grants(
        cls,
        caller: AuthenticatedUser,
        role_type: Optional[str] = "all",
    ) -> List[DelegationGrantResponse]:
        """List grants visible to caller (as grantor, grantee, or auditor)."""
        results: List[DelegationGrantResponse] = []
        for grant in _MOCK_GRANTS_DB.values():
            if not cls._user_can_access_grant(caller, grant):
                continue

            if role_type == "grantor" and grant["grantor_id"] != caller.user_id:
                continue
            if role_type == "grantee" and grant["grantee_id"] != caller.user_id:
                continue

            results.append(cls._build_response(grant))

        return sorted(results, key=lambda g: g.created_at, reverse=True)

    @classmethod
    def revoke_grant(
        cls,
        grant_id: str,
        reason: str,
        caller: AuthenticatedUser,
    ) -> DelegationGrantResponse:
        """Revoke an active delegation grant immediately."""
        grant = _MOCK_GRANTS_DB.get(grant_id)
        if not grant:
            raise NotFoundException(f"Delegation grant '{grant_id}' not found")

        if not cls._user_can_manage_grant(caller, grant):
            raise PermissionDeniedException("Only the grantor or system administrator can revoke this delegation grant")

        if grant["status"] == "REVOKED":
            raise ConflictException(f"Delegation grant '{grant_id}' is already revoked")

        now = datetime.now(timezone.utc)
        grant["status"] = "REVOKED"
        grant["revoked_at"] = now
        grant["revoked_by"] = caller.user_id
        grant["revocation_reason"] = reason

        AuditService.record_event(
            action_type="DELEGATION_GRANT_REVOKED",
            target_resource=f"delegation/{grant_id}",
            actor_id=caller.user_id,
            actor_role=caller.role,
            metadata={
                "grant_id": grant_id,
                "reason": reason,
                "revoked_by": caller.user_id,
            },
        )

        return cls._build_response(grant)

    @classmethod
    def verify_delegated_request(cls, request: DelegationVerifyRequest) -> DelegationVerifyResponse:
        """Evaluate an in-flight delegated capability request against scopes, expiry, replay, and agent status."""
        now = datetime.now(timezone.utc)
        token_str = request.delegation_token.strip()

        # 1. Find Grant by token or grant_id
        grant = None
        # Check direct grant_id
        if token_str in _MOCK_GRANTS_DB:
            grant = _MOCK_GRANTS_DB[token_str]
        else:
            # Check by token string
            for g in _MOCK_GRANTS_DB.values():
                if g["delegation_token"] == token_str:
                    grant = g
                    break

        # Decode token if not found in mock cache
        decoded_payload = {}
        if not grant:
            try:
                decoded_payload = jwt.decode(
                    token_str,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    options={"verify_aud": False},
                )
                g_id = decoded_payload.get("grant_id")
                if g_id and g_id in _MOCK_GRANTS_DB:
                    grant = _MOCK_GRANTS_DB[g_id]
                else:
                    grant = {
                        "id": g_id or "grant-decoded",
                        "grantor_id": decoded_payload.get("sub"),
                        "grantee_id": decoded_payload.get("grantee"),
                        "grantee_type": decoded_payload.get("grantee_type", "AI_AGENT"),
                        "actions": decoded_payload.get("actions", []),
                        "resources": decoded_payload.get("resources", []),
                        "audiences": decoded_payload.get("aud", []),
                        "status": "ACTIVE",
                        "expires_at": datetime.fromtimestamp(decoded_payload.get("exp", 0), timezone.utc),
                    }
            except Exception as e:
                AuditService.record_event(
                    action_type="DELEGATION_EVALUATED",
                    target_resource=request.requested_resource,
                    outcome="DENIED",
                    metadata={"reason": "INVALID_TOKEN", "error": str(e)},
                )
                return DelegationVerifyResponse(
                    is_valid=False,
                    decision="DENIED",
                    reason_code="INVALID_TOKEN",
                    message=f"Cryptographic delegation token invalid or corrupt: {str(e)}",
                )

        grant_id = grant.get("id", "unknown")
        grantor_id = grant.get("grantor_id")
        grantee_id = grant.get("grantee_id")
        grantee_type = grant.get("grantee_type", "AI_AGENT")
        actions = grant.get("actions", [])
        resources = grant.get("resources", [])
        audiences = grant.get("audiences", [])
        expires_at = grant.get("expires_at")
        status = grant.get("status", "ACTIVE")

        def deny(code: str, msg: str) -> DelegationVerifyResponse:
            AuditService.record_event(
                action_type="DELEGATION_EVALUATED",
                target_resource=request.requested_resource,
                actor_id=grantee_id,
                outcome="DENIED",
                metadata={
                    "grant_id": grant_id,
                    "grantor_id": grantor_id,
                    "grantee_id": grantee_id,
                    "requested_action": request.requested_action,
                    "reason_code": code,
                },
            )
            return DelegationVerifyResponse(
                is_valid=False,
                decision="DENIED",
                reason_code=code,
                grantor_id=grantor_id,
                grantee_id=grantee_id,
                grantee_type=grantee_type,
                granted_actions=actions,
                granted_resources=resources,
                expires_at=expires_at,
                message=msg,
            )

        # 2. Status & Revocation Check
        if status == "REVOKED":
            return deny("GRANT_REVOKED", f"Delegation grant '{grant_id}' has been formally revoked.")

        # 3. Time Expiration Check
        if expires_at and expires_at < now:
            return deny("GRANT_EXPIRED", f"Delegation grant '{grant_id}' expired at {expires_at.isoformat()}.")

        # 4. Audience Validation
        if audiences:
            req_aud = request.audience.strip()
            if req_aud not in audiences and "*" not in audiences:
                return deny(
                    "AUDIENCE_MISMATCH",
                    f"Requested audience '{req_aud}' does not match permitted audiences: {audiences}",
                )

        # 5. Action Scope Check
        if request.requested_action not in actions and "*" not in actions:
            return deny(
                "ACTION_OUT_OF_SCOPE",
                f"Action '{request.requested_action}' is not permitted by grant. Granted actions: {actions}",
            )

        # 6. Resource Scope Check
        resource_matched = any(match_resource_pattern(pattern, request.requested_resource) for pattern in resources)
        if not resource_matched:
            return deny(
                "RESOURCE_OUT_OF_SCOPE",
                f"Target resource '{request.requested_resource}' does not match permitted resource patterns: {resources}",
            )

        # 7. Replay Protection: Nonce Validation
        if request.nonce:
            nonce_key = request.nonce.strip()
            if nonce_key in _MOCK_NONCES_DB:
                return deny(
                    "NONCE_ALREADY_USED",
                    f"Replay attack detected: cryptographic nonce '{nonce_key}' was already consumed.",
                )
            _MOCK_NONCES_DB[nonce_key] = {
                "grant_id": grant_id,
                "consumed_at": now,
                "expires_at": expires_at,
            }

        # 8. Grantee AI-Agent Lifecycle Linkage (Phase 14)
        if grantee_type == "AI_AGENT" and grantee_id:
            agent = _MOCK_AGENTS_DB.get(grantee_id)
            if not agent:
                agent = next((a for a in _MOCK_AGENTS_DB.values() if a["agent_slug"] == grantee_id), None)
            if agent and agent["status"] != "ACTIVE":
                return deny(
                    "GRANTEE_AGENT_INACTIVE",
                    f"Delegated AI Agent '{grantee_id}' is not in ACTIVE state (current status: '{agent['status']}').",
                )

        # 9. All Constraints Verified: ALLOW
        AuditService.record_event(
            action_type="DELEGATION_EVALUATED",
            target_resource=request.requested_resource,
            actor_id=grantee_id,
            outcome="ALLOW",
            metadata={
                "grant_id": grant_id,
                "grantor_id": grantor_id,
                "grantee_id": grantee_id,
                "action": request.requested_action,
                "decision": "ALLOW",
            },
        )

        return DelegationVerifyResponse(
            is_valid=True,
            decision="ALLOW",
            reason_code="AUTHORIZED",
            grantor_id=grantor_id,
            grantee_id=grantee_id,
            grantee_type=grantee_type,
            granted_actions=actions,
            granted_resources=resources,
            expires_at=expires_at,
            message="Delegated capability verified successfully within granted scope.",
        )
