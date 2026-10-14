"""Security utilities, token decoding, and role-based dependencies."""

from typing import Any, Dict, List, Optional
import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings
from app.core.errors import AuthenticationException, PermissionDeniedException

bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    user_id: str
    email: Optional[str] = None
    role: str = "ROLE_SUBJECT"
    raw_claims: Dict[str, Any] = {}


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """Decode and validate a Supabase JWT token using configured secret or fallback."""
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
    role = app_meta.get("role", "ROLE_SUBJECT")
    email = payload.get("email")

    return AuthenticatedUser(
        user_id=user_id,
        email=email,
        role=role,
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
