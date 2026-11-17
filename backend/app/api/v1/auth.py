"""Authentication and session inspection endpoints."""

import time
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import AuthenticatedUser, decode_jwt_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserProfileResponse(BaseModel):
    user_id: str = Field(..., description="Unique subject ID from Supabase Auth")
    email: Optional[str] = Field(None, description="Email address associated with the account")
    role: str = Field(..., description="Assigned platform RBAC role")
    raw_claims: Dict[str, Any] = Field(default_factory=dict, description="Validated JWT token claims")


class SessionStatusResponse(BaseModel):
    active: bool = Field(..., description="Whether the authentication session is active and valid")
    user_id: str = Field(..., description="Subject ID")
    role: str = Field(..., description="User role")
    expires_at: Optional[int] = Field(None, description="Unix timestamp when token expires")
    seconds_remaining: Optional[int] = Field(None, description="Remaining seconds until token expiry")


class TokenVerificationRequest(BaseModel):
    token: str = Field(..., description="Supabase JWT access token to verify")


class TokenVerificationResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    error: Optional[str] = None


@router.get("/me", response_model=UserProfileResponse, summary="Get current authenticated user profile")
async def get_me(user: AuthenticatedUser = Depends(get_current_user)):
    """Returns the verified profile and claims of the current authenticated user."""
    return UserProfileResponse(
        user_id=user.user_id,
        email=user.email,
        role=user.role,
        raw_claims=user.raw_claims,
    )


@router.get("/session", response_model=SessionStatusResponse, summary="Inspect current session validity and expiry")
async def get_session(user: AuthenticatedUser = Depends(get_current_user)):
    """Inspects the active Bearer token and returns remaining session validity."""
    exp = user.raw_claims.get("exp")
    seconds_left = None
    if exp:
        seconds_left = max(0, int(exp - time.time()))

    return SessionStatusResponse(
        active=True,
        user_id=user.user_id,
        role=user.role,
        expires_at=exp,
        seconds_remaining=seconds_left,
    )


@router.post("/verify-token", response_model=TokenVerificationResponse, summary="Verify access token validity")
async def verify_token(request: TokenVerificationRequest):
    """Verifies a JWT token signature, expiration, and audience without leaking secrets."""
    try:
        claims = decode_jwt_token(request.token)
        app_meta = claims.get("app_metadata", {})
        return TokenVerificationResponse(
            valid=True,
            user_id=claims.get("sub"),
            email=claims.get("email"),
            role=app_meta.get("role", "ROLE_SUBJECT"),
        )
    except Exception as e:
        return TokenVerificationResponse(
            valid=False,
            error=str(e),
        )
