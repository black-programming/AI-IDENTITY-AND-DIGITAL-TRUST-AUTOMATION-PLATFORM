"""Unit and Integration Tests for Phase 14 AI-Agent Identity Registry."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

MOCK_PEM_KEY_1 = (
    "-----BEGIN PUBLIC KEY-----\n"
    "MCowBQYDK2VwAyEAGb9f4n5e8z1k0v2m4q6w8e0r2t4y6u8i0o2p4a6s8d0=\n"
    "-----END PUBLIC KEY-----"
)

MOCK_PEM_KEY_2 = (
    "-----BEGIN PUBLIC KEY-----\n"
    "MCowBQYDK2VwAyEAXy8b2n9e1z3k5v7m9q1w3e5r7t9y1u3i5o7p9a1s3d5=\n"
    "-----END PUBLIC KEY-----"
)


# -----------------------------------------------------------------------------
# 1. Agent Registration & Conflict Tests
# -----------------------------------------------------------------------------
def test_register_agent_success(client: TestClient, subject_token: str):
    """Subject can register an AI Agent with version 1 manifest and public key fingerprint."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    payload = {
        "name": "Audit Verification Copilot",
        "agent_slug": "audit-copilot-v1",
        "description": "Assistant agent for automated evidence parsing and policy audit",
        "manifest": {
            "capabilities": ["extract:ocr", "read:evidence", "audit:read"],
            "model_provider": "google",
            "model_id": "gemini-1.5-flash",
            "runtime_environment": "CONTAINER",
            "system_prompt_hash": "sha256:112233445566778899aabbccddeeff00112233445566778899aabbccddeeff00",
            "change_summary": "Initial baseline manifest for audit copilot",
        },
        "public_key_pem": MOCK_PEM_KEY_1,
        "key_algorithm": "ED25519",
        "validity_days": 365,
    }

    res = client.post("/api/v1/agents", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()

    assert data["name"] == "Audit Verification Copilot"
    assert data["agent_slug"] == "audit-copilot-v1"
    assert data["status"] == "ACTIVE"
    assert data["is_active"] is True
    assert data["current_manifest_version"] == 1
    assert data["public_key_fingerprint"].startswith("SHA256:")
    assert data["current_manifest"]["capabilities"] == ["extract:ocr", "read:evidence", "audit:read"]
    assert data["current_manifest"]["model_provider"] == "google"
    assert data["current_manifest"]["model_id"] == "gemini-1.5-flash"


def get_error_message(res) -> str:
    body = res.json()
    if isinstance(body, dict):
        if "error" in body and isinstance(body["error"], dict):
            return body["error"].get("message", "")
        if "detail" in body:
            if isinstance(body["detail"], list):
                return " ".join(str(d.get("msg", "")) for d in body["detail"])
            return str(body["detail"])
    return str(body)


def test_register_agent_duplicate_slug_conflict(client: TestClient, subject_token: str):
    """Registering an agent with an already claimed slug returns HTTP 409 Conflict."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    payload = {
        "name": "Duplicate Agent",
        "agent_slug": "ocr-vision-pipeline-v1",  # Pre-seeded agent
        "manifest": {
            "capabilities": ["task:execute"],
            "model_provider": "openai",
            "model_id": "gpt-4o",
        },
    }

    res = client.post("/api/v1/agents", json=payload, headers=headers)
    assert res.status_code == 409
    assert "already exists" in get_error_message(res).lower()


def test_register_agent_invalid_capabilities_rejected(client: TestClient, subject_token: str):
    """Declaring unsupported capabilities is rejected with HTTP 422 Unprocessable Content."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    payload = {
        "name": "Malicious Agent",
        "agent_slug": "evil-agent-01",
        "manifest": {
            "capabilities": ["illegal:superuser_access", "read:evidence"],
            "model_provider": "google",
            "model_id": "gemini-1.5-pro",
        },
    }

    res = client.post("/api/v1/agents", json=payload, headers=headers)
    assert res.status_code == 422


# -----------------------------------------------------------------------------
# 2. Manifest Versioning Tests
# -----------------------------------------------------------------------------
def test_update_agent_manifest_versions_cleanly(client: TestClient, subject_token: str):
    """Publishing an updated manifest increments the version and preserves version history."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    # 1. Register agent
    create_payload = {
        "name": "Validation Engine Agent",
        "agent_slug": "val-engine-v1",
        "manifest": {
            "capabilities": ["validate:rules"],
            "model_provider": "self-hosted",
            "model_id": "rules-engine-1",
            "change_summary": "v1 initial release",
        },
    }
    create_res = client.post("/api/v1/agents", json=create_payload, headers=headers)
    agent_id = create_res.json()["id"]

    # 2. Update to v2
    update_payload = {
        "capabilities": ["validate:rules", "evaluate:policy"],
        "model_provider": "self-hosted",
        "model_id": "rules-engine-2-enhanced",
        "runtime_environment": "SERVERLESS",
        "change_summary": "v2: added policy evaluation capability",
    }
    update_res = client.put(f"/api/v1/agents/{agent_id}/manifest", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["current_manifest_version"] == 2
    assert updated_data["current_manifest"]["capabilities"] == ["validate:rules", "evaluate:policy"]
    assert updated_data["current_manifest"]["model_id"] == "rules-engine-2-enhanced"

    # 3. Retrieve manifest history
    history_res = client.get(f"/api/v1/agents/{agent_id}/manifests", headers=headers)
    assert history_res.status_code == 200
    manifests = history_res.json()
    assert len(manifests) == 2
    assert manifests[0]["manifest_version"] == 1
    assert manifests[1]["manifest_version"] == 2


# -----------------------------------------------------------------------------
# 3. Cryptographic Key Rotation Tests
# -----------------------------------------------------------------------------
def test_rotate_agent_key_updates_fingerprint(client: TestClient, subject_token: str):
    """Rotating an agent's public key recalculates the SHA-256 fingerprint."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    # Register with Key 1
    create_payload = {
        "name": "Signing Key Agent",
        "agent_slug": "signing-key-agent",
        "manifest": {
            "capabilities": ["task:execute"],
            "model_provider": "anthropic",
            "model_id": "claude-3-5-sonnet",
        },
        "public_key_pem": MOCK_PEM_KEY_1,
    }
    create_res = client.post("/api/v1/agents", json=create_payload, headers=headers)
    agent_id = create_res.json()["id"]
    fingerprint_1 = create_res.json()["public_key_fingerprint"]

    # Rotate to Key 2
    rotate_payload = {
        "public_key_pem": MOCK_PEM_KEY_2,
        "key_algorithm": "ED25519",
    }
    rotate_res = client.post(f"/api/v1/agents/{agent_id}/rotate-key", json=rotate_payload, headers=headers)
    assert rotate_res.status_code == 200
    fingerprint_2 = rotate_res.json()["public_key_fingerprint"]

    assert fingerprint_2 != fingerprint_1
    assert fingerprint_2.startswith("SHA256:")


# -----------------------------------------------------------------------------
# 4. Lifecycle: Suspend, Activate, Revocation Tests
# -----------------------------------------------------------------------------
def test_suspend_and_activate_agent(client: TestClient, subject_token: str):
    """Agent can be suspended temporarily and reactivated cleanly."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    # Register
    create_payload = {
        "name": "Togglable Agent",
        "agent_slug": "togglable-agent",
        "manifest": {"capabilities": ["task:execute"], "model_provider": "google", "model_id": "gemini-1.5-flash"},
    }
    create_res = client.post("/api/v1/agents", json=create_payload, headers=headers)
    agent_id = create_res.json()["id"]

    # Suspend
    suspend_res = client.post(f"/api/v1/agents/{agent_id}/suspend", headers=headers)
    assert suspend_res.status_code == 200
    assert suspend_res.json()["status"] == "SUSPENDED"
    assert suspend_res.json()["is_active"] is False

    # Activate
    activate_res = client.post(f"/api/v1/agents/{agent_id}/activate", headers=headers)
    assert activate_res.status_code == 200
    assert activate_res.json()["status"] == "ACTIVE"
    assert activate_res.json()["is_active"] is True


def test_agent_revocation_lifecycle(client: TestClient, subject_token: str):
    """Revoking an agent permanently terminates it and locks further mutations."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    create_payload = {
        "name": "Revocable Agent",
        "agent_slug": "revocable-agent",
        "manifest": {"capabilities": ["task:execute"], "model_provider": "google", "model_id": "gemini-1.5-flash"},
    }
    create_res = client.post("/api/v1/agents", json=create_payload, headers=headers)
    agent_id = create_res.json()["id"]

    # Revoke
    revoke_payload = {"reason": "Suspected key compromise during routine security scan"}
    revoke_res = client.post(f"/api/v1/agents/{agent_id}/revoke", json=revoke_payload, headers=headers)
    assert revoke_res.status_code == 200
    revoked_data = revoke_res.json()
    assert revoked_data["status"] == "REVOKED"
    assert revoked_data["is_active"] is False
    assert revoked_data["revocation_reason"] == "Suspected key compromise during routine security scan"
    assert revoked_data["revoked_at"] is not None

    # Duplicate revocation returns 409 Conflict
    dup_res = client.post(f"/api/v1/agents/{agent_id}/revoke", json=revoke_payload, headers=headers)
    assert dup_res.status_code == 409

    # Cannot update manifest of revoked agent
    update_res = client.put(
        f"/api/v1/agents/{agent_id}/manifest",
        json={"capabilities": ["task:execute"], "model_provider": "google", "model_id": "m1", "change_summary": "v2 fail"},
        headers=headers,
    )
    assert update_res.status_code == 422

    # Cannot rotate key of revoked agent
    rotate_res = client.post(
        f"/api/v1/agents/{agent_id}/rotate-key",
        json={"public_key_pem": MOCK_PEM_KEY_2},
        headers=headers,
    )
    assert rotate_res.status_code == 422

    # Cannot reactivate revoked agent
    reactivate_res = client.post(f"/api/v1/agents/{agent_id}/activate", headers=headers)
    assert reactivate_res.status_code == 422


# -----------------------------------------------------------------------------
# 5. Boundary Isolation & Authorization Tests
# -----------------------------------------------------------------------------
def test_agent_boundary_isolation_cross_user_blocked(
    client: TestClient, subject_token: str, subject_b_token: str
):
    """User B cannot view, modify, or revoke User A's private agent (HTTP 403 Forbidden)."""
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    headers_b = {"Authorization": f"Bearer {subject_b_token}"}

    create_payload = {
        "name": "Confidential Agent A",
        "agent_slug": "confidential-agent-a",
        "manifest": {"capabilities": ["audit:read"], "model_provider": "google", "model_id": "gemini-1.5-pro"},
    }
    create_res = client.post("/api/v1/agents", json=create_payload, headers=headers_a)
    agent_id = create_res.json()["id"]

    # User B cannot read
    get_res = client.get(f"/api/v1/agents/{agent_id}", headers=headers_b)
    assert get_res.status_code == 403

    # User B cannot update manifest
    update_res = client.put(
        f"/api/v1/agents/{agent_id}/manifest",
        json={"capabilities": ["audit:read"], "model_provider": "google", "model_id": "m2", "change_summary": "unauthorized edit"},
        headers=headers_b,
    )
    assert update_res.status_code == 403

    # User B cannot revoke
    revoke_res = client.post(
        f"/api/v1/agents/{agent_id}/revoke",
        json={"reason": "Attacker attempting unauthorized sabotage"},
        headers=headers_b,
    )
    assert revoke_res.status_code == 403


def test_auditor_and_verifier_can_inspect_agents(
    client: TestClient, auditor_token: str, verifier_token: str
):
    """Auditors and Verifiers have privileged read access to inspect active agent manifests."""
    headers_aud = {"Authorization": f"Bearer {auditor_token}"}
    headers_ver = {"Authorization": f"Bearer {verifier_token}"}

    # Auditor listing
    list_res = client.get("/api/v1/agents", headers=headers_aud)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 2

    # Verifier reading pre-seeded agent
    get_res = client.get("/api/v1/agents/agent-ocr-extractor-01", headers=headers_ver)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "OCR Vision Extraction Agent"


def test_unauthenticated_agent_access_rejected(client: TestClient):
    """Unauthenticated requests to agent endpoints are rejected with HTTP 401."""
    res_list = client.get("/api/v1/agents")
    assert res_list.status_code == 401

    res_post = client.post("/api/v1/agents", json={})
    assert res_post.status_code == 401
