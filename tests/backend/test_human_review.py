"""Automated tests for Phase 10 — Human Reviewer Workbench, Queue, Field Corrections, and Decision Recording."""

import io
import pytest
from fastapi.testclient import TestClient

from app.services.evidence_service import _MOCK_EVIDENCE_DB
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
# 1. Reviewer Queue Access & Priority Ordering
# -----------------------------------------------------------------------------
def test_get_review_queue_authorized(client: TestClient, verifier_token: str, admin_token: str):
    """Reviewers and Sys Admins can fetch pending cases queue sorted by priority."""
    headers_v = {"Authorization": f"Bearer {verifier_token}"}
    res_v = client.get("/api/v1/review/queue", headers=headers_v)
    assert res_v.status_code == 200
    data_v = res_v.json()
    assert "pending_cases" in data_v
    assert "queue_length" in data_v
    assert data_v["queue_length"] >= 1

    # Verify Sys Admin also has access
    headers_a = {"Authorization": f"Bearer {admin_token}"}
    res_a = client.get("/api/v1/review/queue", headers=headers_a)
    assert res_a.status_code == 200


def test_get_review_queue_unauthorized_blocked(client: TestClient, subject_token: str):
    """Subjects are strictly blocked from accessing the reviewer queue (HTTP 403)."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    res = client.get("/api/v1/review/queue", headers=headers)
    assert res.status_code == 403
    assert "not authorized" in get_error_message(res)


# -----------------------------------------------------------------------------
# 2. Side-by-Side Reviewer Workbench Inspection
# -----------------------------------------------------------------------------
def test_review_workbench_data_inspection(client: TestClient, subject_token: str, verifier_token: str):
    """Reviewer can fetch complete workbench bundle with evidence URLs, fields, bounding boxes, and validation report."""
    headers_sub = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_sub)
    case_id = case_res.json()["case_id"]

    # Upload evidence and run OCR
    img_bytes, _, _ = generate_synthetic_document_image("SYNTH_NAT_ID_V1")
    upload_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload",
        files={"file": ("id.png", io.BytesIO(img_bytes), "image/png")},
        headers=headers_sub,
    )
    file_id = upload_res.json()["file_id"]
    client.post(f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr", headers=headers_sub)
    client.post(f"/api/v1/cases/{case_id}/validate", json={}, headers=headers_sub)

    # Reviewer inspects workbench
    headers_v = {"Authorization": f"Bearer {verifier_token}"}
    bench_res = client.get(f"/api/v1/review/cases/{case_id}/workbench", headers=headers_v)
    assert bench_res.status_code == 200
    data = bench_res.json()

    assert data["case_id"] == case_id
    assert len(data["evidence"]) >= 1
    assert data["evidence"][0]["download_url"] is not None
    assert "document_number" in data["extracted_fields"]
    assert len(data["fields_detail"]) >= 5
    assert data["validation_report"] is not None
    assert "ALLOW" in data["permitted_decisions"]


def test_workbench_unauthorized_for_subject(client: TestClient, subject_token: str):
    """Subject cannot inspect reviewer workbench (HTTP 403)."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    res = client.get(f"/api/v1/review/cases/{case_id}/workbench", headers=headers)
    assert res.status_code == 403


# -----------------------------------------------------------------------------
# 3. Field Corrections with Audit Trail
# -----------------------------------------------------------------------------
def test_apply_field_corrections_with_audit(client: TestClient, subject_token: str, verifier_token: str):
    """Reviewer field correction updates extracted field and creates immutable audit record."""
    headers_sub = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_sub)
    case_id = case_res.json()["case_id"]

    # Upload evidence and run OCR
    img_bytes, _, _ = generate_synthetic_document_image("SYNTH_NAT_ID_V1")
    upload_res = client.post(
        f"/api/v1/cases/{case_id}/evidence/upload",
        files={"file": ("id.png", io.BytesIO(img_bytes), "image/png")},
        headers=headers_sub,
    )
    file_id = upload_res.json()["file_id"]
    client.post(f"/api/v1/cases/{case_id}/evidence/{file_id}/ocr", headers=headers_sub)

    # Reviewer applies correction
    headers_v = {"Authorization": f"Bearer {verifier_token}"}
    correction_payload = {
        "corrections": [
            {
                "field_key": "full_name",
                "corrected_value": "Jane Synthetic Citizen-Smith",
                "justification": "OCR truncated hyphenated surname; corrected per physical document VIZ",
            }
        ]
    }
    corr_res = client.post(f"/api/v1/review/cases/{case_id}/corrections", json=correction_payload, headers=headers_v)
    assert corr_res.status_code == 200
    corr_data = corr_res.json()
    assert corr_data["updated_fields"]["full_name"] == "Jane Synthetic Citizen-Smith"
    assert len(corr_data["corrections_applied"]) == 1

    # Verify audit record appears in workbench corrections history
    bench_data = client.get(f"/api/v1/review/cases/{case_id}/workbench", headers=headers_v).json()
    assert len(bench_data["corrections_history"]) >= 1
    assert bench_data["corrections_history"][0]["corrected_value"] == "Jane Synthetic Citizen-Smith"

    # Verify timeline event logged
    case_data = client.get(f"/api/v1/cases/{case_id}", headers=headers_v).json()
    timeline_comments = [e["comment"] for e in case_data["timeline"]]
    assert any("Reviewer corrected field 'full_name'" in c for c in timeline_comments)


def test_apply_field_corrections_by_subject_blocked(client: TestClient, subject_token: str):
    """Subject cannot call corrections endpoint (HTTP 403)."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    res = client.post(
        f"/api/v1/review/cases/{case_id}/corrections",
        json={"corrections": [{"field_key": "full_name", "corrected_value": "Hacked", "justification": "None"}]},
        headers=headers,
    )
    assert res.status_code == 403


# -----------------------------------------------------------------------------
# 4. Request Additional Evidence
# -----------------------------------------------------------------------------
def test_request_additional_evidence_success(client: TestClient, subject_token: str, verifier_token: str):
    """Reviewer can flag case as Action Required with actionable guidance for subject."""
    headers_sub = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_sub)
    case_id = case_res.json()["case_id"]

    # Reviewer requests additional evidence
    headers_v = {"Authorization": f"Bearer {verifier_token}"}
    req_payload = {
        "reason_code": "ERR_BLUR_DETECTED",
        "guidance": "Please upload a sharper, glare-free photo of your National ID under good lighting.",
    }
    req_res = client.post(f"/api/v1/review/cases/{case_id}/request-evidence", json=req_payload, headers=headers_v)
    assert req_res.status_code == 200
    assert req_res.json()["status"] == "Action Required"

    # Verify case status updated to Action Required
    case_data = client.get(f"/api/v1/cases/{case_id}", headers=headers_sub).json()
    assert case_data["status"] == "Action Required"


# -----------------------------------------------------------------------------
# 5. Manual Decision Recording
# -----------------------------------------------------------------------------
def test_submit_decision_allow_transitions_to_verified(client: TestClient, subject_token: str, verifier_token: str):
    """Reviewer decision ALLOW transitions case to Verified."""
    headers_sub = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_sub)
    case_id = case_res.json()["case_id"]

    headers_v = {"Authorization": f"Bearer {verifier_token}"}
    dec_payload = {
        "decision": "ALLOW",
        "reason_code": "DEC_ALLOW_MANUAL_VERIFIED",
        "notes": "All identity markers and physical security holograms verified manually.",
    }
    dec_res = client.post(f"/api/v1/review/cases/{case_id}/decision", json=dec_payload, headers=headers_v)
    assert dec_res.status_code == 200
    assert dec_res.json()["new_status"] == "Verified"

    case_data = client.get(f"/api/v1/cases/{case_id}", headers=headers_sub).json()
    assert case_data["status"] == "Verified"
    assert case_data["current_decision"] == "ALLOW"


def test_submit_decision_block_transitions_to_rejected(client: TestClient, subject_token: str, verifier_token: str):
    """Reviewer decision BLOCK transitions case to Rejected."""
    headers_sub = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_sub)
    case_id = case_res.json()["case_id"]

    headers_v = {"Authorization": f"Bearer {verifier_token}"}
    dec_payload = {
        "decision": "BLOCK",
        "reason_code": "DEC_BLOCK_MANUAL_FRAUD_FLAG",
        "notes": "Altered font identified on document number.",
    }
    dec_res = client.post(f"/api/v1/review/cases/{case_id}/decision", json=dec_payload, headers=headers_v)
    assert dec_res.status_code == 200
    assert dec_res.json()["new_status"] == "Rejected"

    case_data = client.get(f"/api/v1/cases/{case_id}", headers=headers_sub).json()
    assert case_data["status"] == "Rejected"
    assert case_data["current_decision"] == "BLOCK"


def test_submit_decision_restrict_transitions_to_restricted(client: TestClient, subject_token: str, verifier_token: str):
    """Reviewer decision RESTRICT transitions case to Restricted."""
    headers_sub = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_sub)
    case_id = case_res.json()["case_id"]

    headers_v = {"Authorization": f"Bearer {verifier_token}"}
    dec_payload = {
        "decision": "RESTRICT",
        "reason_code": "DEC_RESTRICT_PARTIAL_MATCH",
        "notes": "Secondary address unverified; granting restricted tier only.",
    }
    dec_res = client.post(f"/api/v1/review/cases/{case_id}/decision", json=dec_payload, headers=headers_v)
    assert dec_res.status_code == 200
    assert dec_res.json()["new_status"] == "Restricted"


def test_submit_decision_on_terminal_case_rejected(client: TestClient, subject_token: str, verifier_token: str):
    """Cannot record a manual decision on an already terminal case (HTTP 400)."""
    headers_sub = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_sub)
    case_id = case_res.json()["case_id"]

    headers_v = {"Authorization": f"Bearer {verifier_token}"}
    # First decision sets to Verified
    client.post(
        f"/api/v1/review/cases/{case_id}/decision",
        json={"decision": "ALLOW", "reason_code": "DEC_ALLOW_MANUAL_VERIFIED"},
        headers=headers_v,
    )

    # Second decision attempt must be rejected
    res2 = client.post(
        f"/api/v1/review/cases/{case_id}/decision",
        json={"decision": "BLOCK", "reason_code": "DEC_BLOCK_MANUAL_FRAUD_FLAG"},
        headers=headers_v,
    )
    assert res2.status_code == 400
    assert "Cannot record decision on terminal case" in get_error_message(res2)


def test_submit_decision_by_subject_blocked(client: TestClient, subject_token: str):
    """Subject cannot record reviewer decisions (HTTP 403)."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = case_res.json()["case_id"]

    res = client.post(
        f"/api/v1/review/cases/{case_id}/decision",
        json={"decision": "ALLOW", "reason_code": "DEC_ALLOW_MANUAL_VERIFIED"},
        headers=headers,
    )
    assert res.status_code == 403


def test_submit_decision_with_corrections_bundled(client: TestClient, subject_token: str, verifier_token: str):
    """Reviewer can bundle corrections with the final manual decision atomically."""
    headers_sub = {"Authorization": f"Bearer {subject_token}"}
    case_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_sub)
    case_id = case_res.json()["case_id"]

    headers_v = {"Authorization": f"Bearer {verifier_token}"}
    dec_payload = {
        "decision": "ALLOW",
        "reason_code": "DEC_ALLOW_MANUAL_VERIFIED",
        "notes": "Verified after manual spelling fix.",
        "corrections": [
            {
                "field_key": "full_name",
                "corrected_value": "Jane S. Citizen",
                "justification": "Spelling normalized",
            }
        ],
    }
    res = client.post(f"/api/v1/review/cases/{case_id}/decision", json=dec_payload, headers=headers_v)
    assert res.status_code == 200
    assert res.json()["new_status"] == "Verified"
