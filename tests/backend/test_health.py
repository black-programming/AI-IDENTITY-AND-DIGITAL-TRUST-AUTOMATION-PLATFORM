"""Test health check endpoint."""

from fastapi.testclient import TestClient


def test_health_check_returns_200(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "environment" in data
    assert "timestamp" in data
