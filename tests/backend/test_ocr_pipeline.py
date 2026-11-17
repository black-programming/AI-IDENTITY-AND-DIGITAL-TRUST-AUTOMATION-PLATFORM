"""Automated tests for Phase 8 — OCR Pipeline, Engine Provenance, Pre-processing, and Synthetic Documents."""

import io
import pytest
from fastapi.testclient import TestClient

from app.services.evidence_service import _MOCK_EVIDENCE_DB
from app.services.synthetic_docs import (
    SYNTHETIC_TEMPLATES,
    WATERMARK_TEXT,
    generate_synthetic_document_image,
)


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
# 1. Synthetic Watermarked Document Generation Tests
# -----------------------------------------------------------------------------
def test_synthetic_document_generator_watermarked():
    """Synthetic generator produces valid PNG bytes with explicit non-PII test watermark."""
    img_bytes, fields, bboxes = generate_synthetic_document_image(
        template_key="SYNTH_NAT_ID_V1",
        format="PNG",
    )
    assert len(img_bytes) > 1000
    assert img_bytes.startswith(b"\x89PNG")
    assert fields["document_number"] == "NAT-98421074"
    assert fields["full_name"] == "Jane Synth Citizen"
    assert "document_number" in bboxes
    assert bboxes["document_number"]["width"] > 0
    assert bboxes["document_number"]["height"] > 0


def test_synthetic_document_generator_templates():
    """Generator supports all identity templates: National ID, Driving Licence, and Passport."""
    for key in ["SYNTH_NAT_ID_V1", "SYNTH_DL_V1", "SYNTH_PASSPORT_V1"]:
        img_bytes, fields, bboxes = generate_synthetic_document_image(template_key=key)
        assert len(img_bytes) > 1000
        assert "document_number" in fields
        assert "full_name" in fields
        assert "expiry_date" in fields


# -----------------------------------------------------------------------------
# 2. OCR Extraction Happy Path Tests
# -----------------------------------------------------------------------------
def test_ocr_extraction_happy_path_national_id(client: TestClient, subject_token: str):
    """OCR extraction on synthetic national ID extracts structured fields with provenance."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    assert case_res.status_code == 201
    case_id = case_res.json()["case_id"]

    # Generate synthetic image and upload
    img_bytes, fields, _ = generate_synthetic_document_image("SYNTH_NAT_ID_V1")
    upload_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload",
        files={"file": ("national_id.png", io.BytesIO(img_bytes), "image/png")},
        headers=headers,
    )
    assert upload_res.status_code == 201
    file_id = upload_res.json()["file_id"]

    # Trigger OCR extraction
    ocr_res = client.post(f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr", headers=headers)
    assert ocr_res.status_code == 200
    data = ocr_res.json()

    assert data["status"] == "SUCCESS"
    assert data["is_conclusive"] is True
    assert data["overall_confidence"] >= 0.85
    assert "ocr_engine" in data
    assert "engine_version" in data

    extracted = data["extracted_fields"]
    assert extracted["document_number"] == "NAT-98421074"
    assert extracted["full_name"] == "Jane Synth Citizen"
    assert extracted["date_of_birth"] == "1988-04-12"
    assert extracted["expiry_date"] == "2030-05-15"

    # Verify field bounding boxes and provenance
    detail = data["fields_detail"]
    assert len(detail) >= 5
    for field in detail:
        assert field["confidence"] > 0.80
        assert field["bounding_box"] is not None
        assert field["bounding_box"]["width"] > 0
        assert field["ocr_engine"] is not None
        assert field["extracted_at"] is not None


def test_ocr_extraction_happy_path_drivers_license(client: TestClient, subject_token: str):
    """OCR extraction on synthetic driver license extracts license fields."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_DL_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    img_bytes, _, _ = generate_synthetic_document_image("SYNTH_DL_V1")
    upload_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload",
        files={"file": ("driver_license.png", io.BytesIO(img_bytes), "image/png")},
        headers=headers,
    )
    file_id = upload_res.json()["file_id"]

    ocr_res = client.post(f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr", headers=headers)
    assert ocr_res.status_code == 200
    data = ocr_res.json()

    assert data["status"] == "SUCCESS"
    extracted = data["extracted_fields"]
    assert extracted["document_number"] == "DL-TN-2021-998811"
    assert extracted["full_name"] == "John Synth Driver"
    assert extracted["vehicle_classes"] == "LMV, MCWG"


def test_ocr_extraction_happy_path_passport(client: TestClient, subject_token: str):
    """OCR extraction on synthetic passport extracts MRZ lines and passport number."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_PASSPORT_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    img_bytes, _, _ = generate_synthetic_document_image("SYNTH_PASSPORT_V1")
    upload_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload",
        files={"file": ("passport.png", io.BytesIO(img_bytes), "image/png")},
        headers=headers,
    )
    file_id = upload_res.json()["file_id"]

    ocr_res = client.post(f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr", headers=headers)
    assert ocr_res.status_code == 200
    data = ocr_res.json()

    assert data["status"] == "SUCCESS"
    extracted = data["extracted_fields"]
    assert extracted["document_number"] == "P9823411"
    assert "mrz_line1" in extracted
    assert "mrz_line2" in extracted


# -----------------------------------------------------------------------------
# 3. Defect & Low Quality Image Tests (FR-05.4)
# -----------------------------------------------------------------------------
def test_ocr_low_resolution_image_inconclusive(client: TestClient, subject_token: str):
    """Low resolution image (<300x200) triggers low confidence and auto-escalates case to Under Review."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    # Generate undersized image: 180x110 px
    low_res_bytes, _, _ = generate_synthetic_document_image(width=180, height=110)
    upload_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload",
        files={"file": ("tiny_id.png", io.BytesIO(low_res_bytes), "image/png")},
        headers=headers,
    )
    file_id = upload_res.json()["file_id"]

    # Explicitly attach low res bytes to mock record
    _MOCK_EVIDENCE_DB[file_id]["raw_bytes"] = low_res_bytes

    ocr_res = client.post(f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr", headers=headers)
    assert ocr_res.status_code == 200
    data = ocr_res.json()

    assert data["is_conclusive"] is False
    assert data["status"] == "INCONCLUSIVE"
    assert data["overall_confidence"] < 0.60
    assert "ERR_LOW_RESOLUTION" in data["reason_codes"]
    assert "DEC_VERIFY_OCR_CONF_LOW" in data["reason_codes"]

    # Verify case status escalated to 'Under Review'
    detail_res = client.get(f"/api/v1/cases/{case_id}", headers=headers)
    assert detail_res.json()["status"] == "Under Review"


def test_ocr_blurry_image_low_confidence(client: TestClient, subject_token: str):
    """Blurry image triggers ERR_BLUR_DETECTED and reduced extraction confidence."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    blurry_bytes, _, _ = generate_synthetic_document_image(blur_radius=5.0)
    upload_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload",
        files={"file": ("blurry_id.png", io.BytesIO(blurry_bytes), "image/png")},
        headers=headers,
    )
    file_id = upload_res.json()["file_id"]
    _MOCK_EVIDENCE_DB[file_id]["raw_bytes"] = blurry_bytes

    ocr_res = client.post(f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr", headers=headers)
    assert ocr_res.status_code == 200
    data = ocr_res.json()

    assert "ERR_BLUR_DETECTED" in data["reason_codes"]
    assert data["overall_confidence"] < 0.85


def test_ocr_rotated_document_auto_corrected(client: TestClient, subject_token: str):
    """Rotated image (height > width) triggers auto-rotation pre-processing."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    # Rotate 90 degrees
    rotated_bytes, _, _ = generate_synthetic_document_image(rotate_degrees=90)
    upload_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload",
        files={"file": ("sideways_id.png", io.BytesIO(rotated_bytes), "image/png")},
        headers=headers,
    )
    file_id = upload_res.json()["file_id"]
    _MOCK_EVIDENCE_DB[file_id]["raw_bytes"] = rotated_bytes

    ocr_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr",
        json={"auto_rotate": True},
        headers=headers,
    )
    assert ocr_res.status_code == 200
    data = ocr_res.json()

    assert "AUTO_ROTATED_90_DEG" in data["reason_codes"]
    assert data["status"] == "SUCCESS"


# -----------------------------------------------------------------------------
# 4. Field Provenance & Aggregated Summary Tests
# -----------------------------------------------------------------------------
def test_get_evidence_ocr_fields_endpoint(client: TestClient, subject_token: str):
    """Endpoint GET /cases/{case_id}/evidence/{file_id}/ocr returns fields with bounding boxes."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    img_bytes, _, _ = generate_synthetic_document_image("SYNTH_NAT_ID_V1")
    upload_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload",
        files={"file": ("national_id.png", io.BytesIO(img_bytes), "image/png")},
        headers=headers,
    )
    file_id = upload_res.json()["file_id"]

    client.post(f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr", headers=headers)

    # Read extracted fields list
    get_res = client.get(f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr", headers=headers)
    assert get_res.status_code == 200
    fields_list = get_res.json()
    assert len(fields_list) >= 5
    assert all("bounding_box" in f for f in fields_list)
    assert all("ocr_engine" in f for f in fields_list)


def test_get_case_ocr_fields_summary_endpoint(client: TestClient, subject_token: str):
    """Endpoint GET /cases/{case_id}/ocr/fields returns aggregated fields summary."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    img_bytes, _, _ = generate_synthetic_document_image("SYNTH_NAT_ID_V1")
    upload_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload",
        files={"file": ("national_id.png", io.BytesIO(img_bytes), "image/png")},
        headers=headers,
    )
    file_id = upload_res.json()["file_id"]

    client.post(f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr", headers=headers)

    summary_res = client.get(f"/api/v1/cases/{case_id}/ocr/fields", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["case_id"] == case_id
    assert summary["total_fields"] >= 5
    assert summary["is_conclusive"] is True
    assert "document_number" in summary["extracted_fields"]


# -----------------------------------------------------------------------------
# 5. Security & Authorization Boundary Tests
# -----------------------------------------------------------------------------
def test_ocr_cross_user_access_blocked(client: TestClient, subject_token: str, subject_b_token: str):
    """Subject B cannot trigger or view OCR extractions on Subject A's case (HTTP 403)."""
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_a)
    case_id = case_res.json()["case_id"]

    img_bytes, _, _ = generate_synthetic_document_image("SYNTH_NAT_ID_V1")
    upload_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload",
        files={"file": ("doc.png", io.BytesIO(img_bytes), "image/png")},
        headers=headers_a,
    )
    file_id = upload_res.json()["file_id"]

    # Subject B attempts to run OCR
    headers_b = {"Authorization": f"Bearer {subject_b_token}"}
    run_res = client.post(f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr", headers=headers_b)
    assert run_res.status_code == 403
    assert "Cross-user access denied" in get_error_message(run_res)

    # Subject B attempts to read OCR summary
    summary_res = client.get(f"/api/v1/cases/{case_id}/ocr/fields", headers=headers_b)
    assert summary_res.status_code == 403
    assert "Cross-user access denied" in get_error_message(summary_res)


def test_ocr_unauthenticated_request_blocked(client: TestClient):
    """Unauthenticated requests to OCR endpoints fail closed with HTTP 401."""
    res = client.post("/api/v1/cases/00000000-0000-0000-0000-000000000001/evidence/some-file/ocr")
    assert res.status_code == 401


def test_synthetic_templates_catalog_endpoint(client: TestClient, subject_token: str):
    """GET /ocr/synthetic-templates returns available non-PII test templates."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    res = client.get("/api/v1/ocr/synthetic-templates", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "SYNTH_NAT_ID_V1" in data["templates"]
    assert "SYNTH_DL_V1" in data["templates"]
    assert "SYNTH_PASSPORT_V1" in data["templates"]
