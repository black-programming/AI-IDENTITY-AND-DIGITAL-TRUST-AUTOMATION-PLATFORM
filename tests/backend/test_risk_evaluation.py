"""Unit and Integration Tests for Phase 16 AI/ML Risk Evaluation."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.services.risk_evaluation_service import (
    generate_synthetic_dataset,
    RuleBasedRiskBaseline,
    CalibratedMLRiskClassifier,
    extract_feature_vector,
)


# -----------------------------------------------------------------------------
# 1. Dataset & Baseline Unit Tests
# -----------------------------------------------------------------------------
def test_synthetic_dataset_generation():
    """Synthetic dataset generates reproducible ground truth with documented slices."""
    dataset = generate_synthetic_dataset(num_samples=200, seed=42)
    assert len(dataset) == 200

    labels = [d["label"] for d in dataset]
    genuine_count = labels.count(0)
    anomaly_count = labels.count(1)

    assert genuine_count == 120  # 60%
    assert anomaly_count == 80   # 40%

    # Verify slices
    doc_types = {d["doc_type"] for d in dataset}
    assert doc_types == {"NATIONAL_ID", "DRIVERS_LICENSE", "PASSPORT"}

    qualities = {d["quality"] for d in dataset}
    assert qualities == {"HIGH_RES_CLEAN", "LOW_RES", "BLURRY", "ROTATED"}

    age_bands = {d["age_band"] for d in dataset}
    assert "UNDER_18" in age_bands and "AGE_18_25" in age_bands and "AGE_26_60" in age_bands


def test_rule_baseline_accuracy_and_metrics():
    """Rule-based baseline scores deterministic fraud indicators cleanly."""
    dataset = generate_synthetic_dataset(num_samples=200, seed=42)

    # Test clean sample
    clean_sample = next(d for d in dataset if d["anomaly_type"] == "NONE_GENUINE")
    score, pred = RuleBasedRiskBaseline.predict_sample(clean_sample)
    assert score <= 0.20
    assert pred == 0

    # Test expired sample
    expired_sample = next(d for d in dataset if d["anomaly_type"] == "EXPIRED")
    score, pred = RuleBasedRiskBaseline.predict_sample(expired_sample)
    assert score == 1.0
    assert pred == 1


# -----------------------------------------------------------------------------
# 2. ML Classifier & Calibration Unit Tests
# -----------------------------------------------------------------------------
def test_ml_classifier_training_and_calibration():
    """Calibrated ML classifier outputs probabilities in [0.0, 1.0] with feature explainability."""
    clf = CalibratedMLRiskClassifier()
    assert clf.model is not None

    sample_dict = {
        "ocr_confidence": 0.95,
        "mrz_valid": True,
        "days_expiry": 450,
        "subject_age": 30,
        "resolution_ratio": 1.0,
        "blur_metric": 80.0,
        "field_mismatches": 0,
        "doc_type": "PASSPORT",
    }
    f_vec = extract_feature_vector(sample_dict)
    risk_score, contributions = clf.predict_risk(f_vec)

    assert 0.0 <= risk_score <= 1.0
    assert risk_score < 0.30  # Clean passport should have low risk
    assert len(contributions) > 0


# -----------------------------------------------------------------------------
# 3. API Risk Evaluation & Fallback Tests
# -----------------------------------------------------------------------------
def test_predict_risk_happy_path_genuine(client: TestClient, subject_token: str):
    """Genuine, sharp document evaluates to LOW risk with APPROVE_ELIGIBLE recommendation."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    payload = {
        "ocr_confidence_score": 0.96,
        "mrz_checksum_valid": True,
        "days_until_expiry": 500,
        "subject_age": 32,
        "document_resolution_ratio": 1.0,
        "image_blur_metric": 85.0,
        "num_field_mismatches": 0,
        "document_type": "PASSPORT",
    }

    res = client.post("/api/v1/risk/predict", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["risk_score"] < 0.25
    assert data["risk_tier"] == "LOW"
    assert data["recommendation"] == "APPROVE_ELIGIBLE"
    assert data["is_safe_fallback_triggered"] is False
    assert len(data["feature_contributions"]) > 0


def test_predict_risk_tampered_document_triggers_fallback(client: TestClient, subject_token: str):
    """Tampered document with failed checksum and field mismatches triggers high risk and review fallback."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    payload = {
        "ocr_confidence_score": 0.55,
        "mrz_checksum_valid": False,  # Tampered MRZ
        "days_until_expiry": -30,      # Expired
        "subject_age": 16,             # Underage
        "document_resolution_ratio": 0.5,
        "image_blur_metric": 20.0,
        "num_field_mismatches": 3,
        "document_type": "NATIONAL_ID",
    }

    res = client.post("/api/v1/risk/predict", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["risk_score"] >= 0.70
    assert data["risk_tier"] in ("HIGH", "CRITICAL")
    assert data["is_safe_fallback_triggered"] is True
    assert data["recommendation"] in ("STEP_UP_MFA", "ROUTE_TO_HUMAN_REVIEW")


def test_safe_fallback_on_low_confidence_image(client: TestClient, subject_token: str):
    """Severe blur or low OCR confidence automatically triggers safe human review fallback."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    payload = {
        "ocr_confidence_score": 0.32,  # Very low OCR confidence
        "mrz_checksum_valid": True,
        "days_until_expiry": 200,
        "subject_age": 40,
        "document_resolution_ratio": 1.0,
        "image_blur_metric": 10.0,     # Very blurry
        "num_field_mismatches": 0,
        "document_type": "DRIVERS_LICENSE",
    }

    res = client.post("/api/v1/risk/predict", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["is_safe_fallback_triggered"] is True
    assert data["recommendation"] == "ROUTE_TO_HUMAN_REVIEW"


# -----------------------------------------------------------------------------
# 4. Benchmark, Model Card & Dataset Card Tests
# -----------------------------------------------------------------------------
def test_benchmark_endpoint_metrics_and_subgroups(client: TestClient, auditor_token: str):
    """Benchmark endpoint provides confusion matrices, calibration Brier scores, and subgroup slices."""
    headers = {"Authorization": f"Bearer {auditor_token}"}

    res = client.get("/api/v1/risk/benchmark", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "rule_baseline_metrics" in data
    assert "ml_model_metrics" in data
    assert "confusion_matrices" in data
    assert "subgroup_comparisons" in data
    assert "calibration_metrics" in data

    # Calibration comparison: ML Brier score is documented
    assert data["calibration_metrics"]["brier_score_ml"] >= 0.0

    # Subgroup comparisons include document_type and image_quality
    dimensions = {s["subgroup_dimension"] for s in data["subgroup_comparisons"]}
    assert "document_type" in dimensions
    assert "image_quality" in dimensions
    assert "age_band" in dimensions


def test_dataset_card_endpoint(client: TestClient):
    """Dataset Card endpoint returns total samples, slice distributions, and zero-PII safeguards."""
    res = client.get("/api/v1/risk/dataset-card")
    assert res.status_code == 200
    data = res.json()

    assert data["total_samples"] == 200
    assert "GENUINE" in data["class_distribution"]
    assert "TAMPERED" in data["class_distribution"]
    assert "Zero real PII" in data["pii_safeguards"]


def test_model_card_endpoint(client: TestClient):
    """Model Card endpoint documents intended use, ethical considerations, and caveats."""
    res = client.get("/api/v1/risk/model-card")
    assert res.status_code == 200
    data = res.json()

    assert data["model_name"] == "ExplainableIdentityRiskScorer"
    assert "human review" in data["intended_use"].lower()
    assert len(data["ethical_considerations"]) > 0
    assert len(data["caveats_and_limitations"]) > 0


def test_evaluate_case_risk_integration(client: TestClient, subject_token: str):
    """Evaluating risk for an existing case returns risk score and logs audit event."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    # 1. Create a case
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    # 2. Evaluate risk
    risk_res = client.post(f"/api/v1/risk/evaluate-case/{case_id}", headers=headers)
    assert risk_res.status_code == 200
    data = risk_res.json()

    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["risk_tier"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert data["recommendation"] is not None
