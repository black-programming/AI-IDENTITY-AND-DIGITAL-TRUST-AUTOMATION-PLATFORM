"""Unit and Integration Tests for Phase 15 Delegated Authorization."""

from datetime import datetime, timezone
import uuid
import pytest
from fastapi.testclient import TestClient

from app.services.agent_registry_service import _MOCK_AGENTS_DB


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


# -----------------------------------------------------------------------------
# 1. Grant Creation & Agent Status Validation
# -----------------------------------------------------------------------------
def test_create_delegation_grant_success(client: TestClient, subject_token: str):
    """Subject can delegate scoped capabilities to an active AI Agent with a signed token."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    payload = {
        "grantee_id": "agent-ocr-extractor-01",
        "grantee_type": "AI_AGENT",
        "actions": ["extract:ocr", "read:evidence"],
        "resources": ["case:*", "evidence:*"],
        "audiences": ["https://api.trustplatform.internal"],
        "validity_hours": 48,
        "notes": "Delegated OCR parsing authority for ongoing cases",
    }

    res = client.post("/api/v1/delegation/grants", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()

    assert data["grantee_id"] == "agent-ocr-extractor-01"
    assert data["grantee_type"] == "AI_AGENT"
    assert data["actions"] == ["extract:ocr", "read:evidence"]
    assert data["resources"] == ["case:*", "evidence:*"]
    assert data["audiences"] == ["https://api.trustplatform.internal"]
    assert data["status"] == "ACTIVE"
    assert data["is_active"] is True
    assert data["delegation_token"] is not None
    assert data["token_fingerprint"].startswith("SHA256:")


def test_create_delegation_to_inactive_agent_rejected(client: TestClient, subject_token: str):
    """Attempting to delegate authority to a suspended or revoked AI Agent returns HTTP 422."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    # Register temporary agent and revoke it
    agent_slug = f"temp-agent-{uuid.uuid4().hex[:6]}"
    reg_res = client.post(
        "/api/v1/agents",
        json={
            "name": "Temporary Suspended Agent",
            "agent_slug": agent_slug,
            "manifest": {"capabilities": ["task:execute"], "model_provider": "google", "model_id": "gemini-1.5-flash"},
        },
        headers=headers,
    )
    temp_agent_id = reg_res.json()["id"]

    # Revoke the agent
    client.post(f"/api/v1/agents/{temp_agent_id}/revoke", json={"reason": "Testing inactive delegation block"}, headers=headers)

    # Attempt to delegate to revoked agent
    payload = {
        "grantee_id": temp_agent_id,
        "grantee_type": "AI_AGENT",
        "actions": ["task:execute"],
        "resources": ["case:*"],
        "audiences": ["https://api.trustplatform.internal"],
    }
    res = client.post("/api/v1/delegation/grants", json=payload, headers=headers)
    assert res.status_code == 422
    assert "inactive" in get_error_message(res).lower()


# -----------------------------------------------------------------------------
# 2. In-Flight Capability Evaluation & Scope Matching
# -----------------------------------------------------------------------------
def test_verify_delegated_capability_allow_happy_path(client: TestClient, subject_token: str):
    """In-flight request with valid scope, matching audience, and fresh nonce evaluates to ALLOW."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    # Create grant
    grant_payload = {
        "grantee_id": "agent-ocr-extractor-01",
        "grantee_type": "AI_AGENT",
        "actions": ["read:evidence"],
        "resources": ["case:*", "evidence:ev-999"],
        "audiences": ["https://api.trustplatform.internal"],
        "validity_hours": 12,
    }
    grant_res = client.post("/api/v1/delegation/grants", json=grant_payload, headers=headers)
    token = grant_res.json()["delegation_token"]

    # Verify request
    verify_payload = {
        "delegation_token": token,
        "requested_action": "read:evidence",
        "requested_resource": "case:case-8888",
        "audience": "https://api.trustplatform.internal",
        "nonce": f"nonce-{uuid.uuid4().hex}",
    }
    verify_res = client.post("/api/v1/delegation/verify", json=verify_payload)
    assert verify_res.status_code == 200
    data = verify_res.json()

    assert data["decision"] == "ALLOW"
    assert data["is_valid"] is True
    assert data["reason_code"] == "AUTHORIZED"


def test_verify_delegated_capability_action_out_of_scope_denied(client: TestClient, subject_token: str):
    """Requesting an action not granted returns DENIED with ACTION_OUT_OF_SCOPE."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    grant_payload = {
        "grantee_id": "agent-ocr-extractor-01",
        "grantee_type": "AI_AGENT",
        "actions": ["read:evidence"],  # Only read:evidence
        "resources": ["case:*"],
        "audiences": ["https://api.trustplatform.internal"],
    }
    grant_res = client.post("/api/v1/delegation/grants", json=grant_payload, headers=headers)
    token = grant_res.json()["delegation_token"]

    verify_payload = {
        "delegation_token": token,
        "requested_action": "write:evidence",  # Out of scope action
        "requested_resource": "case:case-123",
        "audience": "https://api.trustplatform.internal",
    }
    verify_res = client.post("/api/v1/delegation/verify", json=verify_payload)
    assert verify_res.status_code == 200
    data = verify_res.json()

    assert data["decision"] == "DENIED"
    assert data["is_valid"] is False
    assert data["reason_code"] == "ACTION_OUT_OF_SCOPE"


def test_verify_delegated_capability_resource_out_of_scope_denied(client: TestClient, subject_token: str):
    """Requesting a resource outside granted resource patterns returns DENIED with RESOURCE_OUT_OF_SCOPE."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    grant_payload = {
        "grantee_id": "agent-ocr-extractor-01",
        "grantee_type": "AI_AGENT",
        "actions": ["read:evidence"],
        "resources": ["case:specific-123"],  # Specific resource only
        "audiences": ["https://api.trustplatform.internal"],
    }
    grant_res = client.post("/api/v1/delegation/grants", json=grant_payload, headers=headers)
    token = grant_res.json()["delegation_token"]

    verify_payload = {
        "delegation_token": token,
        "requested_action": "read:evidence",
        "requested_resource": "case:different-456",  # Different resource
        "audience": "https://api.trustplatform.internal",
    }
    verify_res = client.post("/api/v1/delegation/verify", json=verify_payload)
    assert verify_res.status_code == 200
    data = verify_res.json()

    assert data["decision"] == "DENIED"
    assert data["is_valid"] is False
    assert data["reason_code"] == "RESOURCE_OUT_OF_SCOPE"


def test_verify_delegated_capability_audience_mismatch_denied(client: TestClient, subject_token: str):
    """Requesting an unapproved service audience returns DENIED with AUDIENCE_MISMATCH."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    grant_payload = {
        "grantee_id": "agent-ocr-extractor-01",
        "grantee_type": "AI_AGENT",
        "actions": ["read:evidence"],
        "resources": ["case:*"],
        "audiences": ["https://api.trustplatform.internal"],
    }
    grant_res = client.post("/api/v1/delegation/grants", json=grant_payload, headers=headers)
    token = grant_res.json()["delegation_token"]

    verify_payload = {
        "delegation_token": token,
        "requested_action": "read:evidence",
        "requested_resource": "case:case-123",
        "audience": "https://unauthorized-external-verifier.org",
    }
    verify_res = client.post("/api/v1/delegation/verify", json=verify_payload)
    assert verify_res.status_code == 200
    data = verify_res.json()

    assert data["decision"] == "DENIED"
    assert data["is_valid"] is False
    assert data["reason_code"] == "AUDIENCE_MISMATCH"


# -----------------------------------------------------------------------------
# 3. Replay Protection: Nonce Validation
# -----------------------------------------------------------------------------
def test_verify_delegated_capability_replay_attack_denied(client: TestClient, subject_token: str):
    """Presenting an already consumed nonce is blocked as a replay attack (NONCE_ALREADY_USED)."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    grant_payload = {
        "grantee_id": "agent-ocr-extractor-01",
        "grantee_type": "AI_AGENT",
        "actions": ["read:evidence"],
        "resources": ["case:*"],
        "audiences": ["https://api.trustplatform.internal"],
    }
    grant_res = client.post("/api/v1/delegation/grants", json=grant_payload, headers=headers)
    token = grant_res.json()["delegation_token"]
    nonce = f"one-time-nonce-{uuid.uuid4().hex}"

    verify_payload = {
        "delegation_token": token,
        "requested_action": "read:evidence",
        "requested_resource": "case:case-replay",
        "audience": "https://api.trustplatform.internal",
        "nonce": nonce,
    }

    # First consumption succeeds
    first_res = client.post("/api/v1/delegation/verify", json=verify_payload)
    assert first_res.status_code == 200
    assert first_res.json()["decision"] == "ALLOW"

    # Replay attempt fails
    replay_res = client.post("/api/v1/delegation/verify", json=verify_payload)
    assert replay_res.status_code == 200
    data = replay_res.json()
    assert data["decision"] == "DENIED"
    assert data["reason_code"] == "NONCE_ALREADY_USED"


# -----------------------------------------------------------------------------
# 4. Revocation & Linkage to Phase 14 AI Agent State
# -----------------------------------------------------------------------------
def test_revoke_delegation_grant_and_verify_denied(client: TestClient, subject_token: str):
    """Grantor can revoke a capability grant; subsequent verification evaluates to GRANT_REVOKED."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    grant_payload = {
        "grantee_id": "agent-ocr-extractor-01",
        "grantee_type": "AI_AGENT",
        "actions": ["read:evidence"],
        "resources": ["case:*"],
        "audiences": ["https://api.trustplatform.internal"],
    }
    grant_res = client.post("/api/v1/delegation/grants", json=grant_payload, headers=headers)
    grant_id = grant_res.json()["id"]
    token = grant_res.json()["delegation_token"]

    # Revoke grant
    revoke_res = client.post(
        f"/api/v1/delegation/grants/{grant_id}/revoke",
        json={"reason": "Grantor withdrawing delegation permission"},
        headers=headers,
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "REVOKED"
    assert revoke_res.json()["revocation_reason"] == "Grantor withdrawing delegation permission"

    # Duplicate revocation returns 409
    dup_res = client.post(
        f"/api/v1/delegation/grants/{grant_id}/revoke",
        json={"reason": "Second revoke attempt"},
        headers=headers,
    )
    assert dup_res.status_code == 409

    # Verification attempt after revocation
    verify_payload = {
        "delegation_token": token,
        "requested_action": "read:evidence",
        "requested_resource": "case:case-test",
        "audience": "https://api.trustplatform.internal",
    }
    verify_res = client.post("/api/v1/delegation/verify", json=verify_payload)
    assert verify_res.status_code == 200
    assert verify_res.json()["decision"] == "DENIED"
    assert verify_res.json()["reason_code"] == "GRANT_REVOKED"


def test_grantee_agent_revocation_denies_delegation(client: TestClient, subject_token: str):
    """When a grantee AI Agent is revoked in Phase 14, in-flight delegation is DENIED with GRANTEE_AGENT_INACTIVE."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    # Register dynamic agent
    slug = f"agent-linked-{uuid.uuid4().hex[:6]}"
    reg_res = client.post(
        "/api/v1/agents",
        json={
            "name": "Linked Test Agent",
            "agent_slug": slug,
            "manifest": {"capabilities": ["task:execute"], "model_provider": "google", "model_id": "gemini-1.5-pro"},
        },
        headers=headers,
    )
    agent_id = reg_res.json()["id"]

    # Delegate to active agent
    grant_payload = {
        "grantee_id": agent_id,
        "grantee_type": "AI_AGENT",
        "actions": ["task:execute"],
        "resources": ["case:*"],
        "audiences": ["https://api.trustplatform.internal"],
    }
    grant_res = client.post("/api/v1/delegation/grants", json=grant_payload, headers=headers)
    token = grant_res.json()["delegation_token"]

    # Revoke agent in Phase 14 registry
    client.post(f"/api/v1/agents/{agent_id}/revoke", json={"reason": "Compromised agent decommission"}, headers=headers)

    # In-flight delegation check
    verify_payload = {
        "delegation_token": token,
        "requested_action": "task:execute",
        "requested_resource": "case:case-123",
        "audience": "https://api.trustplatform.internal",
    }
    verify_res = client.post("/api/v1/delegation/verify", json=verify_payload)
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data["decision"] == "DENIED"
    assert data["reason_code"] == "GRANTEE_AGENT_INACTIVE"


# -----------------------------------------------------------------------------
# 5. Boundary Isolation & Privileged Access
# -----------------------------------------------------------------------------
def test_cross_user_grant_revocation_blocked(
    client: TestClient, subject_token: str, subject_b_token: str
):
    """User B cannot revoke User A's delegation grant (HTTP 403 Forbidden)."""
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    headers_b = {"Authorization": f"Bearer {subject_b_token}"}

    grant_payload = {
        "grantee_id": "agent-ocr-extractor-01",
        "grantee_type": "AI_AGENT",
        "actions": ["read:evidence"],
        "resources": ["case:*"],
        "audiences": ["https://api.trustplatform.internal"],
    }
    grant_res = client.post("/api/v1/delegation/grants", json=grant_payload, headers=headers_a)
    grant_id = grant_res.json()["id"]

    # User B attempts to revoke
    revoke_res = client.post(
        f"/api/v1/delegation/grants/{grant_id}/revoke",
        json={"reason": "Attacker trying to revoke grant"},
        headers=headers_b,
    )
    assert revoke_res.status_code == 403


def test_auditor_can_inspect_delegation_grants(client: TestClient, auditor_token: str):
    """Auditors have privileged read access to list and inspect delegation grants."""
    headers_aud = {"Authorization": f"Bearer {auditor_token}"}

    list_res = client.get("/api/v1/delegation/grants", headers=headers_aud)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
