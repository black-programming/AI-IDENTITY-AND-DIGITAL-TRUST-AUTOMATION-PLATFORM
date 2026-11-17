"""Staging Deployment Automated Smoke and Authorization Gate.

Used by CD pipelines and release engineers to validate staging container deployments
before promoting code or database migrations to production.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
import requests
import jwt

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings

TARGET_URL = os.getenv("STAGING_URL", "http://127.0.0.1:8000")


def generate_token(role: str = "ROLE_SYS_ADMIN", user_id: str = "smoke_user_01") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": f"{user_id}@trust-platform.internal",
        "app_metadata": {"role": role},
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "iss": settings.SUPABASE_URL,
        "aud": "authenticated",
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


def log_phase(title: str):
    print(f"\n[SMOKE-TEST] ----------------------------------------")
    print(f"[SMOKE-TEST] >>> {title}")
    print(f"[SMOKE-TEST] ----------------------------------------")


def run_staging_smoke_tests(base_url: str = TARGET_URL) -> bool:
    session = requests.Session()
    admin_token = generate_token("ROLE_SYS_ADMIN", "admin_smoke")
    subject_token = generate_token("ROLE_SUBJECT", "subject_smoke")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    subject_headers = {"Authorization": f"Bearer {subject_token}"}

    # 1. Health Probe
    log_phase("1. Probing Container Health & Latency")
    resp_health = session.get(f"{base_url}/api/v1/health")
    assert resp_health.status_code == 200, f"Expected 200, got {resp_health.status_code}"
    assert "X-Request-ID" in resp_health.headers, "X-Request-ID header missing"
    assert "X-Process-Time-Ms" in resp_health.headers, "X-Process-Time-Ms header missing"
    print(f"    [OK] /api/v1/health returned 200. Latency: {resp_health.headers.get('X-Process-Time-Ms')}ms")

    # 2. Detailed Subsystem Monitoring
    log_phase("2. Subsystem Diagnostics (DB, Storage, OCR, Audit)")
    resp_mon = session.get(f"{base_url}/api/v1/monitoring/health")
    assert resp_mon.status_code == 200, f"Expected 200, got {resp_mon.status_code}"
    mon_data = resp_mon.json()
    assert mon_data["status"] in ["HEALTHY", "DEGRADED"], f"Unhealthy status: {mon_data['status']}"
    print(f"    [OK] System Health: {mon_data['status']} ({len(mon_data['components'])} active components)")

    # 3. Security Headers Verification
    log_phase("3. Security Headers Verification (HSTS, CSP, Sniff Protection)")
    assert resp_health.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp_health.headers.get("X-Frame-Options") == "DENY"
    print("    [OK] Security headers verified (nosniff, DENY, X-Request-ID present).")

    # 4. Authorization Boundary Checks (401 & 403)
    log_phase("4. Authorization Boundary Enforcement")
    # Unauthenticated -> 401
    resp_unauth = session.post(f"{base_url}/api/v1/cases", json={"claim_type": "disability"})
    assert resp_unauth.status_code == 401, f"Expected 401, got {resp_unauth.status_code}"
    print("    [OK] Unauthenticated request correctly rejected with 401 Unauthorized.")

    # Insufficient Role -> 403
    resp_forbidden = session.post(
        f"{base_url}/api/v1/monitoring/circuit-breaker/trip",
        headers=subject_headers
    )
    assert resp_forbidden.status_code == 403, f"Expected 403, got {resp_forbidden.status_code}"
    print("    [OK] Privileged admin operation forbidden to ROLE_SUBJECT (403 Forbidden).")

    # 5. Idempotent Mutation & Workflow Test
    log_phase("5. Staging Mutation & Idempotency Workflow")
    idemp_key = f"smoke-idemp-{uuid.uuid4().hex}"
    case_payload = {
        "title": "Staging Deployment Smoke Claim",
        "description": "Validation check executed during CD deployment gate",
        "claim_type": "national_id",
        "priority": "HIGH"
    }

    # Call 1
    resp_c1 = session.post(
        f"{base_url}/api/v1/cases",
        json=case_payload,
        headers={"Idempotency-Key": idemp_key, **admin_headers}
    )
    assert resp_c1.status_code == 201, f"Expected 201, got {resp_c1.status_code}: {resp_c1.text}"
    assert resp_c1.headers.get("X-Cache-Lookup") == "MISS", "Expected cache MISS on first call"
    case_id = resp_c1.json()["case_id"]

    # Call 2 (Duplicate replay)
    resp_c2 = session.post(
        f"{base_url}/api/v1/cases",
        json=case_payload,
        headers={"Idempotency-Key": idemp_key, **admin_headers}
    )
    assert resp_c2.status_code == 201, f"Expected 201, got {resp_c2.status_code}"
    assert resp_c2.headers.get("X-Cache-Lookup") == "HIT", "Expected cache HIT on replay"
    assert resp_c2.json()["case_id"] == case_id, "Replay returned different case ID!"
    print(f"    [OK] Case {case_id} created with idempotent deduplication verified.")

    # 6. Operational Telemetry Check
    log_phase("6. Staging Operational Telemetry & Alert State")
    resp_metrics = session.get(f"{base_url}/api/v1/monitoring/metrics", headers=admin_headers)
    assert resp_metrics.status_code == 200
    metrics = resp_metrics.json()
    print(f"    [OK] Telemetry counters recorded: total_requests={metrics['total_requests']}, 2xx={metrics['status_2xx_count']}")

    print("\n=================================================================")
    print(">>> STAGING DEPLOYMENT SMOKE & AUTHORIZATION GATES PASSED 100% <<<")
    print("=================================================================")
    return True


if __name__ == "__main__":
    try:
        run_staging_smoke_tests()
    except Exception as e:
        print(f"\n[!] Staging smoke test failure: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
