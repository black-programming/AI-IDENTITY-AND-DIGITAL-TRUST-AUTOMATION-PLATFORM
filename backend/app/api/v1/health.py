"""Health check endpoint for liveness and readiness probes."""

from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: datetime


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def check_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
    )
