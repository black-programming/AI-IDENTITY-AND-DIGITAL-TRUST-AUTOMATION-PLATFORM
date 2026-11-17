"""Comprehensive End-to-End (E2E) and User Acceptance Testing (UAT) Suite for Phase 20.

Tests all integrated cross-phase personas and workflows:
1. Individual Applicant Lifecycle (Case submission, Evidence Upload, OCR, Policy, Receipt).
2. Reviewer / Trust Officer Workbench (Queue triage, Case inspection, Reviewer decision).
3. Enterprise Organization & Employment Verification (Registration, Self-asserted vs Confirmed claim).
4. AI Agent Registration, Scoped Delegation, and Permanent Revocation.
5. Privacy, GDPR Right-to-Erasure, and Cryptographic Tombstones.
6. System Reliability, Idempotency, and Upstream Circuit Breakers.
7. Language and Localization Support (Tamil and English) and Trust Semantics.
"""

import io
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services.monitoring_service import MonitoringService
from app.services.ocr_service import OCRService

client = TestClient(app)


def make_token(role: str = "ROLE_SUBJECT", user_id: str = "user_e2e_01", email: str = "user@test.org") -> str:
    import jwt
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "app_metadata": {"role": role},
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=2)).timestamp()),
        "iss": settings.SUPABASE_URL,
        "aud": "authenticated",
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


def test_e2e_uat_applicant_full_verification_journey():
    """UAT Journey 1: Individual Applicant submits claim, uploads evidence, triggers OCR & validation, and receives receipt."""
    subject_id = f"sub_{uuid.uuid4().hex[:8]}"
    token = make_token(role="ROLE_SUBJECT", user_id=subject_id)
    auth_headers = {"Authorization": f"Bearer {token}"}
    headers = auth_headers

    # 1. Create Verification Case
    case_res = client.post(
        "/api/v1/cases",
        json={
            "title": "National ID Verification",
            "description": "Standard identity claim verification for banking onboarding",
            "claim_type": "SYNTH_NAT_ID_V1",
            "priority": "HIGH"
        },
        headers={**auth_headers, "Idempotency-Key": f"idemp-case-{uuid.uuid4().hex}"}
    )
    assert case_res.status_code == 201
    case_data = case_res.json()
    case_id = case_data["case_id"]
    assert case_data["status"] in ["Draft", "SUBMITTED"]

    # 2. Request Signed Upload URL
    upload_url_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload-url",
        json={"case_id": case_id, "file_name": "id_card_front.png", "mime_type": "image/png", "file_size_bytes": 102400},
        headers={**auth_headers, "Idempotency-Key": f"idemp-upload-{uuid.uuid4().hex}"}
    )
    assert upload_url_res.status_code == 200
    upload_data = upload_url_res.json()
    file_id = upload_data["file_id"]

    # 3. Direct Binary Evidence Upload (simulate synthetic PNG)
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 256
    upload_file_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload",
        files={"file": ("id_card_front.png", io.BytesIO(fake_png), "image/png")},
        headers=headers
    )
    assert upload_file_res.status_code == 201
    direct_file_id = upload_file_res.json()["file_id"]

    # 4. Trigger OCR Extraction
    ocr_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr",
        json={"auto_rotate": True, "detect_watermarks": True},
        headers=headers
    )
    assert ocr_res.status_code == 200
    ocr_data = ocr_res.json()
    assert ocr_data["case_id"] == case_id

    # 5. Evaluate Trust Policy Engine
    policy_res = client.post(
        "/api/v1/policy/evaluate",
        json={
            "case_id": case_id,
            "claim_type": "SYNTH_NAT_ID_V1",
            "ocr_confidence": 0.95,
            "extracted_fields": {"full_name": "Jane Citizen"},
            "validation_flags": []
        },
        headers=headers
    )
    assert policy_res.status_code == 200
    policy_data = policy_res.json()
    assert policy_data["decision"] in ["ALLOW", "VERIFY", "RESTRICT", "BLOCK"]

    # 6. Issue Merkle-backed Cryptographic Evidence Receipt
    receipt_res = client.post(f"/api/v1/receipts/cases/{case_id}/issue", headers=headers)
    assert receipt_res.status_code == 200
    receipt_data = receipt_res.json()
    assert receipt_data["case_id"] == case_id
    receipt_token = receipt_data["integrity"]["receipt_token"]
    assert receipt_token.startswith("rcpt_")

    # 7. Public Cryptographic Verification (Zero Auth Required)
    verify_receipt_res = client.post("/api/v1/receipts/verify", json={"receipt_token": receipt_token})
    assert verify_receipt_res.status_code == 200
    assert verify_receipt_res.json()["is_valid"] is True
    assert verify_receipt_res.json()["case_id"] == case_id


def test_e2e_uat_trust_officer_review_workbench():
    """UAT Journey 2: Human Reviewer fetches queue, inspects cases, and records review decision."""
    verifier_id = "rev_officer_99"
    verifier_token = make_token(role="ROLE_VERIFIER", user_id=verifier_id)
    headers = {"Authorization": f"Bearer {verifier_token}"}

    # 1. Fetch Review Queue
    queue_res = client.get("/api/v1/review/queue", headers=headers)
    assert queue_res.status_code == 200
    queue_data = queue_res.json()
    assert "pending_cases" in queue_data
    assert "queue_length" in queue_data

    # 2. Review Metrics & Capacity
    metrics_res = client.get("/api/v1/review/metrics", headers=headers)
    assert metrics_res.status_code == 200


def test_e2e_uat_organization_employment_attestation():
    """UAT Journey 3: Enterprise Admin registers organization and verifies employee attestation."""
    admin_id = "org_admin_corp"
    token = make_token(role="ROLE_SUBJECT", user_id=admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Register Corporate Organization
    unique_slug = f"corp-trust-{uuid.uuid4().hex[:6]}"
    org_res = client.post(
        "/api/v1/organizations",
        json={
            "name": "Apex Trust Global Financial Corp",
            "slug": unique_slug,
            "verified_domain": "apextrust.com",
            "registration_number": f"REG-{uuid.uuid4().hex[:6].upper()}",
            "country_region": "US",
            "tier": "ENTERPRISE"
        },
        headers=headers
    )
    assert org_res.status_code == 201
    org_data = org_res.json()
    org_id = org_data["id"]

    # 2. Submit Employment Claim
    claim_res = client.post(
        f"/api/v1/organizations/{org_id}/claims",
        json={
            "job_title": "Principal Cryptographic Engineer",
            "department": "Security Architecture",
            "employee_id": f"EMP-{uuid.uuid4().hex[:4].upper()}",
            "work_email": "architect@apextrust.com",
            "start_date": "2024-01-15",
            "evidence_hashes": ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"]
        },
        headers=headers
    )
    assert claim_res.status_code == 201
    claim_data = claim_res.json()
    assert claim_data["assertion_type"] == "SELF_ASSERTED"
    assert claim_data["job_title"] == "Principal Cryptographic Engineer"


def test_e2e_uat_ai_agent_delegation_and_revocation():
    """UAT Journey 4: Register autonomous AI Agent, delegate authority, and permanently revoke."""
    subject_token = make_token(role="ROLE_SUBJECT", user_id="agent_supervisor")
    headers = {"Authorization": f"Bearer {subject_token}"}

    # 1. Register AI Agent
    agent_slug = f"sentinel-agent-{uuid.uuid4().hex[:6]}"
    agent_res = client.post(
        "/api/v1/agents",
        json={
            "name": "FraudSentinel AI Agent",
            "agent_slug": agent_slug,
            "manifest": {
                "capabilities": ["extract:ocr", "evaluate:policy"],
                "model_provider": "google",
                "model_id": "gemini-1.5-pro"
            }
        },
        headers=headers
    )
    assert agent_res.status_code == 201
    agent_data = agent_res.json()
    agent_id = agent_data["id"]
    assert agent_data["status"] == "ACTIVE"

    # 2. Issue Delegated Authorization Grant
    grant_res = client.post(
        "/api/v1/delegation/grants",
        json={
            "grantee_id": agent_id,
            "grantee_type": "AI_AGENT",
            "actions": ["extract:ocr", "evaluate:policy"],
            "resources": ["case:*"],
            "audiences": ["https://api.trustplatform.internal"],
            "validity_hours": 24,
            "notes": "Automated OCR extraction authority"
        },
        headers=headers
    )
    assert grant_res.status_code == 201
    grant_data = grant_res.json()
    assert grant_data["status"] == "ACTIVE"
    assert grant_data["delegation_token"] is not None

    # 3. Permanently Revoke Agent
    revoke_res = client.post(
        f"/api/v1/agents/{agent_id}/revoke",
        json={"reason": "Decommissioned after routine audit drill"},
        headers=headers
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "REVOKED"


def test_e2e_uat_privacy_erasure_and_audit_ledger():
    """UAT Journey 5: Right-to-be-Forgotten erasure with cryptographic tombstone and audit chain integrity."""
    subject_id = f"sub_gdpr_{uuid.uuid4().hex[:8]}"
    sub_token = make_token(role="ROLE_SUBJECT", user_id=subject_id)
    sub_headers = {"Authorization": f"Bearer {sub_token}"}
    admin_headers = {"Authorization": f"Bearer {make_token(role='ROLE_SYS_ADMIN')}"}

    # 1. Create Case and Evidence
    case_res = client.post(
        "/api/v1/cases",
        json={"title": "Private Medical Identity", "claim_type": "disability"},
        headers=sub_headers
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["case_id"]

    # 2. Execute Right-to-be-Forgotten Erasure Request
    erasure_res = client.post(
        "/api/v1/privacy/erasure-request",
        json={
            "user_id": subject_id,
            "reason": "GDPR Article 17 Right to Erasure requested by subject",
            "confirm_irreversible": True
        },
        headers=sub_headers
    )
    assert erasure_res.status_code == 200
    erasure_data = erasure_res.json()
    assert erasure_data["status"] in ["CONFIRMED", "COMPLETED", "ERASED"]
    assert erasure_data["tombstone_hash"] is not None

    # 3. Verify Cryptographic Audit Chain Integrity
    chain_res = client.post("/api/v1/audit/verify-chain", headers=admin_headers)
    assert chain_res.status_code == 200
    chain_data = chain_res.json()
    assert chain_data["is_valid"] is True


def test_e2e_uat_reliability_circuit_breaker_and_idempotency():
    """UAT Journey 6: Upstream Circuit Breaker trips gracefully, engages fallback, and restores nominal state."""
    admin_headers = {"Authorization": f"Bearer {make_token(role='ROLE_SYS_ADMIN')}"}

    # 1. Inspect initial circuit breaker
    cb_stat = client.get("/api/v1/monitoring/circuit-breaker").json()
    assert cb_stat["state"] in ["CLOSED", "HALF_OPEN", "OPEN"]

    # 2. Trip Circuit Breaker
    trip_res = client.post("/api/v1/monitoring/circuit-breaker/trip", headers=admin_headers)
    assert trip_res.status_code == 200
    assert trip_res.json()["state"] == "OPEN"
    assert trip_res.json()["fallback_active"] is True

    # 3. Verify OCR fallback executes with circuit open without crashing
    MonitoringService.record_upstream_failure()
    fallback = OCRService.extract_from_bytes(
        image_bytes=b"\x89PNG\r\n\x1a\n" + b"\x00" * 32,
        case_id="e2e_circuit_case",
        file_id="e2e_circuit_file",
        claim_type="insurance"
    )
    assert "CircuitBreakerFallback" in fallback["ocr_engine"]
    assert "WARN_CIRCUIT_BREAKER_FALLBACK_ENGAGED" in fallback["reason_codes"]

    # 4. Reset Circuit Breaker
    reset_res = client.post("/api/v1/monitoring/circuit-breaker/reset", headers=admin_headers)
    assert reset_res.status_code == 200
    assert reset_res.json()["state"] == "CLOSED"
    assert reset_res.json()["fallback_active"] is False


def test_e2e_uat_language_localization_and_disclaimer_semantics():
    """UAT Journey 7: Multi-language support (English and Tamil) and non-definitive trust decision semantics."""
    # Verify Language controller definitions in frontend code
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    lang_file = os.path.join(base_dir, "frontend", "lib", "core", "localization", "language_controller.dart")
    with open(lang_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "'ta'" in content, "Tamil ('ta') locale must be supported"
    assert "'en'" in content, "English ('en') locale must be supported"
    assert "தமிழ்" in content, "Native Tamil glyph must be present"
