"""API Endpoints for Phase 18 Operational Monitoring, Health Diagnostics, Telemetry, and Circuit Breakers."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import AuthenticatedUser, get_current_user, require_role
from app.schemas.monitoring import (
    AlertsListResponse,
    CircuitBreakerStatusResponse,
    OperationalAlertItem,
    OperationalMetricsResponse,
    SystemHealthResponse,
)
from app.services.monitoring_service import MonitoringService

router = APIRouter(prefix="/monitoring", tags=["Operational Monitoring & Reliability"])


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health() -> SystemHealthResponse:
    """Detailed health check probe evaluating API, Database, Storage, OCR Engine, and Audit Chain."""
    return MonitoringService.get_system_health()


@router.get("/metrics", response_model=OperationalMetricsResponse)
async def get_operational_metrics(
    current_user: AuthenticatedUser = Depends(require_role(["ROLE_AUDITOR", "ROLE_SYS_ADMIN", "ROLE_VERIFIER"])),
) -> OperationalMetricsResponse:
    """Live telemetry counters: total requests, 2xx/4xx/5xx ratios, average latency, and active case queues."""
    return MonitoringService.get_operational_metrics()


@router.get("/circuit-breaker", response_model=CircuitBreakerStatusResponse)
async def get_circuit_breaker_status() -> CircuitBreakerStatusResponse:
    """Inspect current circuit breaker state (CLOSED, OPEN, HALF_OPEN) for upstream dependencies."""
    return MonitoringService.get_circuit_breaker_status()


@router.post("/circuit-breaker/trip", response_model=CircuitBreakerStatusResponse)
async def trip_circuit_breaker(
    current_user: AuthenticatedUser = Depends(require_role(["ROLE_SYS_ADMIN"])),
) -> CircuitBreakerStatusResponse:
    """Simulate upstream failure burst to trip circuit breaker into OPEN state (Admin only)."""
    for _ in range(3):
        MonitoringService.record_upstream_failure()
    return MonitoringService.get_circuit_breaker_status()


@router.post("/circuit-breaker/reset", response_model=CircuitBreakerStatusResponse)
async def reset_circuit_breaker(
    current_user: AuthenticatedUser = Depends(require_role(["ROLE_SYS_ADMIN"])),
) -> CircuitBreakerStatusResponse:
    """Force reset circuit breaker back to CLOSED nominal state (Admin only)."""
    MonitoringService.reset_circuit_breaker()
    return MonitoringService.get_circuit_breaker_status()


@router.get("/alerts", response_model=AlertsListResponse)
async def list_alerts(
    include_resolved: bool = Query(True, description="Whether to include resolved alerts"),
    current_user: AuthenticatedUser = Depends(require_role(["ROLE_AUDITOR", "ROLE_SYS_ADMIN", "ROLE_VERIFIER"])),
) -> AlertsListResponse:
    """List operational and security alerts triggered by system subsystems."""
    return MonitoringService.get_alerts(include_resolved=include_resolved)


@router.post("/alerts/{alert_id}/resolve", response_model=OperationalAlertItem)
async def resolve_alert(
    alert_id: str,
    current_user: AuthenticatedUser = Depends(require_role(["ROLE_SYS_ADMIN", "ROLE_VERIFIER"])),
) -> OperationalAlertItem:
    """Acknowledge and mark an operational alert as resolved."""
    alert = MonitoringService.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert '{alert_id}' not found")
    return alert
