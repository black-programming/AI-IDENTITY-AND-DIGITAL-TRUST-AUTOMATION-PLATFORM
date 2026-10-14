"""Tests for Deterministic Trust & Policy Engine."""

from fastapi.testclient import TestClient


def test_policy_allow_happy_path(client: TestClient, subject_token: str):
    """Valid unexpired synthetic national ID with high confidence returns ALLOW."""
    payload = {
        "case_id": "00000000-0000-0000-0000-000000000001",
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {
            "document_number": "A12345678",
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
    assert data["requires_human_review"] is False


def test_policy_block_expired_document(client: TestClient, subject_token: str):
    """Expired document must be blocked with DEC_BLOCK_DOC_EXPIRED."""
    payload = {
        "case_id": "00000000-0000-0000-0000-000000000002",
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {
            "document_number": "A87654321",
            "full_name": "MORGAN EXPIRED CITIZEN",
            "expiry_date": "2023-01-01",  # Expired in past
        },
        "ocr_confidence": 0.92,
    }
    headers = {"Authorization": f"Bearer {subject_token}"}
    response = client.post("/api/v1/policy/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert "DEC_BLOCK_DOC_EXPIRED" in data["reason_codes"]
    assert data["requires_human_review"] is False


def test_policy_verify_low_ocr_confidence(client: TestClient, subject_token: str):
    """Low OCR confidence (< 0.85) must trigger VERIFY and require human review."""
    payload = {
        "case_id": "00000000-0000-0000-0000-000000000003",
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {
            "document_number": "A11223344",
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


def test_policy_block_revoked_identifier(client: TestClient, subject_token: str):
    """Compromised document number must return BLOCK and DEC_BLOCK_BLACKLISTED_IDENTIFIER."""
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
