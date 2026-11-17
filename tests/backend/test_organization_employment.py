"""Automated Tests for Phase 13 — Organization and Employment Verification.

Covers organization registration, membership management, self-asserted vs organization-confirmed
employment claims, cross-organization boundary isolation, provenance tracking, and audit logging.
"""

from fastapi.testclient import TestClient

from app.services.audit_service import AuditService


# -----------------------------------------------------------------------------
# 1. Organization Registration & Onboarding
# -----------------------------------------------------------------------------
def test_register_organization_success(client: TestClient, subject_token: str):
    """Subject can register a new corporate entity and automatically become Organization Admin."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    payload = {
        "name": "Stark Industries Trust",
        "slug": "stark-industries",
        "verified_domain": "starkindustries.com",
        "registration_number": "REG-STARK-2026",
        "country_region": "US",
        "tier": "ENTERPRISE",
    }
    res = client.post("/api/v1/organizations", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Stark Industries Trust"
    assert data["slug"] == "stark-industries"
    assert data["tier"] == "ENTERPRISE"
    assert data["is_active"] is True
    org_id = data["id"]

    # Verify creator is listed as ROLE_ORG_ADMIN
    members_res = client.get(f"/api/v1/organizations/{org_id}/members", headers=headers)
    assert members_res.status_code == 200
    members = members_res.json()
    assert len(members) == 1
    assert members[0]["role"] == "ROLE_ORG_ADMIN"


def test_register_duplicate_slug_conflict(client: TestClient, subject_token: str):
    """Attempting to register an organization with an existing slug returns HTTP 409 Conflict."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    payload = {
        "name": "Acme Trust Fake",
        "slug": "acme-trust",  # Already exists in seeds
        "verified_domain": "fake.org",
    }
    res = client.post("/api/v1/organizations", json=payload, headers=headers)
    assert res.status_code == 409


def test_list_organizations_scoped_to_memberships(
    client: TestClient, org_member_token: str, admin_token: str
):
    """Org member sees organizations they belong to; Sys Admin sees all organizations globally."""
    headers_m = {"Authorization": f"Bearer {org_member_token}"}
    res_m = client.get("/api/v1/organizations", headers=headers_m)
    assert res_m.status_code == 200
    slugs_m = [o["slug"] for o in res_m.json()]
    assert "acme-trust" in slugs_m
    assert "globex-corp" not in slugs_m  # Member does not belong to Globex

    headers_adm = {"Authorization": f"Bearer {admin_token}"}
    res_adm = client.get("/api/v1/organizations", headers=headers_adm)
    assert res_adm.status_code == 200
    slugs_adm = [o["slug"] for o in res_adm.json()]
    assert "acme-trust" in slugs_adm
    assert "globex-corp" in slugs_adm


# -----------------------------------------------------------------------------
# 2. Membership Lifecycle & Access Control
# -----------------------------------------------------------------------------
def test_add_and_remove_organization_member(client: TestClient, org_admin_token: str):
    """Organization Admin can add a new member and subsequently remove them (HTTP 204)."""
    headers = {"Authorization": f"Bearer {org_admin_token}"}
    org_id = "org-acme-111"

    # Add member
    add_req = {
        "user_id": "user-test-contractor-999",
        "role": "ROLE_ORG_MEMBER",
        "email": "contractor@acme.org",
    }
    add_res = client.post(f"/api/v1/organizations/{org_id}/members", json=add_req, headers=headers)
    assert add_res.status_code == 201
    assert add_res.json()["user_id"] == "user-test-contractor-999"

    # Verify listed
    list_res = client.get(f"/api/v1/organizations/{org_id}/members", headers=headers)
    assert any(m["user_id"] == "user-test-contractor-999" for m in list_res.json())

    # Remove member
    del_res = client.delete(f"/api/v1/organizations/{org_id}/members/user-test-contractor-999", headers=headers)
    assert del_res.status_code == 204

    # Verify removed
    list_after = client.get(f"/api/v1/organizations/{org_id}/members", headers=headers)
    assert not any(m["user_id"] == "user-test-contractor-999" for m in list_after.json())


def test_non_admin_member_cannot_manage_members(client: TestClient, org_member_token: str):
    """Standard Organization Member cannot add or remove members (HTTP 403 Forbidden)."""
    headers = {"Authorization": f"Bearer {org_member_token}"}
    org_id = "org-acme-111"

    add_req = {"user_id": "user-unauthorized-add", "role": "ROLE_ORG_MEMBER"}
    add_res = client.post(f"/api/v1/organizations/{org_id}/members", json=add_req, headers=headers)
    assert add_res.status_code == 403

    del_res = client.delete(f"/api/v1/organizations/{org_id}/members/some-user", headers=headers)
    assert del_res.status_code == 403


# -----------------------------------------------------------------------------
# 3. Employment Claims Lifecycle: Self-Asserted vs Confirmed
# -----------------------------------------------------------------------------
def test_subject_can_submit_self_asserted_employment_claim(client: TestClient, subject_token: str):
    """Subject submits an employment claim for an organization; initial state is strictly SELF_ASSERTED."""
    headers = {"Authorization": f"Bearer {subject_token}"}
    org_id = "org-acme-111"

    claim_req = {
        "job_title": "Senior Cryptographic Engineer",
        "department": "Security Architecture",
        "employee_id": "EMP-9901",
        "work_email": "jane.citizen@acme.org",
        "start_date": "2024-03-01",
        "evidence_hashes": ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
    }
    res = client.post(f"/api/v1/organizations/{org_id}/claims", json=claim_req, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["assertion_type"] == "SELF_ASSERTED"
    assert data["job_title"] == "Senior Cryptographic Engineer"
    assert data["confirmed_by_user_id"] is None
    assert data["confirmed_at"] is None
    assert data["credential_expires_at"] is None
    claim_id = data["claim_id"]

    # Subject can query their personal claims
    my_claims_res = client.get("/api/v1/organizations/claims/me", headers=headers)
    assert my_claims_res.status_code == 200
    assert any(c["claim_id"] == claim_id for c in my_claims_res.json())


def test_org_admin_confirms_employment_claim(
    client: TestClient, subject_token: str, org_admin_token: str
):
    """Organization Admin verifies and confirms pending self-asserted claim; sets expiration & provenance."""
    headers_sub = {"Authorization": f"Bearer {subject_token}"}
    org_id = "org-acme-111"

    # Submit claim
    claim_req = {
        "job_title": "Lead Security Auditor",
        "department": "Compliance",
        "work_email": "auditor.lead@acme.org",
        "start_date": "2024-01-10",
    }
    submit_res = client.post(f"/api/v1/organizations/{org_id}/claims", json=claim_req, headers=headers_sub)
    claim_id = submit_res.json()["claim_id"]

    # Org Admin confirms
    headers_adm = {"Authorization": f"Bearer {org_admin_token}"}
    verify_req = {"action": "CONFIRM", "credential_validity_days": 180}
    verify_res = client.post(
        f"/api/v1/organizations/{org_id}/claims/{claim_id}/verify",
        json=verify_req,
        headers=headers_adm,
    )
    assert verify_res.status_code == 200
    confirmed = verify_res.json()
    assert confirmed["assertion_type"] == "ORGANIZATION_CONFIRMED"
    assert confirmed["confirmed_by_user_id"] == "user-acme-admin"
    assert confirmed["confirmed_at"] is not None
    assert confirmed["credential_expires_at"] is not None


def test_org_admin_rejects_employment_claim(
    client: TestClient, subject_token: str, org_admin_token: str
):
    """Organization Admin rejects invalid or unverified employment claim with reason code."""
    headers_sub = {"Authorization": f"Bearer {subject_token}"}
    org_id = "org-acme-111"

    claim_req = {
        "job_title": "Chief Executive Officer",
        "department": "Executive",
        "work_email": "imposter@acme.org",
        "start_date": "2026-01-01",
    }
    submit_res = client.post(f"/api/v1/organizations/{org_id}/claims", json=claim_req, headers=headers_sub)
    claim_id = submit_res.json()["claim_id"]

    # Org Admin rejects
    headers_adm = {"Authorization": f"Bearer {org_admin_token}"}
    verify_req = {
        "action": "REJECT",
        "rejection_reason": "Subject is not present in corporate HR database",
    }
    verify_res = client.post(
        f"/api/v1/organizations/{org_id}/claims/{claim_id}/verify",
        json=verify_req,
        headers=headers_adm,
    )
    assert verify_res.status_code == 200
    rejected = verify_res.json()
    assert rejected["assertion_type"] == "REJECTED"
    assert rejected["rejection_reason"] == "Subject is not present in corporate HR database"


def test_cross_org_claims_verification_blocked(
    client: TestClient, subject_token: str, org_b_member_token: str
):
    """Admin of Organization B is blocked from verifying claims belonging to Organization A (HTTP 403)."""
    headers_sub = {"Authorization": f"Bearer {subject_token}"}
    org_id = "org-acme-111"

    claim_req = {
        "job_title": "Software Engineer",
        "department": "Engineering",
        "work_email": "dev@acme.org",
        "start_date": "2024-05-01",
    }
    submit_res = client.post(f"/api/v1/organizations/{org_id}/claims", json=claim_req, headers=headers_sub)
    claim_id = submit_res.json()["claim_id"]

    # Globex Admin attempts to verify Acme claim
    headers_b = {"Authorization": f"Bearer {org_b_member_token}"}
    res_b = client.post(
        f"/api/v1/organizations/{org_id}/claims/{claim_id}/verify",
        json={"action": "CONFIRM"},
        headers=headers_b,
    )
    assert res_b.status_code == 403


def test_cross_org_claims_listing_blocked(client: TestClient, org_b_member_token: str):
    """Member of Organization B is blocked from listing claims for Organization A (HTTP 403)."""
    headers_b = {"Authorization": f"Bearer {org_b_member_token}"}
    res = client.get("/api/v1/organizations/org-acme-111/claims", headers=headers_b)
    assert res.status_code == 403
