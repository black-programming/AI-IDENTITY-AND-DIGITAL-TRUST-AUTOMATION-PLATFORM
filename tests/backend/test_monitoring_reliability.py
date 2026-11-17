"""Unit and Integration Tests for Phase 18 Operational Monitoring, Reliability, and Idempotency."""

from datetime import datetime, timezone
import io
import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.logging import sanitize_log_message
from app.core.middleware import reset_idempotency_store
from app.services.monitoring_service import MonitoringService
from app.services.ocr_service import OCRService, SYNTHETIC_TEMPLATES


# -----------------------------------------------------------------------------
# 1. Request ID & Processing Time Headers
# -----------------------------------------------------------------------------
def test_request_id_and_process_time_headers_returned(client: TestClient):
    """Every HTTP response must include correlation X-Request-ID and X-Process-Time-Ms."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200

    headers = res.headers
    assert "X-Request-ID" in headers
    assert len(headers["X-Request-ID"]) >= 16
    assert "X-Process-Time-Ms" in headers
    assert float(headers["X-Process-Time-Ms"]) >= 0.0


def test_incoming_request_id_propagated(client: TestClient):
    """Incoming client-supplied X-Request-ID is preserved and echoed in response headers."""
    custom_req_id = "req-audit-correlation-998877"
    res = client.get("/api/v1/health", headers={"x-request-id": custom_req_id})
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == custom_req_id


# -----------------------------------------------------------------------------
# 2. Structured Redacted Logging & Masking
# -----------------------------------------------------------------------------
def test_structured_log_redaction_sanitizes_secrets_and_pii():
    """Automated log sanitizer suppresses JWT tokens, private keys, passwords, and credit cards."""
    # 1. JWT Token Redaction
    sample_jwt = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotLeakThisSignatureValue"
    msg_jwt = f"User authentication attempt with token {sample_jwt}"
    clean_jwt = sanitize_log_message(msg_jwt)
    assert "doNotLeakThisSignatureValue" not in clean_jwt
    assert "Bearer [REDACTED_JWT]" in clean_jwt

    # 2. Private Key Redaction
    sample_pem = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0987654321deadbeefcafebabe\n"
        "-----END RSA PRIVATE KEY-----"
    )
    clean_pem = sanitize_log_message(f"Loaded credentials: {sample_pem}")
    assert "deadbeef" not in clean_pem
    assert "[REDACTED_PRIVATE_KEY]" in clean_pem

    # 3. Password field scrubbing
    clean_pw = sanitize_log_message('Attempt payload: {"user": "alice", "password": "SuperSecretPassword123!"}')
    assert "SuperSecretPassword123!" not in clean_pw
    assert "***REDACTED***" in clean_pw

    # 4. Credit card masking
    clean_cc = sanitize_log_message("Charged card 4111 2222 3333 4444 for payment")
    assert "4111" not in clean_cc
    assert "****-****-****-****" in clean_cc


# -----------------------------------------------------------------------------
# 3. Idempotency Protection for Mutating Requests
# -----------------------------------------------------------------------------
def test_idempotency_key_prevents_duplicate_mutations(client: TestClient, subject_token: str):
    """Repeated requests with identical Idempotency-Key return cached response with X-Cache-Lookup: HIT."""
    reset_idempotency_store()
    headers = {
        "Authorization": f"Bearer {subject_token}",
        "Idempotency-Key": str(uuid.uuid4()),
    }
    payload = {"claim_type": "SYNTH_NAT_ID_V1"}

    # First request: Cache MISS -> Creates case
    res1 = client.post("/api/v1/cases", json=payload, headers=headers)
    assert res1.status_code == 201
    assert res1.headers.get("X-Cache-Lookup") == "MISS"
    case_id_1 = res1.json()["case_id"]

    # Second identical request with same key: Cache HIT -> Returns identical response
    res2 = client.post("/api/v1/cases", json=payload, headers=headers)
    assert res2.status_code == 201
    assert res2.headers.get("X-Cache-Lookup") == "HIT"
    assert res2.headers.get("Idempotency-Key") == headers["Idempotency-Key"]
    case_id_2 = res2.json()["case_id"]

    assert case_id_1 == case_id_2


def test_idempotency_key_different_keys_execute_distinct_actions(client: TestClient, subject_token: str):
    """Different Idempotency-Keys execute independently, creating distinct entities."""
    reset_idempotency_store()
    headers_1 = {"Authorization": f"Bearer {subject_token}", "Idempotency-Key": str(uuid.uuid4())}
    headers_2 = {"Authorization": f"Bearer {subject_token}", "Idempotency-Key": str(uuid.uuid4())}
    payload = {"claim_type": "SYNTH_NAT_ID_V1"}

    res1 = client.post("/api/v1/cases", json=payload, headers=headers_1)
    res2 = client.post("/api/v1/cases", json=payload, headers=headers_2)

    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res1.json()["case_id"] != res2.json()["case_id"]


# -----------------------------------------------------------------------------
# 4. System Health Diagnostics & Subsystem Probes
# -----------------------------------------------------------------------------
def test_monitoring_system_health_endpoint(client: TestClient):
    """Detailed health probe inspects API, Database, Storage, OCR Engine, and Audit Chain."""
    res = client.get("/api/v1/monitoring/health")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] in ("HEALTHY", "DEGRADED")
    assert data["uptime_seconds"] >= 0.0
    comps = data["components"]
    assert "api" in comps and comps["api"]["status"] == "HEALTHY"
    assert "database" in comps and comps["database"]["status"] == "HEALTHY"
    assert "storage" in comps and comps["storage"]["status"] == "HEALTHY"
    assert "ocr_engine" in comps
    assert "audit_chain" in comps and comps["audit_chain"]["status"] == "HEALTHY"


# -----------------------------------------------------------------------------
# 5. Operational Telemetry & Metrics
# -----------------------------------------------------------------------------
def test_monitoring_operational_metrics_endpoint(client: TestClient, auditor_token: str):
    """Operational telemetry returns counters, error ratios, latency, and active queues."""
    headers = {"Authorization": f"Bearer {auditor_token}"}
    res = client.get("/api/v1/monitoring/metrics", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_requests"] >= 0
    assert data["status_2xx_count"] >= 0
    assert 0.0 <= data["error_rate_percentage"] <= 100.0
    assert data["average_latency_ms"] >= 0.0
    assert data["circuit_breaker_state"] in ("CLOSED", "OPEN", "HALF_OPEN")


# -----------------------------------------------------------------------------
# 6. Circuit Breaker & Graceful Degradation
# -----------------------------------------------------------------------------
def test_circuit_breaker_status_and_tripping(client: TestClient, admin_token: str):
    """Circuit breaker trips on upstream outages, engaging fallback and recovering on reset."""
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Initial state: CLOSED
    status_res = client.get("/api/v1/monitoring/circuit-breaker")
    assert status_res.status_code == 200
    assert status_res.json()["state"] == "CLOSED"

    # Trip breaker
    trip_res = client.post("/api/v1/monitoring/circuit-breaker/trip", headers=admin_headers)
    assert trip_res.status_code == 200
    assert trip_res.json()["state"] == "OPEN"
    assert trip_res.json()["fallback_active"] is True
    assert MonitoringService.is_circuit_open() is True

    # Reset breaker
    reset_res = client.post("/api/v1/monitoring/circuit-breaker/reset", headers=admin_headers)
    assert reset_res.status_code == 200
    assert reset_res.json()["state"] == "CLOSED"
    assert MonitoringService.is_circuit_open() is False


def test_circuit_breaker_engages_ocr_fallback():
    """When circuit breaker is OPEN, OCR service engages fallback engine without failure."""
    try:
        # Trip breaker
        for _ in range(3):
            MonitoringService.record_upstream_failure()
        assert MonitoringService.is_circuit_open() is True

        # Process a valid document
        sample_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200
        result = OCRService.extract_from_bytes(
            image_bytes=sample_bytes,
            case_id="case-cb-test",
            file_id=str(uuid.uuid4()),
            claim_type="SYNTH_NAT_ID_V1",
        )

        assert "CircuitBreakerFallback" in result["ocr_engine"]
        assert "WARN_CIRCUIT_BREAKER_FALLBACK_ENGAGED" in result["reason_codes"]
    finally:
        MonitoringService.reset_circuit_breaker()


# -----------------------------------------------------------------------------
# 7. Incident Alerting & Resolution
# -----------------------------------------------------------------------------
def test_incident_alert_dispatch_and_resolution(client: TestClient, auditor_token: str, verifier_token: str):
    """System records alerts for critical anomalies and tracks acknowledgment/resolution."""
    auditor_headers = {"Authorization": f"Bearer {auditor_token}"}
    verifier_headers = {"Authorization": f"Bearer {verifier_token}"}

    # 1. Dispatch an incident alert
    alert = MonitoringService.record_alert("CRITICAL", "STORAGE_SUBSYSTEM", "Simulated storage bucket latency degradation")
    assert alert.alert_id is not None

    # 2. Query alerts
    list_res = client.get("/api/v1/monitoring/alerts", headers=auditor_headers)
    assert list_res.status_code == 200
    alerts = list_res.json()["alerts"]
    matching = [a for a in alerts if a["alert_id"] == alert.alert_id]
    assert len(matching) == 1
    assert matching[0]["resolved"] is False

    # 3. Resolve the alert
    resolve_res = client.post(f"/api/v1/monitoring/alerts/{alert.alert_id}/resolve", headers=verifier_headers)
    assert resolve_res.status_code == 200
    assert resolve_res.json()["resolved"] is True


# -----------------------------------------------------------------------------
# 8. RBAC Access Control on Monitoring Endpoints
# -----------------------------------------------------------------------------
def test_non_privileged_user_blocked_from_metrics_and_alerts(client: TestClient, subject_token: str):
    """Unprivileged citizen subjects cannot inspect system telemetry or security alerts."""
    headers = {"Authorization": f"Bearer {subject_token}"}

    metrics_res = client.get("/api/v1/monitoring/metrics", headers=headers)
    assert metrics_res.status_code == 403

    alerts_res = client.get("/api/v1/monitoring/alerts", headers=headers)
    assert alerts_res.status_code == 403
