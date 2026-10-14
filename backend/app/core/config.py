"""Application configuration module using Pydantic v2."""

import os
from typing import List
from pydantic import BaseModel, Field


class Settings(BaseModel):
    PROJECT_NAME: str = "AI Identity & Digital Trust Automation Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    BACKEND_HOST: str = Field(default_factory=lambda: os.getenv("BACKEND_HOST", "127.0.0.1"))
    BACKEND_PORT: int = Field(default_factory=lambda: int(os.getenv("BACKEND_PORT", "8000")))

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
    ]

    # Supabase (Server-side service_role key must NEVER be sent to client)
    SUPABASE_URL: str = Field(
        default_factory=lambda: os.getenv("SUPABASE_URL", "https://mock.supabase.co")
    )
    SUPABASE_ANON_KEY: str = Field(
        default_factory=lambda: os.getenv("SUPABASE_ANON_KEY", "mock-anon-key")
    )
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE_KEY", "mock-service-role-key")
    )
    SUPABASE_JWT_SECRET: str = Field(
        default_factory=lambda: os.getenv(
            "SUPABASE_JWT_SECRET", "super-secret-jwt-key-minimum-32-characters-test"
        )
    )

    # Storage & Signing
    STORAGE_BUCKET_QUARANTINE: str = Field(
        default_factory=lambda: os.getenv("STORAGE_BUCKET_QUARANTINE", "evidence-quarantine")
    )
    STORAGE_BUCKET_VERIFIED: str = Field(
        default_factory=lambda: os.getenv("STORAGE_BUCKET_VERIFIED", "evidence-verified")
    )
    SIGNED_URL_EXPIRY_SECONDS: int = Field(
        default_factory=lambda: int(os.getenv("SIGNED_URL_EXPIRY_SECONDS", "900"))
    )

    # Thresholds
    OCR_CONFIDENCE_THRESHOLD: float = 0.85
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB


settings = Settings()
