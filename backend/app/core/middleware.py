import json
import os
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
import uuid
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.logging import set_request_id

# Global rate limiter configuration
RATE_LIMIT_WINDOW_SECONDS = 60
DEFAULT_MAX_REQUESTS_PER_WINDOW = 120
SENSITIVE_MAX_REQUESTS_PER_WINDOW = 30

# In-memory sliding window request store: {identifier: [(timestamp, count)]}
_REQUEST_HISTORY: Dict[str, List[float]] = defaultdict(list)

# In-memory store for idempotency caching: {f"{client_key}:{idempotency_key}": {"status_code": int, "content": Any, "headers": dict}}
_IDEMPOTENCY_STORE: Dict[str, Dict[str, Any]] = {}

# Test bypass key
BYPASS_HEADER = "x-bypass-rate-limit"
BYPASS_SECRET = os.getenv("RATE_LIMIT_BYPASS_SECRET", "test-bypass-secret-phase17")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects defensive HTTP security headers into every outgoing response."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # 1. Prevent MIME Sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 2. Prevent Clickjacking / Framing
        response.headers["X-Frame-Options"] = "DENY"

        # 3. HTTP Strict Transport Security (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # 4. Content Security Policy (CSP)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none';"
        )

        # 5. X-XSS-Protection legacy defense
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 6. Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 7. Permissions Policy: Restrict sensitive device APIs
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"

        # 8. Server Obfuscation
        response.headers["Server"] = "DigitalTrustEngine"

        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Enforces sliding-window rate limits per client IP or authenticated subject."""

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next):
        # Allow disabling via environment or bypass header during heavy integration tests
        if not self.enabled or os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "false":
            return await call_next(request)

        # Check bypass header
        bypass_val = request.headers.get(BYPASS_HEADER)
        if bypass_val and bypass_val == BYPASS_SECRET:
            return await call_next(request)

        # Skip rate limiting for static asset and health check endpoints
        path = request.url.path
        if path.startswith(("/assets", "/canvaskit", "/icons", "/docs", "/openapi.json", "/api/v1/health")):
            return await call_next(request)

        # Resolve client identifier: IP or Forwarded IP
        client_ip = request.client.host if request.client else "127.0.0.1"
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        # Route-sensitive threshold
        is_sensitive = any(
            frag in path for frag in ("/predict", "/evaluate-case", "/evidence/direct-upload", "/evidence/upload-url", "/auth/login")
        )
        max_limit = SENSITIVE_MAX_REQUESTS_PER_WINDOW if is_sensitive else DEFAULT_MAX_REQUESTS_PER_WINDOW

        # Sliding window check
        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW_SECONDS
        key = f"{client_ip}:{path if is_sensitive else 'general'}"

        # Prune old timestamps
        timestamps = _REQUEST_HISTORY[key]
        _REQUEST_HISTORY[key] = [t for t in timestamps if t > window_start]

        if len(_REQUEST_HISTORY[key]) >= max_limit:
            retry_after = int(RATE_LIMIT_WINDOW_SECONDS - (now - _REQUEST_HISTORY[key][0])) + 1
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "detail": f"Too many requests. Limit is {max_limit} requests per minute.",
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + retry_after)),
                },
            )

        # Record this request
        _REQUEST_HISTORY[key].append(now)

        response: Response = await call_next(request)
        remaining = max(0, max_limit - len(_REQUEST_HISTORY[key]))
        response.headers["X-RateLimit-Limit"] = str(max_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


def reset_rate_limiter():
    """Clear in-memory rate limiter tracking state (used in testing)."""
    _REQUEST_HISTORY.clear()


def reset_idempotency_store():
    """Clear in-memory idempotency cache (used in testing)."""
    _IDEMPOTENCY_STORE.clear()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Propagates or generates correlation X-Request-ID and measures execution latency."""

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        set_request_id(req_id)
        start_time = time.perf_counter()

        try:
            response: Response = await call_next(request)
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time-Ms"] = str(duration_ms)

        # Record live telemetry metric
        try:
            from app.services.monitoring_service import MonitoringService
            MonitoringService.record_request_metric(response.status_code, duration_ms)
        except Exception:
            pass

        return response


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Enforces deduplication for mutating requests via Idempotency-Key header."""

    async def dispatch(self, request: Request, call_next):
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return await call_next(request)

        idempotency_key = request.headers.get("idempotency-key")
        if not idempotency_key:
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        cache_key = f"{client_ip}:{idempotency_key}"

        # 1. Cache HIT: Return previously computed response
        if cache_key in _IDEMPOTENCY_STORE:
            cached = _IDEMPOTENCY_STORE[cache_key]
            return JSONResponse(
                status_code=cached["status_code"],
                content=cached["content"],
                headers={
                    **cached.get("headers", {}),
                    "X-Cache-Lookup": "HIT",
                    "Idempotency-Key": idempotency_key,
                },
            )

        # 2. Cache MISS: Execute and cache
        response = await call_next(request)

        # Cache definitive responses (< 500)
        if response.status_code < 500:
            body_chunks = [chunk async for chunk in response.body_iterator]
            body_bytes = b"".join(body_chunks)
            try:
                parsed_content = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                parsed_content = body_bytes.decode("utf-8", errors="replace")

            _IDEMPOTENCY_STORE[cache_key] = {
                "status_code": response.status_code,
                "content": parsed_content,
                "headers": {"content-type": response.headers.get("content-type", "application/json")},
            }

            headers_dict = dict(response.headers)
            headers_dict["X-Cache-Lookup"] = "MISS"
            headers_dict["Idempotency-Key"] = idempotency_key

            return JSONResponse(
                status_code=response.status_code,
                content=parsed_content,
                headers=headers_dict,
            )

        return response
