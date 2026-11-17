"""Comprehensive Tests for Aadhaar Card Entity Detection, OCR Extraction, Verhoeff Checksum & Privacy Masking."""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.aadhaar_service import (
    AadhaarEntityDetectionService,
    calculate_verhoeff_checksum,
    clean_aadhaar_digits,
    generate_verhoeff_check_digit,
    mask_aadhaar_number,
    validate_aadhaar_number,
)
from app.services.synthetic_docs import generate_synthetic_document_image
from app.services.validation_engine import ValidationEngine

client = TestClient(app)


# -----------------------------------------------------------------------------
# 1. Verhoeff Checksum Algorithm Tests
# -----------------------------------------------------------------------------
def test_verhoeff_check_digit_generation():
    """Verify that Verhoeff check digit generation is deterministic and valid."""
    prefix = "36759832415"
    check_digit = generate_verhoeff_check_digit(prefix)
    assert 0 <= check_digit <= 9
    
    full_number = prefix + str(check_digit)
    assert calculate_verhoeff_checksum(full_number) is True


def test_verhoeff_checksum_catches_transposition_error():
    """Verhoeff algorithm mathematically detects adjacent transposition errors."""
    prefix = "49281736504"
    check_digit = generate_verhoeff_check_digit(prefix)
    valid_number = prefix + str(check_digit)
    assert calculate_verhoeff_checksum(valid_number) is True

    # Swap adjacent digits (e.g. 28 -> 82)
    transposed = "49821736504" + str(check_digit)
    assert calculate_verhoeff_checksum(transposed) is False


def test_verhoeff_checksum_catches_single_digit_substitution():
    """Verhoeff algorithm catches any single digit modification."""
    prefix = "51928374610"
    chk = generate_verhoeff_check_digit(prefix)
    valid = prefix + str(chk)
    assert calculate_verhoeff_checksum(valid) is True

    # Replace last prefix digit '0' with '9'
    altered = "51928374619" + str(chk)
    assert calculate_verhoeff_checksum(altered) is False


def test_validate_aadhaar_number_structural_rules():
    """Verify non-zero/non-one initial digit, 12-digit length, and empty inputs."""
    # Empty
    res_empty = validate_aadhaar_number("")
    assert res_empty["is_valid"] is False
    assert res_empty["error_code"] == "ERR_AADHAAR_EMPTY"

    # Invalid length (10 digits)
    res_short = validate_aadhaar_number("2345678901")
    assert res_short["is_valid"] is False
    assert res_short["error_code"] == "ERR_AADHAAR_INVALID_LENGTH"

    # Starts with 0
    prefix_0 = "01234567890"
    chk_0 = generate_verhoeff_check_digit(prefix_0)
    res_0 = validate_aadhaar_number(prefix_0 + str(chk_0))
    assert res_0["is_valid"] is False
    assert res_0["error_code"] == "ERR_AADHAAR_INVALID_FIRST_DIGIT"

    # Starts with 1
    prefix_1 = "11234567890"
    chk_1 = generate_verhoeff_check_digit(prefix_1)
    res_1 = validate_aadhaar_number(prefix_1 + str(chk_1))
    assert res_1["is_valid"] is False
    assert res_1["error_code"] == "ERR_AADHAAR_INVALID_FIRST_DIGIT"

    # Valid starting with 3
    valid_num = "3675 9832 4152"
    res_valid = validate_aadhaar_number(valid_num)
    assert res_valid["is_valid"] is True
    assert res_valid["error_code"] is None
    assert res_valid["masked_number"] == "XXXX XXXX 4152"


# -----------------------------------------------------------------------------
# 2. UIDAI Privacy Masking Tests
# -----------------------------------------------------------------------------
def test_aadhaar_privacy_masking():
    """Verify first 8 digits are replaced with 'X's, retaining only last 4 digits."""
    # With spaces
    assert mask_aadhaar_number("3675 9832 4152") == "XXXX XXXX 4152"
    # With hyphens
    assert mask_aadhaar_number("3675-9832-4152") == "XXXX XXXX 4152"
    # Unformatted continuous
    assert mask_aadhaar_number("367598324152") == "XXXX XXXX 4152"
    # Custom delimiter
    assert mask_aadhaar_number("367598324152", delimiter="-") == "XXXX-XXXX-4152"


# -----------------------------------------------------------------------------
# 3. Synthetic Aadhaar Generation & Entity Detection Tests
# -----------------------------------------------------------------------------
def test_synthetic_aadhaar_generation():
    """Verify generation of synthetic watermarked Aadhaar card image."""
    img_bytes, meta, bboxes = generate_synthetic_document_image("SYNTH_AADHAAR_V1")
    assert len(img_bytes) > 1000
    assert meta["country"] == "IND"
    assert "document_number" in meta
    assert calculate_verhoeff_checksum(meta["document_number"]) is True


def test_aadhaar_entity_detection_and_extraction():
    """Verify detection of entities (name, dob, address, aadhar_number) and OCR parsing."""
    img_bytes, _, _ = generate_synthetic_document_image("SYNTH_AADHAAR_V1")
    res = AadhaarEntityDetectionService.detect_and_extract(
        image_bytes=img_bytes,
        case_id="case-test-aadhaar-1",
    )

    assert res["status"] == "SUCCESS"
    assert res["verhoeff_valid"] is True
    assert res["masked_number"] == "XXXX XXXX 4152"
    assert len(res["bounding_boxes"]) >= 4

    entities = res["detected_entities"]
    assert "name" in entities
    assert "dob" in entities
    assert "address" in entities
    assert "aadhar_number" in entities


# -----------------------------------------------------------------------------
# 4. Validation Engine (VAL-AADHAAR-VERHOEFF) Tests
# -----------------------------------------------------------------------------
def test_validation_engine_aadhaar_valid():
    """ValidationEngine should successfully pass valid Aadhaar claims."""
    extracted = {
        "document_number": "3675 9832 4152",
        "full_name": "Aarav Sharma",
        "date_of_birth": "1994-08-15",
    }
    val_res = ValidationEngine.validate(
        case_id="case-101",
        claim_type="AADHAAR_CARD",
        extracted_fields=extracted,
    )

    assert val_res.validation_passed is True
    assert val_res.overall_outcome == "PASS"
    verhoeff_rule = next((r for r in val_res.rule_results if r.rule_id == "VAL-AADHAAR-VERHOEFF"), None)
    assert verhoeff_rule is not None
    assert verhoeff_rule.passed is True


def test_validation_engine_aadhaar_invalid_checksum():
    """ValidationEngine should fail Aadhaar claims with corrupted check digits."""
    extracted = {
        "document_number": "3675 9832 4159",  # Last digit altered
        "full_name": "Aarav Sharma",
        "date_of_birth": "1994-08-15",
    }
    val_res = ValidationEngine.validate(
        case_id="case-102",
        claim_type="AADHAAR_CARD",
        extracted_fields=extracted,
    )

    assert val_res.validation_passed is False
    assert val_res.overall_outcome == "FAIL"
    assert "FLAG_INVALID_AADHAAR_CHECKSUM" in val_res.flags
    assert "ERR_AADHAAR_CHECKSUM_FAILED" in val_res.reason_codes


# -----------------------------------------------------------------------------
# 5. REST API Endpoints Tests
# -----------------------------------------------------------------------------
def test_api_aadhaar_validate_number_valid():
    """Test POST /api/v1/aadhaar/validate-number with valid input."""
    response = client.post(
        "/api/v1/aadhaar/validate-number",
        json={"aadhar_number": "3675 9832 4152"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["masked_number"] == "XXXX XXXX 4152"
    assert len(data["sha256_hash"]) == 64


def test_api_aadhaar_validate_number_invalid():
    """Test POST /api/v1/aadhaar/validate-number with invalid input."""
    response = client.post(
        "/api/v1/aadhaar/validate-number",
        json={"aadhar_number": "1234 5678 9012"},  # Starts with 1
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert data["error_code"] == "ERR_AADHAAR_INVALID_FIRST_DIGIT"


def test_api_aadhaar_detect_and_extract_synthetic():
    """Test POST /api/v1/aadhaar/detect-and-extract default synthetic processing."""
    response = client.post("/api/v1/aadhaar/detect-and-extract")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["verhoeff_valid"] is True
    assert data["masked_number"] == "XXXX XXXX 4152"
    assert len(data["bounding_boxes"]) >= 4


def test_api_aadhaar_detect_and_extract_with_file_upload():
    """Test POST /api/v1/aadhaar/detect-and-extract with multipart file upload."""
    img_bytes, _, _ = generate_synthetic_document_image("SYNTH_AADHAAR_V1")
    files = {"file": ("aadhaar_sample.png", img_bytes, "image/png")}
    response = client.post("/api/v1/aadhaar/detect-and-extract", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["extracted_fields"]["full_name"] == "Aarav Sharma"


def test_api_aadhaar_sample_image():
    """Test GET /api/v1/aadhaar/sample-image returns PNG image bytes."""
    response = client.get("/api/v1/aadhaar/sample-image")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 1000
