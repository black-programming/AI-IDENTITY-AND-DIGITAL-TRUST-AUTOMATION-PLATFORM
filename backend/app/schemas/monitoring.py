"""Schemas for Phase 18 Operational Monitoring, Reliability Metrics, and Alerting."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ComponentHealthItem(BaseModel):
    """Health evaluation for a specific internal component or upstream dependency."""
    name: str = Field(..., description="E.g. api, database, storage, ocr_engine, policy_engine, audit_chain")
    status: str = Field(..., description="HEALTHY, DEGRADED, UNAVAILABLE")
    latency_ms: float = Field(..., description="Observed round-trip ping latency in milliseconds")
    details: str = Field(..., description="Diagnostic diagnostic summary")


class SystemHealthResponse(BaseModel):
    """Overall system health evaluation across all core subsystems."""
    status: str = Field(..., description="HEALTHY, DEGRADED, CRITICAL")
    version: str
    environment: str
    uptime_seconds: float
    components: Dict[str, ComponentHealthItem]
    timestamp: datetime


class OperationalMetricsResponse(BaseModel):
    """Live operational telemetry and traffic metrics."""
    total_requests: int
    status_2xx_count: int
    status_4xx_count: int
    status_5xx_count: int
    error_rate_percentage: float
    average_latency_ms: float
    active_verification_cases: int
    pending_human_review_count: int
    circuit_breaker_state: str = Field("CLOSED", description="CLOSED (normal), OPEN (tripped), HALF_OPEN (recovering)")
    timestamp: datetime


class OperationalAlertItem(BaseModel):
    """Recorded operational or security incident alert."""
    alert_id: str
    severity: str = Field(..., description="INFO, WARNING, CRITICAL")
    source: str = Field(..., description="E.g. AUDIT_LEDGER, OCR_SERVICE, RATE_LIMITER, HTTP_SERVER")
    message: str
    triggered_at: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertsListResponse(BaseModel):
    """List of system operational alerts."""
    alerts: List[OperationalAlertItem]
    total_unresolved: int


class CircuitBreakerStatusResponse(BaseModel):
    """Circuit breaker state for upstream integrations."""
    service_name: str
    state: str = Field(..., description="CLOSED, OPEN, HALF_OPEN")
    consecutive_failures: int
    failure_threshold: int
    cooldown_seconds: int
    fallback_active: bool
