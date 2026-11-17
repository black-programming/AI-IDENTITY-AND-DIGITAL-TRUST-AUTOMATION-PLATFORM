"""Tests for Phase 4 authentication endpoints and session inspection."""

import pytest
from fastapi.testclient import TestClient


def test_get_me_unauthenticated(client: TestClient):
    """Calling /api/v1/auth/me without a token must fail with 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_with_valid_subject_token(client: TestClient, subject_token: str):
    """Calling /api/v1/auth/me with subject token must return user profile and role."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "a0000000-0000-0000-0000-000000000001"
    assert data["email"] == "test.citizen@example.com"
    assert data["role"] == "ROLE_SUBJECT"
    assert "raw_claims" in data


def test_get_me_with_verifier_token(client: TestClient, verifier_token: str):
    """Calling /api/v1/auth/me with verifier token must return ROLE_VERIFIER."""
    headers = {"Authorization": f"Bearer {verifier_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "a0000000-0000-0000-0000-000000000001"
    assert data["email"] == "verifier@compliance.org"
    assert data["role"] == "ROLE_VERIFIER"


def test_session_inspection(client: TestClient, subject_token: str):
    """Calling /api/v1/auth/session must return active session status and remaining seconds."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    response = client.get("/api/v1/auth/session", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["active"] is True
    assert data["user_id"] == "a0000000-0000-0000-0000-000000000001"
    assert data["seconds_remaining"] is not None
    assert data["seconds_remaining"] > 0


def test_verify_token_valid(client: TestClient, admin_token: str):
    """Calling /api/v1/auth/verify-token with valid token must succeed."""
    response = client.post("/api/v1/auth/verify-token", json={"token": admin_token})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["user_id"] == "a0000000-0000-0000-0000-000000000001"
    assert data["email"] == "admin@platform.org"
    assert data["role"] == "ROLE_SYS_ADMIN"


def test_verify_token_expired(client: TestClient, expired_token: str):
    """Calling /api/v1/auth/verify-token with expired token must return valid=False."""
    response = client.post("/api/v1/auth/verify-token", json={"token": expired_token})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "expired" in data["error"].lower()


def test_verify_token_tampered(client: TestClient):
    """Calling /api/v1/auth/verify-token with garbage token must return valid=False."""
    response = client.post("/api/v1/auth/verify-token", json={"token": "invalid.jwt.token"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["error"] is not None
