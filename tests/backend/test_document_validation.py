"""Automated tests for Phase 9 — Deterministic Document Validation Engine."""

import io
import pytest
from fastapi.testclient import TestClient

from app.services.synthetic_docs import generate_synthetic_document_image


def get_error_message(res) -> str:
    """Helper to extract error message from standard platform envelope or detail."""
    data = res.json()
    if isinstance(data, dict):
        if "error" in data and isinstance(data["error"], dict):
            return data["error"].get("message", "")
        if "detail" in data:
            return str(data["detail"])
    return str(data)


# -----------------------------------------------------------------------------
# 1. Happy Path Deterministic Validation
# -----------------------------------------------------------------------------
def test_validation_happy_path_national_id(client: TestClient, subject_token: str):
    """Valid unexpired National ID passes all deterministic checks with overall PASS outcome."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    assert case_res.status_code == 201
    case_id = case_res.json()["case_id"]

    val_payload = {
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {
            "document_number": "NAT-98421074",
            "full_name": "Jane Synth Citizen",
            "date_of_birth": "1988-04-12",
            "issue_date": "2020-05-15",
            "expiry_date": "2030-05-15",
            "issuing_authority": "National Identity Authority",
            "country": "IND",
        },
        "user_profile": {"full_name": "Jane Synth Citizen", "date_of_birth": "1988-04-12"},
    }

    res = client.post(f"/api/v1/cases/{case_id}/validate", json=val_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["validation_passed"] is True
    assert data["overall_outcome"] == "PASS"
    assert "VAL_PASSED_ALL_CHECKS" in data["reason_codes"]
    assert len(data["flags"]) == 0
    assert all(r["passed"] for r in data["rule_results"])


# -----------------------------------------------------------------------------
# 2. Required Fields & Format Checks
# -----------------------------------------------------------------------------
def test_validation_missing_required_fields_fails(client: TestClient, subject_token: str):
    """Missing mandatory fields fail deterministic validation with ERR_MISSING_REQUIRED_FIELDS."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    val_payload = {
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {
            # Missing full_name and expiry_date
            "document_number": "NAT-98421074",
            "date_of_birth": "1988-04-12",
        },
    }

    res = client.post(f"/api/v1/cases/{case_id}/validate", json=val_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["validation_passed"] is False
    assert data["overall_outcome"] == "FAIL"
    assert "ERR_MISSING_REQUIRED_FIELDS" in data["reason_codes"]
    assert "DEC_BLOCK_REQUIRED_FIELD_MISSING" in data["reason_codes"]
    assert "FLAG_INCOMPLETE_FIELDS" in data["flags"]


def test_validation_invalid_format_regex_fails(client: TestClient, subject_token: str):
    """Document number not matching regex format triggers ERR_INVALID_FIELD_FORMAT."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    val_payload = {
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {
            "document_number": "INVALID-123",  # Expected format: NAT-12345678
            "full_name": "Jane Citizen",
            "date_of_birth": "1988-04-12",
            "expiry_date": "2030-05-15",
        },
    }

    res = client.post(f"/api/v1/cases/{case_id}/validate", json=val_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["validation_passed"] is False
    assert "ERR_INVALID_FIELD_FORMAT" in data["reason_codes"]
    assert "FLAG_INVALID_FORMAT" in data["flags"]


# -----------------------------------------------------------------------------
# 3. Temporal Validity & Expiry Checks
# -----------------------------------------------------------------------------
def test_validation_expired_document_fails(client: TestClient, subject_token: str):
    """Expired document fails validation, sets DEC_BLOCK_DOC_EXPIRED, and blocks case decision."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    val_payload = {
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {
            "document_number": "NAT-98421074",
            "full_name": "Marcus Old Synth",
            "date_of_birth": "1975-01-10",
            "issue_date": "2010-01-01",
            "expiry_date": "2020-01-01",  # Expired
        },
    }

    res = client.post(f"/api/v1/cases/{case_id}/validate", json=val_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["validation_passed"] is False
    assert data["overall_outcome"] == "FAIL"
    assert "DEC_BLOCK_DOC_EXPIRED" in data["reason_codes"]
    assert "ERR_DOCUMENT_EXPIRED" in data["reason_codes"]
    assert "FLAG_EXPIRED_DOCUMENT" in data["flags"]

    # Verify case decision is updated to BLOCK
    case_detail = client.get(f"/api/v1/cases/{case_id}", headers=headers).json()
    assert case_detail["current_decision"] == "BLOCK"


def test_validation_future_issue_date_fails(client: TestClient, subject_token: str):
    """Future issue date triggers chronological inconsistency anomaly."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    val_payload = {
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {
            "document_number": "NAT-98421074",
            "full_name": "Future Traveler",
            "date_of_birth": "1990-01-01",
            "issue_date": "2099-01-01",  # Future date
            "expiry_date": "2109-01-01",
        },
    }

    res = client.post(f"/api/v1/cases/{case_id}/validate", json=val_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["validation_passed"] is False
    assert "ERR_FUTURE_ISSUE_DATE" in data["reason_codes"]
    assert "FLAG_CHRONOLOGICAL_ANOMALY" in data["flags"]


def test_validation_underage_subject_flagged(client: TestClient, subject_token: str):
    """Subject under 18 triggers underage anomaly flag."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_DL_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    val_payload = {
        "claim_type": "SYNTH_DL_V1",
        "extracted_fields": {
            "document_number": "DL-TN-2021-998811",
            "full_name": "Teen Driver",
            "date_of_birth": "2015-05-10",  # ~11 years old
            "issue_date": "2021-01-01",
            "expiry_date": "2031-01-01",
            "vehicle_classes": "LMV",
        },
    }

    res = client.post(f"/api/v1/cases/{case_id}/validate", json=val_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "FLAG_UNDERAGE_SUBJECT" in data["flags"]
    assert "ERR_UNDERAGE_SUBJECT" in data["reason_codes"]


# -----------------------------------------------------------------------------
# 4. MRZ Algorithmic Checksums
# -----------------------------------------------------------------------------
def test_validation_mrz_checksum_valid_passport(client: TestClient, subject_token: str):
    """Passport with valid standard ICAO 9303 MRZ checksums passes."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_PASSPORT_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    val_payload = {
        "claim_type": "SYNTH_PASSPORT_V1",
        "extracted_fields": {
            "document_number": "P9823411",
            "full_name": "Alex Synth Traveler",
            "date_of_birth": "1995-11-03",
            "expiry_date": "2028-07-01",
            "mrz_line1": "P<INDSYNTH<<ALEX<<<<<<<<<<<<<<<<<<<<<<<<<",
            "mrz_line2": "P9823411<7IND9511039M2807018<<<<<<<<<<<<<<2",
        },
    }

    res = client.post(f"/api/v1/cases/{case_id}/validate", json=val_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["validation_passed"] is True
    mrz_rule = next(r for r in data["rule_results"] if r["rule_id"] == "VAL-MRZ-CHECKSUM")
    assert mrz_rule["passed"] is True


def test_validation_mrz_checksum_tampered_fails(client: TestClient, subject_token: str):
    """Tampered MRZ check digit fails algorithmic validation with ERR_MRZ_CHECKSUM_FAILED."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_PASSPORT_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    val_payload = {
        "claim_type": "SYNTH_PASSPORT_V1",
        "extracted_fields": {
            "document_number": "P9823411",
            "full_name": "Alex Synth Traveler",
            "date_of_birth": "1995-11-03",
            "expiry_date": "2028-07-01",
            "mrz_line1": "P<INDSYNTH<<ALEX<<<<<<<<<<<<<<<<<<<<<<<<<",
            # Tampered: char 9 check digit changed from 7 to 0
            "mrz_line2": "P9823411<0IND9511039M2807018<<<<<<<<<<<<<<2",
        },
    }

    res = client.post(f"/api/v1/cases/{case_id}/validate", json=val_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["validation_passed"] is False
    assert "ERR_MRZ_CHECKSUM_FAILED" in data["reason_codes"]
    assert "FLAG_MRZ_CHECKSUM_FAILED" in data["flags"]


# -----------------------------------------------------------------------------
# 5. Cross-Field & Identity Consistency
# -----------------------------------------------------------------------------
def test_validation_cross_field_profile_name_mismatch_flagged(client: TestClient, subject_token: str):
    """Profile name showing zero overlap with document name flags FLAGGED outcome."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    val_payload = {
        "claim_type": "SYNTH_NAT_ID_V1",
        "extracted_fields": {
            "document_number": "NAT-98421074",
            "full_name": "Jane Synth Citizen",
            "date_of_birth": "1988-04-12",
            "expiry_date": "2030-05-15",
        },
        "user_profile": {
            "full_name": "Bob Robert Attacker",  # Completely disjoint name
            "date_of_birth": "1988-04-12",
        },
    }

    res = client.post(f"/api/v1/cases/{case_id}/validate", json=val_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["overall_outcome"] == "FLAGGED"
    assert "ERR_CROSS_FIELD_CONFLICT" in data["reason_codes"]
    assert "DEC_VERIFY_CROSS_FIELD_MISMATCH" in data["reason_codes"]
    assert "FLAG_PROFILE_NAME_MISMATCH" in data["flags"]

    # Verify case status escalated to Under Review
    case_detail = client.get(f"/api/v1/cases/{case_id}", headers=headers).json()
    assert case_detail["status"] == "Under Review"


def test_validation_cross_field_viz_mrz_mismatch_flagged(client: TestClient, subject_token: str):
    """VIZ document number conflicting with MRZ document number triggers mismatch flag."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_PASSPORT_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    val_payload = {
        "claim_type": "SYNTH_PASSPORT_V1",
        "extracted_fields": {
            "document_number": "P1111111",  # VIZ says P1111111
            "full_name": "Alex Traveler",
            "date_of_birth": "1995-11-03",
            "expiry_date": "2028-07-01",
            "mrz_line1": "P<INDSYNTH<<ALEX<<<<<<<<<<<<<<<<<<<<<<<<<",
            "mrz_line2": "P9823411<7IND9511039M2807018<<<<<<<<<<<<<<2",  # MRZ says P9823411
        },
    }

    res = client.post(f"/api/v1/cases/{case_id}/validate", json=val_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "FLAG_VIZ_MRZ_CONFLICT" in data["flags"]
    assert "ERR_VIZ_MRZ_MISMATCH" in data["reason_codes"]


# -----------------------------------------------------------------------------
# 6. Pipeline Integration & Access Control
# -----------------------------------------------------------------------------
def test_validation_pipeline_integration_with_ocr(client: TestClient, subject_token: str):
    """Calling POST /cases/{case_id}/validate without body automatically pulls from OCR extractions."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    # Upload evidence and run OCR
    img_bytes, _, _ = generate_synthetic_document_image("SYNTH_NAT_ID_V1")
    upload_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload",
        files={"file": ("national_id.png", io.BytesIO(img_bytes), "image/png")},
        headers=headers,
    )
    file_id = upload_res.json()["file_id"]
    client.post(f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr", headers=headers)

    # Validate without supplying payload
    val_res = client.post(f"/api/v1/cases/{case_id}/validate", json={}, headers=headers)
    assert val_res.status_code == 200
    data = val_res.json()
    assert data["validation_passed"] is True
    assert data["overall_outcome"] == "PASS"

    # Read latest validation report via GET
    get_val = client.get(f"/api/v1/cases/{case_id}/validation", headers=headers)
    assert get_val.status_code == 200
    assert get_val.json()["validation_id"] == data["validation_id"]


def test_validation_cross_user_access_blocked(client: TestClient, subject_token: str, subject_b_token: str):
    """Subject B cannot run or view validation on Subject A's case (HTTP 403)."""
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_a)
    case_id = case_res.json()["case_id"]

    headers_b = {"Authorization": f"Bearer {subject_b_token}"}
    res = client.post(f"/api/v1/cases/{case_id}/validate", json={}, headers=headers_b)
    assert res.status_code == 403
    assert "Cross-user access denied" in get_error_message(res)


def test_validation_unauthenticated_request_blocked(client: TestClient):
    """Unauthenticated validation requests fail closed with HTTP 401."""
    res = client.post("/api/v1/cases/00000000-0000-0000-0000-000000000001/validate")
    assert res.status_code == 401
