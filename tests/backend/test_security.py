"""Security, authentication, and authorization tests."""

from fastapi.testclient import TestClient


def test_unauthenticated_request_rejected(client: TestClient):
    """Calling protected endpoint without token must return 401."""
    response = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"})
    assert response.status_code == 401
    assert "detail" in response.json() or "error" in response.json()


def test_expired_token_rejected(client: TestClient, expired_token: str):
    """Calling with expired JWT must return 401."""
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    assert response.status_code == 401


def test_subject_cannot_access_reviewer_queue(client: TestClient, subject_token: str):
    """ROLE_SUBJECT must be blocked with 403 when trying to access reviewer queue."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    response = client.get("/api/v1/review/queue", headers=headers)
    assert response.status_code == 403


def test_verifier_can_access_reviewer_queue(client: TestClient, verifier_token: str):
    """ROLE_VERIFIER must be allowed to access reviewer queue."""
    headers = {"Authorization": f"Bearer {verifier_token}"}
    response = client.get("/api/v1/review/queue", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "pending_cases" in data


def test_admin_can_access_reviewer_queue(client: TestClient, admin_token: str):
    """ROLE_SYS_ADMIN must be allowed to access reviewer queue."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/review/queue", headers=headers)
    assert response.status_code == 200


def test_zero_secret_leakage_in_openapi_docs(client: TestClient):
    """OpenAPI schema must never expose server-only secret keys."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema_str = response.text.lower()
    assert "service_role" not in schema_str
    assert "super-secret-jwt" not in schema_str
