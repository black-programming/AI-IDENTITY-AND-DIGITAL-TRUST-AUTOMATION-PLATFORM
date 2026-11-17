"""Pytest configuration and fixtures for backend testing."""

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import jwt
import pytest
from fastapi.testclient import TestClient

# Add backend to sys.path so 'app' can be resolved
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, headers={"x-bypass-rate-limit": "test-bypass-secret-phase17"})


@pytest.fixture
def rate_limited_client() -> TestClient:
    """Client without bypass headers to verify rate limiting and abuse controls."""
    return TestClient(app)


def create_mock_jwt(
    user_id: str = "a0000000-0000-0000-0000-000000000001",
    role: str = "ROLE_SUBJECT",
    email: str = "test.citizen@example.com",
    organization_ids: Optional[List[str]] = None,
    expires_in_seconds: int = 3600,
) -> str:
    """Helper to generate signed mock JWT tokens for test cases."""
    now = datetime.now(timezone.utc)
    app_metadata = {"role": role}
    if organization_ids:
        app_metadata["organization_ids"] = organization_ids

    payload = {
        "sub": user_id,
        "email": email,
        "app_metadata": app_metadata,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in_seconds)).timestamp()),
        "iss": settings.SUPABASE_URL,
        "aud": "authenticated",
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def subject_token() -> str:
    return create_mock_jwt(role="ROLE_SUBJECT")


@pytest.fixture
def subject_b_token() -> str:
    return create_mock_jwt(
        user_id="user-b-attacker-777",
        email="citizen.b@example.com",
        role="ROLE_SUBJECT",
    )


@pytest.fixture
def verifier_token() -> str:
    return create_mock_jwt(role="ROLE_VERIFIER", email="verifier@compliance.org")


@pytest.fixture
def admin_token() -> str:
    return create_mock_jwt(role="ROLE_SYS_ADMIN", email="admin@platform.org")


@pytest.fixture
def org_admin_token() -> str:
    return create_mock_jwt(
        user_id="user-acme-admin",
        role="ROLE_ORG_ADMIN",
        email="admin@acme.org",
        organization_ids=["org-acme-111"],
    )


@pytest.fixture
def org_member_token() -> str:
    return create_mock_jwt(
        user_id="user-acme-member",
        role="ROLE_ORG_MEMBER",
        email="employee@acme.org",
        organization_ids=["org-acme-111"],
    )


@pytest.fixture
def org_b_member_token() -> str:
    return create_mock_jwt(
        user_id="user-globex-admin",
        role="ROLE_ORG_ADMIN",
        email="admin@globex.com",
        organization_ids=["org-globex-222"],
    )


@pytest.fixture
def expired_token() -> str:
    return create_mock_jwt(role="ROLE_SUBJECT", expires_in_seconds=-3600)


@pytest.fixture
def auditor_token() -> str:
    return create_mock_jwt(role="ROLE_AUDITOR", email="auditor@governance.org")
