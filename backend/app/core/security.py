"""Security utilities, token decoding, and role-based dependencies."""

from typing import Any, Dict, List, Optional
import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.errors import AuthenticationException, PermissionDeniedException

bearer_scheme = HTTPBearer(auto_error=False)

# Platform RBAC Roles
ROLE_SUBJECT = "ROLE_SUBJECT"
ROLE_VERIFIER = "ROLE_VERIFIER"
ROLE_ORG_MEMBER = "ROLE_ORG_MEMBER"
ROLE_ORG_ADMIN = "ROLE_ORG_ADMIN"
ROLE_SYS_ADMIN = "ROLE_SYS_ADMIN"
ROLE_AUDITOR = "ROLE_AUDITOR"

ALL_ROLES = {
    ROLE_SUBJECT,
    ROLE_VERIFIER,
    ROLE_ORG_MEMBER,
    ROLE_ORG_ADMIN,
    ROLE_SYS_ADMIN,
    ROLE_AUDITOR,
}


class AuthenticatedUser(BaseModel):
    user_id: str = Field(..., description="Subject unique identifier (UUID)")
    email: Optional[str] = Field(None, description="Account email address")
    role: str = Field(ROLE_SUBJECT, description="Platform RBAC role")
    organization_ids: List[str] = Field(default_factory=list, description="IDs of organizations user belongs to")
    raw_claims: Dict[str, Any] = Field(default_factory=dict, description="Raw JWT token payload")

    def is_admin(self) -> bool:
        return self.role == ROLE_SYS_ADMIN

    def is_reviewer(self) -> bool:
        return self.role in (ROLE_VERIFIER, ROLE_SYS_ADMIN)

    def is_auditor(self) -> bool:
        return self.role in (ROLE_AUDITOR, ROLE_SYS_ADMIN)

    def has_org_access(self, org_id: str) -> bool:
        if self.role == ROLE_SYS_ADMIN:
            return True
        return org_id in self.organization_ids or self.raw_claims.get("organization_id") == org_id


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """Decode and validate a Supabase JWT token using configured secret."""
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_signature": True, "verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Access token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationException(f"Invalid token: {str(e)}")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> AuthenticatedUser:
    """Dependency extracting the authenticated user from the Bearer token."""
    if not credentials or not credentials.credentials:
        raise AuthenticationException("Authorization header with Bearer token is required")

    payload = decode_jwt_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Token payload missing 'sub' subject claim")

    # Extract role from app_metadata or custom claims
    app_meta = payload.get("app_metadata", {})
    role = app_meta.get("role", ROLE_SUBJECT)
    email = payload.get("email")

    # Extract organization memberships
    org_ids = app_meta.get("organization_ids", [])
    if not org_ids and app_meta.get("organization_id"):
        org_ids = [app_meta.get("organization_id")]
    if not org_ids and payload.get("organization_id"):
        org_ids = [payload.get("organization_id")]

    return AuthenticatedUser(
        user_id=user_id,
        email=email,
        role=role,
        organization_ids=org_ids,
        raw_claims=payload,
    )


def require_role(allowed_roles: List[str]):
    """Role-based access control dependency factory."""

    async def role_checker(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if user.role not in allowed_roles:
            raise PermissionDeniedException(
                f"User role '{user.role}' is not authorized. Required: {allowed_roles}"
            )
        return user

    return role_checker


def require_any_role(*roles: str):
    """Shortcut for requiring any of the specified roles."""
    return require_role(list(roles))


def require_sys_admin():
    """Requires ROLE_SYS_ADMIN privilege."""
    return require_role([ROLE_SYS_ADMIN])


def require_reviewer_or_admin():
    """Requires ROLE_VERIFIER or ROLE_SYS_ADMIN."""
    return require_role([ROLE_VERIFIER, ROLE_SYS_ADMIN])


def require_auditor_or_admin():
    """Requires ROLE_AUDITOR or ROLE_SYS_ADMIN."""
    return require_role([ROLE_AUDITOR, ROLE_SYS_ADMIN])


def enforce_case_access(
    case_id: str,
    case_owner_id: str,
    case_org_id: Optional[str],
    user: AuthenticatedUser,
) -> None:
    """Verifies caller is authorized to view or modify a verification case."""
    # Reviewers, auditors, and system admins have global case inspection privileges
    if user.is_reviewer() or user.is_auditor():
        return

    # Owner can access their own case
    if user.user_id == case_owner_id:
        return

    # Organization member can access case belonging to their organization
    if case_org_id and user.has_org_access(case_org_id):
        return

    raise PermissionDeniedException(
        f"Cross-user access denied: user '{user.user_id}' is not authorized to access case '{case_id}'"
    )
