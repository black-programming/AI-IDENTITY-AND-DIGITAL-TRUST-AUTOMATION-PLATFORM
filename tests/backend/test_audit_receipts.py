"""Automated Tests for Phase 12 — Audit Trail and Cryptographic Evidence Receipts.

Covers security action recording, actor/target/timestamp tracking, correlation IDs,
tamper-evident hash chaining, data minimization/PII redaction, access-controlled receipts,
and public cryptographic receipt verification.
"""

import copy
from fastapi.testclient import TestClient

from app.services.audit_service import (
    GENESIS_HASH,
    _MOCK_AUDIT_LOGS,
    AuditService,
)
from app.services.synthetic_docs import generate_synthetic_document_image


# -----------------------------------------------------------------------------
# 1. Tamper-Evident Audit Logging & Hash Chaining
# -----------------------------------------------------------------------------
def test_record_security_event_chains_hashes():
    """Security events are chained with SHA-256 hashes linking backwards to previous records."""
    initial_count = len(_MOCK_AUDIT_LOGS)

    ev1 = AuditService.record_event(
        action_type="TEST_ACTION_ALPHA",
        target_resource="system/test1",
        actor_id="actor-001",
        actor_role="ROLE_SYS_ADMIN",
    )
    assert ev1.event_id is not None
    assert len(ev1.record_hash) == 64
    if initial_count == 0:
        assert ev1.previous_record_hash == GENESIS_HASH

    ev2 = AuditService.record_event(
        action_type="TEST_ACTION_BETA",
        target_resource="system/test2",
        actor_id="actor-002",
        actor_role="ROLE_VERIFIER",
    )
    assert ev2.previous_record_hash == ev1.record_hash
    assert len(ev2.record_hash) == 64


def test_audit_chain_verification_clean():
    """Cryptographic audit chain verification returns valid when log is untampered."""
    res = AuditService.verify_audit_chain()
    assert res.is_valid is True
    assert res.tampered_record_id is None
    assert res.total_records_checked >= 2


def test_audit_chain_detects_tampering():
    """Modifying any historical record in the audit trail causes chain verification to fail."""
    assert len(_MOCK_AUDIT_LOGS) >= 2
    # Create backup of second record
    original_record = copy.deepcopy(_MOCK_AUDIT_LOGS[1])

    try:
        # Tamper with action_type
        _MOCK_AUDIT_LOGS[1]["action_type"] = "MALICIOUS_TAMPERED_ACTION"

        # Verify chain detects tampering
        res = AuditService.verify_audit_chain()
        assert res.is_valid is False
        assert res.tampered_record_id == original_record["event_id"]
        assert "Tampering detected" in res.message or "mismatch" in res.message
    finally:
        # Restore record to untampered state
        _MOCK_AUDIT_LOGS[1] = original_record

    # Verify chain is restored
    res_restored = AuditService.verify_audit_chain()
    assert res_restored.is_valid is True


def test_audit_data_minimization_redacts_secrets_and_raw_bytes():
    """Sensitive passwords, credentials, and raw file bytes are redacted from audit metadata."""
    ev = AuditService.record_event(
        action_type="AUTH_AUTHENTICATED",
        target_resource="auth/session",
        actor_id="actor-test-redaction",
        metadata={
            "user_email": "citizen@test.org",
            "password": "SuperSecretPassword123!",
            "secret_token": "bearer-secret-xyz",
            "safe_attribute": "ALLOWED_VALUE",
            "raw_bytes": "aW1hZ2UtYnl0ZXMtY29udGVudA==",
        },
    )
    meta = ev.event_metadata
    assert meta["password"] == "***REDACTED***"
    assert meta["secret_token"] == "***REDACTED***"
    assert meta["raw_bytes"] == "***REDACTED***"
    assert meta["safe_attribute"] == "ALLOWED_VALUE"
    assert meta["user_email"] == "citizen@test.org"


# -----------------------------------------------------------------------------
# 2. Audit Trail API Endpoints & Role-Based Access Control
# -----------------------------------------------------------------------------
def test_auditor_and_admin_can_list_all_audit_events(
    client: TestClient, auditor_token: str, admin_token: str
):
    """Auditors and Sys Admins have privileged access to query global audit logs."""
    headers_aud = {"Authorization": f"Bearer {auditor_token}"}
    res_aud = client.get("/api/v1/audit/events", headers=headers_aud)
    assert res_aud.status_code == 200
    assert "events" in res_aud.json()
    assert res_aud.json()["total"] >= 1

    headers_adm = {"Authorization": f"Bearer {admin_token}"}
    res_adm = client.get("/api/v1/audit/events", headers=headers_adm)
    assert res_adm.status_code == 200


def test_verify_audit_hash_chain_endpoint_authorized(
    client: TestClient, auditor_token: str, verifier_token: str
):
    """Privileged roles can invoke the cryptographic audit chain verification endpoint."""
    headers = {"Authorization": f"Bearer {auditor_token}"}
    res = client.post("/api/v1/audit/verify-chain", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["total_records_checked"] >= 1


def test_verify_audit_hash_chain_endpoint_forbidden_for_subject(
    client: TestClient, subject_token: str
):
    """Standard subjects are strictly blocked from invoking the chain audit tool (HTTP 403)."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    res = client.post("/api/v1/audit/verify-chain", headers=headers)
    assert res.status_code == 403


def test_subject_can_query_own_case_audit_history(client: TestClient, subject_token: str):
    """Citizen can inspect the complete audit trail for their own verification case."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    # Record case-linked audit event
    AuditService.record_event(
        action_type="CASE_STATE_CHANGED",
        target_resource=f"cases/{case_id}",
        case_id=case_id,
        actor_id=case_res.json()["user_id"],
    )

    res = client.get(f"/api/v1/audit/cases/{case_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert data["events"][0]["case_id"] == case_id


def test_subject_b_blocked_from_citizen_a_case_audit_history(
    client: TestClient, subject_token: str, subject_b_token: str
):
    """Subject B is blocked with 403 Forbidden when attempting to read Subject A's case audit log."""
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_a)
    case_id = case_res.json()["case_id"]

    headers_b = {"Authorization": f"Bearer {subject_b_token}"}
    res_b = client.get(f"/api/v1/audit/cases/{case_id}", headers=headers_b)
    assert res_b.status_code == 403


# -----------------------------------------------------------------------------
# 3. Evidence Receipts Workflow & Public Cryptographic Verification
# -----------------------------------------------------------------------------
def test_generate_and_retrieve_evidence_receipt(client: TestClient, subject_token: str):
    """Citizen can request and retrieve a signed, Merkle-backed evidence receipt for their case."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    # Issue receipt via POST
    issue_res = client.post(f"/api/v1/receipts/cases/{case_id}/issue", headers=headers)
    assert issue_res.status_code == 200
    receipt = issue_res.json()

    assert receipt["case_id"] == case_id
    assert "receipt_id" in receipt
    assert "issuer" in receipt
    assert "claim" in receipt
    assert "determination" in receipt
    assert "integrity" in receipt
    assert receipt["integrity"]["merkle_root"] is not None
    assert receipt["integrity"]["signature"].startswith("HMAC_SHA256:")
    assert receipt["integrity"]["receipt_token"].startswith("rcpt_")

    # Fetch receipt via GET
    get_res = client.get(f"/api/v1/receipts/{case_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["receipt_id"] == receipt["receipt_id"]


def test_cross_user_receipt_issue_blocked(
    client: TestClient, subject_token: str, subject_b_token: str
):
    """Subject B cannot generate or issue a receipt for Subject A's case (HTTP 403)."""
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_a)
    case_id = case_res.json()["case_id"]

    headers_b = {"Authorization": f"Bearer {subject_b_token}"}
    res_b = client.post(f"/api/v1/receipts/cases/{case_id}/issue", headers=headers_b)
    assert res_b.status_code == 403


def test_public_evidence_receipt_cryptographic_verification(
    client: TestClient, subject_token: str
):
    """Public, unauthenticated client can cryptographically verify an issued receipt token."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    issue_res = client.post(f"/api/v1/receipts/cases/{case_id}/issue", headers=headers)
    receipt = issue_res.json()
    receipt_token = receipt["integrity"]["receipt_token"]

    # Verify without any Authorization header!
    verify_res = client.post("/api/v1/receipts/verify", json={"receipt_token": receipt_token})
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["is_valid"] is True
    assert verify_data["case_id"] == case_id
    assert "authentic" in verify_data["message"]


def test_tampered_receipt_payload_verification_fails(client: TestClient, subject_token: str):
    """Public verification fails when a receipt payload's decision or determination is tampered."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    issue_res = client.post(f"/api/v1/receipts/cases/{case_id}/issue", headers=headers)
    receipt = issue_res.json()

    # Tamper with the Merkle root or determination
    tampered_receipt = copy.deepcopy(receipt)
    tampered_receipt["integrity"]["merkle_root"] = "0000000000000000000000000000000000000000000000000000000000000000"

    verify_res = client.post("/api/v1/receipts/verify", json={"receipt_payload": tampered_receipt})
    assert verify_res.status_code == 200
    assert verify_res.json()["is_valid"] is False
    assert "mismatch" in verify_res.json()["message"]
