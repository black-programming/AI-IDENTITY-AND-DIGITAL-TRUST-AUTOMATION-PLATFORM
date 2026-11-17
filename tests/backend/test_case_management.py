"""Phase 6 Verification Case Management Tests."""

import pytest
from fastapi.testclient import TestClient


def test_create_case_success(client: TestClient, subject_token: str):
    """Subject creates a new verification case in Draft status."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    payload = {
        "claim_type": "SYNTH_NAT_ID_V1",
        "purpose": "kyc_onboarding",
        "priority": "HIGH",
    }
    response = client.post("/api/v1/cases", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "Draft"
    assert data["claim_type"] == "SYNTH_NAT_ID_V1"
    assert data["purpose"] == "kyc_onboarding"
    assert data["priority"] == "HIGH"
    assert data["case_id"] is not None


def test_create_case_missing_claim_type_rejected(client: TestClient, subject_token: str):
    """Creating a case without claim_type must be rejected."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    response = client.post("/api/v1/cases", json={"claim_type": "   "}, headers=headers)
    assert response.status_code in (400, 422)


def test_list_cases_subject_isolated(client: TestClient, subject_token: str, subject_b_token: str):
    """Subject can only view cases they own; cannot see other subjects' cases."""
    # 1. Create a case for User A
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    res_a = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_a)
    case_a_id = res_a.json()["case_id"]

    # 2. List cases as User A
    list_a = client.get("/api/v1/cases", headers=headers_a)
    assert list_a.status_code == 200
    ids_a = [c["case_id"] for c in list_a.json()["cases"]]
    assert case_a_id in ids_a

    # 3. List cases as User B
    headers_b = {"Authorization": f"Bearer {subject_b_token}"}
    list_b = client.get("/api/v1/cases", headers=headers_b)
    assert list_b.status_code == 200
    ids_b = [c["case_id"] for c in list_b.json()["cases"]]
    assert case_a_id not in ids_b


def test_list_cases_reviewer_sees_all(client: TestClient, verifier_token: str):
    """Verifier has global visibility to list all cases."""
    headers = {"Authorization": f"Bearer {verifier_token}"}
    res = client.get("/api/v1/cases", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    assert len(data["cases"]) >= 2


def test_list_cases_filter_by_status(client: TestClient, verifier_token: str):
    """Filtering cases by status returns only matching items."""
    headers = {"Authorization": f"Bearer {verifier_token}"}
    res = client.get("/api/v1/cases?status=Under%20Review", headers=headers)
    assert res.status_code == 200
    for case in res.json()["cases"]:
        assert case["status"] == "Under Review"


def test_get_case_detail_with_timeline(client: TestClient, subject_token: str):
    """Retrieving a case detail returns metadata, timeline history, and allowed transitions."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    res = client.get("/api/v1/cases/00000000-0000-0000-0000-000000000001", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "00000000-0000-0000-0000-000000000001"
    assert data["status"] == "Draft"
    assert "timeline" in data
    assert len(data["timeline"]) >= 1
    assert "allowed_next_transitions" in data
    assert "Submitted" in data["allowed_next_transitions"]


def test_case_submit_valid_transition(client: TestClient, subject_token: str):
    """Draft case is successfully submitted by owner."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    # Create draft
    create_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = create_res.json()["case_id"]

    # Submit
    submit_res = client.post(
        f"/api/v1/cases/{case_id}/submit",
        json={"idempotency_key": "sub_key_101"},
        headers=headers,
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "Submitted"

    # Verify detail shows Submitted and updated timeline
    detail_res = client.get(f"/api/v1/cases/{case_id}", headers=headers)
    assert detail_res.json()["status"] == "Submitted"


def test_case_submit_invalid_status_rejected(client: TestClient, subject_token: str):
    """Attempting to submit a case not in Draft or Action Required status fails with 400."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    # Case 00000000-0000-0000-0000-000000000002 is already 'Under Review'
    res = client.post(
        "/api/v1/cases/00000000-0000-0000-0000-000000000002/submit",
        json={"idempotency_key": "invalid_sub_retry"},
        headers=headers,
    )
    assert res.status_code == 400


def test_state_machine_valid_transition_by_reviewer(client: TestClient, verifier_token: str):
    """Reviewer can transition a case from Under Review to Verified."""
    headers = {"Authorization": f"Bearer {verifier_token}"}
    res = client.post(
        "/api/v1/cases/00000000-0000-0000-0000-000000000002/transition",
        json={"to_status": "Verified", "comment": "Document verified successfully"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "Verified"
    assert res.json()["current_decision"] == "ALLOW"


def test_state_machine_invalid_transition_rejected(client: TestClient, subject_token: str):
    """Attempting an invalid transition (e.g. Draft -> Verified) is rejected with 400."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    create_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = create_res.json()["case_id"]

    res = client.post(
        f"/api/v1/cases/{case_id}/transition",
        json={"to_status": "Verified"},
        headers=headers,
    )
    assert res.status_code == 400


def test_state_machine_subject_unauthorized_transition(client: TestClient, subject_token: str):
    """Subject cannot transition a case directly to Verified or Rejected (requires Reviewer)."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    create_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    case_id = create_res.json()["case_id"]

    # Even if transition were allowed, subject is blocked from privileged states
    res = client.post(
        f"/api/v1/cases/{case_id}/transition",
        json={"to_status": "Verified"},
        headers=headers,
    )
    assert res.status_code in (400, 403)


def test_assign_reviewer_success(client: TestClient, verifier_token: str):
    """Reviewer or Administrator can assign a case to a specific reviewer."""
    headers = {"Authorization": f"Bearer {verifier_token}"}
    payload = {
        "reviewer_id": "rev-officer-999",
        "comment": "Assigned to Senior Verification Officer",
    }
    res = client.post("/api/v1/cases/00000000-0000-0000-0000-000000000001/assign", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["assigned_reviewer_id"] == "rev-officer-999"


def test_assign_reviewer_by_subject_blocked(client: TestClient, subject_token: str):
    """Subject caller is strictly blocked with 403 from assigning reviewers."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    payload = {"reviewer_id": "rev-officer-999"}
    res = client.post("/api/v1/cases/00000000-0000-0000-0000-000000000001/assign", json=payload, headers=headers)
    assert res.status_code == 403
