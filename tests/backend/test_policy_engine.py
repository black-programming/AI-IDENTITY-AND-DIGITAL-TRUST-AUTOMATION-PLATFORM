"""Comprehensive Automated Test Suite for Phase 11 — Trust and Policy Engine.

Covers versioned policy catalogs, multi-dimensional rule evaluation (Subject, Action, Resource, Scope,
Expiry, Context), reason codes, missing requirements, scope restrictions, fail-safe resilience
(never approve on upstream OCR failure), and dynamic case-level policy integration.
"""

from fastapi.testclient import TestClient

from app.services.synthetic_docs import generate_synthetic_document_image


# -----------------------------------------------------------------------------
# 1. Versioned Policy Catalog & Rule Inspection
# -----------------------------------------------------------------------------
def test_policy_catalog_retrieval(client: TestClient, subject_token: str):
    """Authenticated users can inspect active versioned policy rules catalog."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    res = client.get("/api/v1/policy/catalog", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "policies" in data
    assert data["total"] >= 3
    policy_ids = [p["policy_id"] for p in data["policies"]]
    assert "POL-IDENTITY-BASIC-V1" in policy_ids
    assert "POL-HIGH-ASSURANCE-V1" in policy_ids
    assert "POL-RESTRICTED-PROBATIONARY-V1" in policy_ids


def test_get_policy_rule_detail(client: TestClient, subject_token: str):
    """Retrieve full specification, confidence thresholds, and rule parameters for a specific policy."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    res = client.get("/api/v1/policy/rules/POL-HIGH-ASSURANCE-V1", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["policy_id"] == "POL-HIGH-ASSURANCE-V1"
    assert data["confidence_threshold"] == 0.90
    assert data["target_action"] == "access.elevated"
    assert data["target_resource"] == "resource:financial_vault"
    assert "vault:access" in data["required_scopes"]


# -----------------------------------------------------------------------------
# 2. Direct Policy Evaluation: ALLOW, BLOCK, VERIFY, RESTRICT
# -----------------------------------------------------------------------------
def test_policy_allow_happy_path(client: TestClient, subject_token: str):
    """Valid unexpired synthetic national ID with high confidence returns ALLOW and compliant reason codes."""
    payload = {
        "case_id": "00000000-0000-0000-0000-000000000001",
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {
            "document_number": "NAT-12345678",
            "full_name": "ALEXANDER TEST CITIZEN",
            "expiry_date": "2030-05-15",
            "date_of_birth": "1990-05-15",
        },
        "ocr_confidence": 0.95,
    }
    headers = {"Authorization": f"Bearer {subject_token}"}
    response = client.post("/api/v1/policy/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "ALLOW"
    assert "DEC_ALLOW_SATISFIED" in data["reason_codes"]
    assert "DEC_ALLOW_POLICY_COMPLIANT" in data["reason_codes"]
    assert data["requires_human_review"] is False
    assert "identity:verify" in data["permitted_scopes"]


def test_policy_block_expired_document(client: TestClient, subject_token: str):
    """Expired document must be blocked with DEC_BLOCK_DOC_EXPIRED and unexpired document requirement."""
    payload = {
        "case_id": "00000000-0000-0000-0000-000000000002",
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {
            "document_number": "NAT-87654321",
            "full_name": "MORGAN EXPIRED CITIZEN",
            "expiry_date": "2023-01-01",  # Expired
        },
        "ocr_confidence": 0.92,
    }
    headers = {"Authorization": f"Bearer {subject_token}"}
    response = client.post("/api/v1/policy/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert "DEC_BLOCK_DOC_EXPIRED" in data["reason_codes"]
    assert "unexpired_identity_document" in data["missing_requirements"]
    assert data["requires_human_review"] is False


def test_policy_block_revoked_identifier(client: TestClient, subject_token: str):
    """Compromised or fraudulent document number must return BLOCK and DEC_BLOCK_BLACKLISTED_IDENTIFIER."""
    payload = {
        "case_id": "00000000-0000-0000-0000-000000000004",
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {
            "document_number": "REVOKED999",
            "expiry_date": "2030-01-01",
        },
        "ocr_confidence": 0.99,
    }
    headers = {"Authorization": f"Bearer {subject_token}"}
    response = client.post("/api/v1/policy/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert "DEC_BLOCK_BLACKLISTED_IDENTIFIER" in data["reason_codes"]


def test_policy_block_underage_subject(client: TestClient, subject_token: str):
    """Subject below minimum policy age (e.g. 15 yrs old for adult ID) is blocked with DEC_BLOCK_UNDERAGE_SUBJECT."""
    payload = {
        "case_id": "00000000-0000-0000-0000-000000000005",
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {
            "document_number": "NAT-99887766",
            "full_name": "MINOR APPLICANT",
            "expiry_date": "2030-01-01",
            "date_of_birth": "2015-06-01",  # ~11 years old
        },
        "ocr_confidence": 0.95,
    }
    headers = {"Authorization": f"Bearer {subject_token}"}
    response = client.post("/api/v1/policy/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert "DEC_BLOCK_UNDERAGE_SUBJECT" in data["reason_codes"]


def test_policy_block_mrz_checksum_tampered(client: TestClient, subject_token: str):
    """Presence of deterministic MRZ checksum failure flag results in immediate BLOCK."""
    payload = {
        "case_id": "00000000-0000-0000-0000-000000000006",
        "claim_type": "SYNTH_PASSPORT_V1",
        "extracted_fields": {
            "document_number": "P12345678",
            "full_name": "TAMPERED PASSPORT USER",
            "expiry_date": "2030-01-01",
            "date_of_birth": "1995-01-01",
        },
        "ocr_confidence": 0.95,
        "validation_flags": ["DEC_BLOCK_MRZ_CHECKSUM_FAILED"],
    }
    headers = {"Authorization": f"Bearer {subject_token}"}
    response = client.post("/api/v1/policy/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert "DEC_BLOCK_MRZ_CHECKSUM_FAILED" in data["reason_codes"]


def test_policy_verify_low_ocr_confidence(client: TestClient, subject_token: str):
    """Low OCR confidence (< 0.85) triggers VERIFY, requires human review, and specifies higher-res requirement."""
    payload = {
        "case_id": "00000000-0000-0000-0000-000000000003",
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {
            "document_number": "NAT-11223344",
            "full_name": "BLURRY DOCUMENT USER",
            "expiry_date": "2029-01-01",
        },
        "ocr_confidence": 0.72,  # Low confidence
    }
    headers = {"Authorization": f"Bearer {subject_token}"}
    response = client.post("/api/v1/policy/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "VERIFY"
    assert "DEC_VERIFY_OCR_CONF_LOW" in data["reason_codes"]
    assert data["requires_human_review"] is True


def test_policy_verify_fail_safe_on_upstream_ocr_error(client: TestClient, subject_token: str):
    """CRITICAL SAFETY: When upstream OCR/AI service fails, engine MUST NEVER approve; defaults to VERIFY."""
    payload = {
        "case_id": "00000000-0000-0000-0000-000000000007",
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {},
        "ocr_confidence": 0.0,
        "context": {
            "ocr_engine_status": "FAILED",
            "upstream_error": "PaddleOCR process timed out",
        },
    }
    headers = {"Authorization": f"Bearer {subject_token}"}
    response = client.post("/api/v1/policy/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "VERIFY"
    assert "ERR_UPSTREAM_SERVICE_FAILED" in data["reason_codes"]
    assert "DEC_VERIFY_OCR_CONF_LOW" in data["reason_codes"]
    assert data["requires_human_review"] is True
    assert "clear_unambiguous_document_scan" in data["missing_requirements"]


def test_policy_verify_step_up_mfa_required(client: TestClient, subject_token: str):
    """Step-up authentication policy triggers VERIFY with missing requirement when MFA is not active."""
    payload = {
        "case_id": "00000000-0000-0000-0000-000000000008",
        "claim_type": "SYNTH_NAT_ID_V1",
        "policy_id": "POL-STEP-UP-AUTH-V1",
        "extracted_fields": {
            "document_number": "NAT-55667788",
            "expiry_date": "2030-01-01",
        },
        "ocr_confidence": 0.95,
        "context": {"mfa_authenticated": False},
    }
    headers = {"Authorization": f"Bearer {subject_token}"}
    response = client.post("/api/v1/policy/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "VERIFY"
    assert "DEC_VERIFY_STEP_UP_REQUIRED" in data["reason_codes"]
    assert "mfa_verification" in data["missing_requirements"]


def test_policy_restrict_probationary_scope(client: TestClient, subject_token: str):
    """Probationary policy returns RESTRICT with explicitly scoped permitted and restricted capabilities."""
    payload = {
        "case_id": "00000000-0000-0000-0000-000000000009",
        "claim_type": "SYNTH_NAT_ID_V1",
        "policy_id": "POL-RESTRICTED-PROBATIONARY-V1",
        "action": "access.probationary",
        "extracted_fields": {
            "document_number": "NAT-33445566",
            "expiry_date": "2029-01-01",
        },
        "ocr_confidence": 0.95,
    }
    headers = {"Authorization": f"Bearer {subject_token}"}
    response = client.post("/api/v1/policy/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "RESTRICT"
    assert "DEC_RESTRICT_CONDITIONAL_APPROVAL" in data["reason_codes"]
    assert "read_only" in data["permitted_scopes"]
    assert "financial_transfer" in data["restricted_scopes"]
    assert data["requires_human_review"] is False


# -----------------------------------------------------------------------------
# 3. Dynamic Case Policy Evaluation & Integration
# -----------------------------------------------------------------------------
def test_evaluate_case_policy_integration(client: TestClient, subject_token: str):
    """End-to-end integration: evaluate active case using stored OCR, validations, and update case timeline."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    # Create Case
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    assert case_res.status_code == 201
    case_id = case_res.json()["case_id"]

    # Upload Evidence
    import io
    img_bytes, _, _ = generate_synthetic_document_image("SYNTH_NAT_ID_V1")
    upload_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload",
        files={"file": ("national_id.png", io.BytesIO(img_bytes), "image/png")},
        headers=headers,
    )
    assert upload_res.status_code == 201
    file_id = upload_res.json()["file_id"]

    # Run OCR Extraction
    ocr_res = client.post(f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr", headers=headers)
    assert ocr_res.status_code == 200

    # Run Deterministic Validation
    val_res = client.post(f"/api/v1/cases/{case_id}/validate", headers=headers)
    assert val_res.status_code == 200

    # Execute Policy Evaluation against Case
    eval_res = client.post(f"/api/v1/policy/cases/{case_id}/evaluate", json={}, headers=headers)
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["case_id"] == case_id
    assert eval_data["decision"] in ("ALLOW", "VERIFY", "RESTRICT", "BLOCK")
    assert len(eval_data["reason_codes"]) >= 1

    # Verify Case Details reflect current_decision
    get_case_res = client.get(f"/api/v1/cases/{case_id}", headers=headers)
    assert get_case_res.status_code == 200
    assert get_case_res.json()["current_decision"] == eval_data["decision"]

    # Check Timeline Event recorded
    timeline = get_case_res.json()["timeline"]
    comments = [evt.get("comment", "") for evt in timeline]
    assert any("Policy" in c for c in comments)


def test_evaluate_case_policy_cross_user_forbidden(
    client: TestClient, subject_token: str, subject_b_token: str
):
    """Subject B is blocked from triggering or viewing policy evaluation on Subject A's case (HTTP 403)."""
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_a)
    case_id = case_res.json()["case_id"]

    headers_b = {"Authorization": f"Bearer {subject_b_token}"}
    res_b = client.post(f"/api/v1/policy/cases/{case_id}/evaluate", json={}, headers=headers_b)
    assert res_b.status_code == 403


def test_get_case_policy_evaluation_endpoint(client: TestClient, subject_token: str):
    """Case owner can fetch the latest policy evaluation record via GET endpoint."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    res = client.get(f"/api/v1/policy/cases/{case_id}/evaluation", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == case_id
    assert "decision" in data
    assert "reason_codes" in data
