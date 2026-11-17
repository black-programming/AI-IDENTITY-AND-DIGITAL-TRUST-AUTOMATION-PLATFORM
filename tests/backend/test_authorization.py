"""Phase 5 Authorization, RBAC, Multi-Tenancy, and Database Security Tests."""

import pytest
from fastapi.testclient import TestClient


def get_error_message(res) -> str:
    """Helper to safely extract error message from standard error envelopes."""
    data = res.json()
    if "detail" in data:
        return str(data["detail"])
    if "error" in data and isinstance(data["error"], dict) and "message" in data["error"]:
        return str(data["error"]["message"])
    return str(data)


def test_case_owner_can_access_own_case(client: TestClient, subject_token: str):
    """Subject can access a case they own."""
    # 1. Create case as subject
    headers = {"Authorization": f"Bearer {subject_token}"}
    create_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers)
    assert create_res.status_code == 201
    case_id = create_res.json()["case_id"]

    # 2. Get case as owner
    get_res = client.get(f"/api/v1/cases/{case_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["case_id"] == case_id


def test_cross_user_case_access_blocked(client: TestClient, subject_token: str, subject_b_token: str):
    """User B must be rejected with HTTP 403 when attempting to access User A's case."""
    # 1. Create case as User A
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    create_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_a)
    assert create_res.status_code == 201
    case_id = create_res.json()["case_id"]

    # 2. Attempt to read case as User B (attacker)
    headers_b = {"Authorization": f"Bearer {subject_b_token}"}
    get_res = client.get(f"/api/v1/cases/{case_id}", headers=headers_b)
    assert get_res.status_code == 403
    assert "Cross-user access denied" in get_error_message(get_res)


def test_cross_user_case_submission_blocked(client: TestClient, subject_token: str, subject_b_token: str):
    """User B must be rejected with HTTP 403 when attempting to submit User A's case."""
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    create_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_a)
    case_id = create_res.json()["case_id"]

    # Attempt submission as User B
    headers_b = {"Authorization": f"Bearer {subject_b_token}"}
    submit_res = client.post(
        f"/api/v1/cases/{case_id}/submit",
        json={"idempotency_key": "sub_attempt_999"},
        headers=headers_b,
    )
    assert submit_res.status_code == 403


def test_cross_user_evidence_upload_blocked(client: TestClient, subject_token: str, subject_b_token: str):
    """User B cannot generate evidence upload URLs for User A's case."""
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    create_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_a)
    case_id = create_res.json()["case_id"]

    headers_b = {"Authorization": f"Bearer {subject_b_token}"}
    upload_res = client.post(
        "/api/v1/evidence/upload-url",
        json={
            "case_id": case_id,
            "file_name": "malicious.pdf",
            "mime_type": "application/pdf",
            "file_size_bytes": 1024,
            "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        },
        headers=headers_b,
    )
    assert upload_res.status_code == 403


def test_cross_user_receipt_access_blocked(client: TestClient, subject_b_token: str):
    """User B cannot view receipts for cases owned by User A."""
    headers_b = {"Authorization": f"Bearer {subject_b_token}"}
    # Case '00000000-0000-0000-0000-000000000002' is owned by User A
    res = client.get("/api/v1/receipts/00000000-0000-0000-0000-000000000002", headers=headers_b)
    assert res.status_code == 403


def test_reviewer_and_admin_can_inspect_any_case(
    client: TestClient,
    subject_token: str,
    verifier_token: str,
    admin_token: str,
):
    """Reviewers and System Admins have elevated privileges to view and verify cases."""
    headers_a = {"Authorization": f"Bearer {subject_token}"}
    create_res = client.post("/api/v1/cases", json={"claim_type": "SYNTH_NAT_ID_V1"}, headers=headers_a)
    case_id = create_res.json()["case_id"]

    # Verifier can access
    headers_v = {"Authorization": f"Bearer {verifier_token}"}
    res_v = client.get(f"/api/v1/cases/{case_id}", headers=headers_v)
    assert res_v.status_code == 200

    # Admin can access
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    res_admin = client.get(f"/api/v1/cases/{case_id}", headers=headers_admin)
    assert res_admin.status_code == 200


def test_subject_cannot_access_review_queue_or_decisions(client: TestClient, subject_token: str):
    """ROLE_SUBJECT callers are strictly barred from reviewer operations."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    # Queue access
    queue_res = client.get("/api/v1/review/queue", headers=headers)
    assert queue_res.status_code == 403

    # Decision submission
    decision_res = client.post(
        "/api/v1/review/cases/00000000-0000-0000-0000-000000000002/decision",
        json={"decision": "ALLOW", "reason_code": "DEC_ALLOW_SATISFIED"},
        headers=headers,
    )
    assert decision_res.status_code == 403


def test_org_member_can_access_own_organization(client: TestClient, org_member_token: str):
    """Organization members can access their own organization details and members."""
    headers = {"Authorization": f"Bearer {org_member_token}"}
    res = client.get("/api/v1/organizations/org-acme-111", headers=headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Acme Trust Technologies"

    members_res = client.get("/api/v1/organizations/org-acme-111/members", headers=headers)
    assert members_res.status_code == 200
    assert len(members_res.json()) >= 1


def test_cross_org_access_blocked(client: TestClient, org_b_member_token: str):
    """Member of Org Globex cannot access Org Acme resources."""
    headers = {"Authorization": f"Bearer {org_b_member_token}"}

    # Cannot view Org Acme
    res = client.get("/api/v1/organizations/org-acme-111", headers=headers)
    assert res.status_code == 403
    assert "Cross-organization access denied" in get_error_message(res)

    # Cannot list Org Acme members
    members_res = client.get("/api/v1/organizations/org-acme-111/members", headers=headers)
    assert members_res.status_code == 403


def test_org_member_cannot_add_members_only_org_admin(
    client: TestClient,
    org_member_token: str,
    org_admin_token: str,
):
    """Standard org member gets 403 when trying to add members; Org Admin succeeds."""
    headers_member = {"Authorization": f"Bearer {org_member_token}"}
    payload = {"user_id": "user-newbie-101", "role": "ROLE_ORG_MEMBER", "email": "newbie@acme.org"}

    # Standard member fails
    fail_res = client.post("/api/v1/organizations/org-acme-111/members", json=payload, headers=headers_member)
    assert fail_res.status_code == 403
    assert "only organization administrators" in get_error_message(fail_res).lower()

    # Org Admin succeeds
    headers_admin = {"Authorization": f"Bearer {org_admin_token}"}
    success_res = client.post("/api/v1/organizations/org-acme-111/members", json=payload, headers=headers_admin)
    assert success_res.status_code == 201
    assert success_res.json()["user_id"] == "user-newbie-101"


def test_sys_admin_has_global_org_access(client: TestClient, admin_token: str):
    """ROLE_SYS_ADMIN can view and manage any organization."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    res_a = client.get("/api/v1/organizations/org-acme-111", headers=headers)
    assert res_a.status_code == 200

    res_b = client.get("/api/v1/organizations/org-globex-222", headers=headers)
    assert res_b.status_code == 200


def test_unauthenticated_requests_fail_closed(client: TestClient):
    """Protected endpoints fail closed with 401 when unauthenticated."""
    assert client.get("/api/v1/cases/any-id").status_code == 401
    assert client.get("/api/v1/review/queue").status_code == 401
    assert client.get("/api/v1/receipts/any-id").status_code == 401
    assert client.get("/api/v1/organizations/org-acme-111").status_code == 401
