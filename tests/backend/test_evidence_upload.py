"""Automated tests for Phase 7 — Secure Evidence Storage, Magic Byte Validation, Quarantine, and Signed URLs."""

import hashlib
import io
import pytest
from fastapi.testclient import TestClient

from app.services.evidence_service import _MOCK_EVIDENCE_DB


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
# Fixtures for Synthetic Valid and Malformed Evidence Payloads
# -----------------------------------------------------------------------------
PNG_MAGIC_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
JPEG_MAGIC_BYTES = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB\x00C\x00"
PDF_MAGIC_BYTES = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


# -----------------------------------------------------------------------------
# 1. Pre-Signed Upload URL Tests
# -----------------------------------------------------------------------------
def test_generate_upload_url_success(client: TestClient, subject_token: str):
    """Case owner can generate short-lived upload URL for valid evidence parameters."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    assert case_res.status_code == 201
    case_id = case_res.json()["case_id"]

    upload_req = {
        "case_id": case_id,
        "file_name": "id_front.png",
        "mime_type": "image/png",
        "file_size_bytes": 10240,
        "sha256_hash": hashlib.sha256(PNG_MAGIC_BYTES).hexdigest(),
    }
    res = client.post(f"/api/v1/cases/{case_id}/evidence/upload-url", json=upload_req, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "upload_url" in data
    assert "token=" in data["upload_url"]
    assert data["bucket"] == "evidence-quarantine"
    assert data["expires_in_seconds"] == 900
    assert data["file_id"] in _MOCK_EVIDENCE_DB


def test_generate_upload_url_unsupported_mime_rejected(client: TestClient, subject_token: str):
    """Unsupported MIME types (e.g. executable/HTML) are rejected with HTTP 422."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    upload_req = {
        "case_id": case_id,
        "file_name": "malicious.exe",
        "mime_type": "application/x-msdownload",
        "file_size_bytes": 4096,
    }
    res = client.post(f"/api/v1/cases/{case_id}/evidence/upload-url", json=upload_req, headers=headers)
    assert res.status_code == 422
    assert "Unsupported MIME type" in get_error_message(res)


def test_generate_upload_url_oversized_rejected(client: TestClient, subject_token: str):
    """Files declared larger than 10MB are rejected with HTTP 413."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    upload_req = {
        "case_id": case_id,
        "file_name": "huge_scan.pdf",
        "mime_type": "application/pdf",
        "file_size_bytes": 15 * 1024 * 1024,  # 15 MB
    }
    res = client.post(f"/api/v1/cases/{case_id}/evidence/upload-url", json=upload_req, headers=headers)
    assert res.status_code == 413
    assert "exceeds maximum allowed limit" in get_error_message(res)


def test_generate_upload_url_cross_user_blocked(client: TestClient, subject_token: str, subject_b_token: str):
    """Subject B cannot request an upload URL for Subject A's verification case (HTTP 403)."""
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_a)
    case_id = case_res.json()["case_id"]

    headers_b = {"Authorization": f"Bearer {subject_b_token}"}
    upload_req = {
        "case_id": case_id,
        "file_name": "injected_doc.png",
        "mime_type": "image/png",
        "file_size_bytes": 1024,
    }
    res = client.post(f"/api/v1/cases/{case_id}/evidence/upload-url", json=upload_req, headers=headers_b)
    assert res.status_code == 403
    assert "Cross-user access denied" in get_error_message(res)


def test_generate_upload_url_unauthenticated_blocked(client: TestClient):
    """Unauthenticated upload URL requests fail closed with HTTP 401."""
    res = client.post(
        "/api/v1/cases/00000000-0000-0000-0000-000000000001/evidence/upload-url",
        json={"case_id": "00000000-0000-0000-0000-000000000001", "file_name": "test.png", "mime_type": "image/png"},
    )
    assert res.status_code == 401


# -----------------------------------------------------------------------------
# 2. Direct Upload & Magic Byte Validation Tests
# -----------------------------------------------------------------------------
def test_direct_upload_valid_png_cleared(client: TestClient, subject_token: str):
    """Direct upload of valid PNG bytes succeeds and auto-clears quarantine."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    files = {"file": ("national_id.png", io.BytesIO(PNG_MAGIC_BYTES), "image/png")}
    res = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["mime_type"] == "image/png"
    assert data["quarantine_status"] == "CLEARED"
    assert data["sha256_hash"] == hashlib.sha256(PNG_MAGIC_BYTES).hexdigest()
    assert data["file_size_bytes"] == len(PNG_MAGIC_BYTES)


def test_direct_upload_valid_jpeg_cleared(client: TestClient, subject_token: str):
    """Direct upload of valid JPEG bytes succeeds and auto-clears quarantine."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_DL_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    files = {"file": ("drivers_license.jpg", io.BytesIO(JPEG_MAGIC_BYTES), "image/jpeg")}
    res = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["mime_type"] == "image/jpeg"
    assert data["quarantine_status"] == "CLEARED"
    assert data["sha256_hash"] == hashlib.sha256(JPEG_MAGIC_BYTES).hexdigest()


def test_direct_upload_valid_pdf_cleared(client: TestClient, subject_token: str):
    """Direct upload of valid PDF document bytes succeeds and auto-clears quarantine."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_PASSPORT_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    files = {"file": ("passport_scan.pdf", io.BytesIO(PDF_MAGIC_BYTES), "application/pdf")}
    res = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["mime_type"] == "application/pdf"
    assert data["quarantine_status"] == "CLEARED"
    assert data["sha256_hash"] == hashlib.sha256(PDF_MAGIC_BYTES).hexdigest()


def test_direct_upload_magic_byte_spoofing_rejected(client: TestClient, subject_token: str):
    """Extension spoofing: plain text disguised as PNG is rejected with HTTP 400."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    fake_png_bytes = b"This is plain text pretending to be a PNG document"
    files = {"file": ("fake_id.png", io.BytesIO(fake_png_bytes), "image/png")}
    res = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files, headers=headers)
    assert res.status_code == 400
    assert "does not match any allowed file signatures" in get_error_message(res)


def test_direct_upload_empty_file_rejected(client: TestClient, subject_token: str):
    """Empty 0-byte file is rejected with HTTP 422."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    files = {"file": ("empty.png", io.BytesIO(b""), "image/png")}
    res = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files, headers=headers)
    assert res.status_code == 422
    assert "cannot be empty" in get_error_message(res)


def test_direct_upload_oversized_file_rejected(client: TestClient, subject_token: str):
    """Payloads exceeding 10MB are rejected with HTTP 413 Payload Too Large."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    # 10 MB + 1024 bytes
    oversized_bytes = b"%PDF-" + b"0" * (10 * 1024 * 1024 + 1024)
    files = {"file": ("giant.pdf", io.BytesIO(oversized_bytes), "application/pdf")}
    res = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files, headers=headers)
    assert res.status_code == 413
    assert "exceeds the maximum limit" in get_error_message(res)


def test_direct_upload_checksum_mismatch_rejected(client: TestClient, subject_token: str):
    """Client providing corrupted/mismatched SHA-256 hash is rejected with HTTP 400."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    bad_checksum = "0000000000000000000000000000000000000000000000000000000000000000"
    files = {"file": ("national_id.png", io.BytesIO(PNG_MAGIC_BYTES), "image/png")}
    data = {"sha256_hash": bad_checksum}
    res = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files, data=data, headers=headers)
    assert res.status_code == 400
    assert "Integrity check failed" in get_error_message(res)


def test_direct_upload_duplicate_idempotency(client: TestClient, subject_token: str):
    """Re-uploading the identical file for the same case safely returns the existing record idempotently."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    files_1 = {"file": ("id.png", io.BytesIO(PNG_MAGIC_BYTES), "image/png")}
    res1 = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files_1, headers=headers)
    assert res1.status_code == 201
    file_id_1 = res1.json()["file_id"]

    # Re-upload identical bytes
    files_2 = {"file": ("id.png", io.BytesIO(PNG_MAGIC_BYTES), "image/png")}
    res2 = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files_2, headers=headers)
    assert res2.status_code == 201
    file_id_2 = res2.json()["file_id"]

    assert file_id_1 == file_id_2


def test_direct_upload_cross_user_blocked(client: TestClient, subject_token: str, subject_b_token: str):
    """Subject B cannot upload evidence directly to Subject A's verification case (HTTP 403)."""
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_a)
    case_id = case_res.json()["case_id"]

    headers_b = {"Authorization": f"Bearer {subject_b_token}"}
    files = {"file": ("hacked.png", io.BytesIO(PNG_MAGIC_BYTES), "image/png")}
    res = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files, headers=headers_b)
    assert res.status_code == 403
    assert "Cross-user access denied" in get_error_message(res)


# -----------------------------------------------------------------------------
# 3. Evidence Listing & Retrieval Tests
# -----------------------------------------------------------------------------
def test_list_and_get_case_evidence(client: TestClient, subject_token: str):
    """Owner can list all evidence files for a case and retrieve metadata."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    # Upload two files
    files_1 = {"file": ("doc1.png", io.BytesIO(PNG_MAGIC_BYTES), "image/png")}
    res1 = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files_1, headers=headers)
    file_id_1 = res1.json()["file_id"]

    files_2 = {"file": ("doc2.pdf", io.BytesIO(PDF_MAGIC_BYTES), "application/pdf")}
    res2 = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files_2, headers=headers)
    file_id_2 = res2.json()["file_id"]

    # List evidence
    list_res = client.get(f"/api/v1/cases/{case_id}/evidence", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 2
    ids = [e["file_id"] for e in list_data["evidence"]]
    assert file_id_1 in ids
    assert file_id_2 in ids

    # Retrieve single record
    get_res = client.get(f"/api/v1/cases/{case_id}/evidence/{file_id_1}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["file_id"] == file_id_1


# -----------------------------------------------------------------------------
# 4. Pre-Signed Download URL Tests & Access Control
# -----------------------------------------------------------------------------
def test_download_url_generation_authorized(client: TestClient, subject_token: str):
    """Case owner can generate short-lived signed download URL for their cleared evidence."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    files = {"file": ("id.png", io.BytesIO(PNG_MAGIC_BYTES), "image/png")}
    upload_res = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files, headers=headers)
    file_id = upload_res.json()["file_id"]

    res = client.get(f"/api/v1/cases/{case_id}/evidence/{file_id}/download-url", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "download_url" in data
    assert "token=" in data["download_url"]
    assert data["expires_in_seconds"] == 900


def test_download_url_cross_user_blocked(client: TestClient, subject_token: str, subject_b_token: str):
    """Subject B cannot obtain download URL for Subject A's evidence (HTTP 403)."""
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_a)
    case_id = case_res.json()["case_id"]

    files = {"file": ("id.png", io.BytesIO(PNG_MAGIC_BYTES), "image/png")}
    upload_res = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files, headers=headers_a)
    file_id = upload_res.json()["file_id"]

    headers_b = {"Authorization": f"Bearer {subject_b_token}"}
    res = client.get(f"/api/v1/cases/{case_id}/evidence/{file_id}/download-url", headers=headers_b)
    assert res.status_code == 403
    assert "Cross-user access denied" in get_error_message(res)


def test_download_url_reviewer_has_access(client: TestClient, subject_token: str, verifier_token: str, admin_token: str):
    """Reviewers and Admins can obtain download URLs across any case's evidence."""
    headers_user = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_user)
    case_id = case_res.json()["case_id"]

    files = {"file": ("doc.pdf", io.BytesIO(PDF_MAGIC_BYTES), "application/pdf")}
    upload_res = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files, headers=headers_user)
    file_id = upload_res.json()["file_id"]

    # Verifier access
    res_verifier = client.get(f"/api/v1/cases/{case_id}/evidence/{file_id}/download-url", headers={"Authorization": f"Bearer {verifier_token}"})
    assert res_verifier.status_code == 200
    assert "download_url" in res_verifier.json()

    # Admin access
    res_admin = client.get(f"/api/v1/cases/{case_id}/evidence/{file_id}/download-url", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert "download_url" in res_admin.json()


def test_download_url_quarantine_rejected_file_blocked_for_subject(client: TestClient, subject_token: str, verifier_token: str):
    """When a file is flagged as REJECTED in quarantine, subject cannot download, but reviewer can."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    files = {"file": ("id.png", io.BytesIO(PNG_MAGIC_BYTES), "image/png")}
    upload_res = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files, headers=headers)
    file_id = upload_res.json()["file_id"]

    # Simulate quarantine marking file as REJECTED
    _MOCK_EVIDENCE_DB[file_id]["quarantine_status"] = "REJECTED"

    # Subject is blocked
    res_subject = client.get(f"/api/v1/cases/{case_id}/evidence/{file_id}/download-url", headers=headers)
    assert res_subject.status_code == 403
    assert "failed quarantine validation" in get_error_message(res_subject)

    # Verifier can still inspect for forensics
    res_verifier = client.get(f"/api/v1/cases/{case_id}/evidence/{file_id}/download-url", headers={"Authorization": f"Bearer {verifier_token}"})
    assert res_verifier.status_code == 200


# -----------------------------------------------------------------------------
# 5. Checksum Verification Endpoint Tests
# -----------------------------------------------------------------------------
def test_verify_evidence_upload_confirmation(client: TestClient, subject_token: str):
    """Post-upload verification confirms matching SHA-256 and clears quarantine."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    files = {"file": ("id.png", io.BytesIO(PNG_MAGIC_BYTES), "image/png")}
    upload_res = client.post(f"/api/v1/cases/{case_id}/evidence/upload", files=files, headers=headers)
    file_id = upload_res.json()["file_id"]
    computed_hash = upload_res.json()["sha256_hash"]

    # Confirm matching checksum
    verify_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/{file_id}/verify",
        json={"sha256_hash": computed_hash},
        headers=headers,
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["sha256_verified"] is True
    assert verify_res.json()["quarantine_status"] == "CLEARED"

    # Confirm mismatched checksum flags as REJECTED
    verify_bad = client.post(
        f"/api/v1/cases/{case_id}/evidence/{file_id}/verify",
        json={"sha256_hash": "deadbeef" * 8},
        headers=headers,
    )
    assert verify_bad.status_code == 200
    assert verify_bad.json()["sha256_verified"] is False
    assert verify_bad.json()["quarantine_status"] == "REJECTED"
