"""Comprehensive Tests for PAN Card Entity Detection, OCR Extraction, Regulatory Validation & Masking."""

import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.pancard_service import (
    PANCardEntityDetectionService,
    clean_pan_string,
    mask_pan_number,
    validate_pan_number,
)
from app.services.synthetic_docs import generate_synthetic_document_image
from app.services.validation_engine import ValidationEngine

client = TestClient(app)


# -----------------------------------------------------------------------------
# 1. PAN Structural & Regulatory Validation Tests
# -----------------------------------------------------------------------------
def test_pan_regulatory_validation_individual():
    """Verify standard individual PAN (4th letter 'P')."""
    res = validate_pan_number("ABCPS1234F", applicant_surname="Sharma")
    assert res["is_valid"] is True
    assert res["error_code"] is None
    assert res["holder_type_code"] == "P"
    assert "Individual" in res["holder_type_description"]
    assert res["surname_match"] is True
    assert res["masked_number"] == "XXXXX1234F"


def test_pan_regulatory_validation_corporate_and_trust():
    """Verify company ('C') and trust ('T') PAN types."""
    # Company
    res_corp = validate_pan_number("AABCA1234C")
    assert res_corp["is_valid"] is True
    assert res_corp["holder_type_code"] == "C"
    assert "Company" in res_corp["holder_type_description"]

    # Trust
    res_trust = validate_pan_number("AAATT9999T")
    assert res_trust["is_valid"] is True
    assert res_trust["holder_type_code"] == "T"
    assert "Trust" in res_trust["holder_type_description"]


def test_pan_surname_mismatch_detected():
    """Verify that a discrepancy between PAN 5th char and surname initial is detected."""
    res = validate_pan_number("ABCPS1234F", applicant_surname="Gupta")
    assert res["is_valid"] is True  # Format is valid
    assert res["surname_match"] is False  # 'S' != 'G'


def test_pan_invalid_format_and_empty():
    """Verify format rejections for incorrect length, invalid entity chars, or empty values."""
    # Empty
    res_empty = validate_pan_number("")
    assert res_empty["is_valid"] is False
    assert res_empty["error_code"] == "ERR_PAN_EMPTY"

    # Too short
    res_short = validate_pan_number("ABCP1234")
    assert res_short["is_valid"] is False
    assert res_short["error_code"] == "ERR_PAN_INVALID_LENGTH"

    # Invalid entity character (e.g. 'Z' is not a valid 4th char)
    res_invalid_entity = validate_pan_number("ABCZS1234F")
    assert res_invalid_entity["is_valid"] is False
    assert res_invalid_entity["error_code"] == "ERR_PAN_FORMAT_MISMATCH"


# -----------------------------------------------------------------------------
# 2. Privacy Masking Tests
# -----------------------------------------------------------------------------
def test_pan_privacy_masking():
    """Verify first 5 characters are masked, preserving the last 5."""
    assert mask_pan_number("ABCPS1234F") == "XXXXX1234F"
    assert mask_pan_number("a b c p s 1 2 3 4 f") == "XXXXX1234F"


# -----------------------------------------------------------------------------
# 3. Synthetic PAN Generation & Entity Detection Tests
# -----------------------------------------------------------------------------
def test_synthetic_pan_generation():
    """Verify generation of synthetic watermarked PAN card image."""
    img_bytes, meta, bboxes = generate_synthetic_document_image("SYNTH_PAN_V1")
    assert len(img_bytes) > 1000
    assert meta["country"] == "IND"
    assert "document_number" in meta
    assert meta["document_number"] == "ABCPS1234F"


def test_pan_entity_detection_and_extraction():
    """Verify detection of entities (pan_number, name, father_name, dob) and OCR parsing."""
    img_bytes, _, _ = generate_synthetic_document_image("SYNTH_PAN_V1")
    res = PANCardEntityDetectionService.detect_and_extract(
        image_bytes=img_bytes,
        case_id="case-test-pan-1",
        applicant_surname="Sharma",
    )

    assert res["status"] == "SUCCESS"
    assert res["pan_valid"] is True
    assert res["masked_number"] == "XXXXX1234F"
    assert len(res["bounding_boxes"]) >= 4

    entities = res["detected_entities"]
    assert "name" in entities
    assert "father_name" in entities
    assert "dob" in entities
    assert "pan_number" in entities


# -----------------------------------------------------------------------------
# 4. Validation Engine (VAL-PAN-FORMAT) Tests
# -----------------------------------------------------------------------------
def test_validation_engine_pan_valid():
    """ValidationEngine should successfully pass valid PAN claims."""
    extracted = {
        "document_number": "ABCPS1234F",
        "full_name": "Aarav Sharma",
        "date_of_birth": "1994-08-15",
    }
    val_res = ValidationEngine.validate(
        case_id="case-pan-101",
        claim_type="PAN_CARD",
        extracted_fields=extracted,
        user_profile={"full_name": "Aarav Sharma"},
    )

    assert val_res.validation_passed is True
    assert val_res.overall_outcome == "PASS"
    pan_rule = next((r for r in val_res.rule_results if r.rule_id == "VAL-PAN-FORMAT"), None)
    assert pan_rule is not None
    assert pan_rule.passed is True


def test_validation_engine_pan_invalid_format():
    """ValidationEngine should fail PAN claims with corrupted format."""
    extracted = {
        "document_number": "ABC12345",  # Malformed PAN
        "full_name": "Aarav Sharma",
        "date_of_birth": "1994-08-15",
    }
    val_res = ValidationEngine.validate(
        case_id="case-pan-102",
        claim_type="PAN_CARD",
        extracted_fields=extracted,
    )

    assert val_res.validation_passed is False
    assert val_res.overall_outcome == "FAIL"
    assert "FLAG_INVALID_PAN_STRUCTURE" in val_res.flags


# -----------------------------------------------------------------------------
# 5. REST API Endpoints Tests
# -----------------------------------------------------------------------------
def test_api_pan_validate_number_valid():
    """Test POST /api/v1/pancard/validate-number with valid input."""
    response = client.post(
        "/api/v1/pancard/validate-number",
        json={"pan_number": "ABCPS1234F", "applicant_surname": "Sharma"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["holder_type_code"] == "P"
    assert data["surname_match"] is True
    assert data["masked_number"] == "XXXXX1234F"


def test_api_pan_validate_number_invalid():
    """Test POST /api/v1/pancard/validate-number with invalid input."""
    response = client.post(
        "/api/v1/pancard/validate-number",
        json={"pan_number": "INVALID_PAN"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert data["error_code"] == "ERR_PAN_INVALID_LENGTH"


def test_api_pan_detect_and_extract_synthetic():
    """Test POST /api/v1/pancard/detect-and-extract default synthetic processing."""
    response = client.post("/api/v1/pancard/detect-and-extract")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["pan_valid"] is True
    assert data["masked_number"] == "XXXXX1234F"
    assert len(data["bounding_boxes"]) >= 4


def test_api_pan_detect_and_extract_with_file_upload():
    """Test POST /api/v1/pancard/detect-and-extract with multipart file upload."""
    img_bytes, _, _ = generate_synthetic_document_image("SYNTH_PAN_V1")
    files = {"file": ("pan_sample.png", img_bytes, "image/png")}
    response = client.post("/api/v1/pancard/detect-and-extract", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["extracted_fields"]["document_number"] == "ABCPS1234F"


def test_api_pan_sample_image():
    """Test GET /api/v1/pancard/sample-image returns PNG image bytes."""
    response = client.get("/api/v1/pancard/sample-image")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 1000
