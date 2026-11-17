"""Application configuration module using Pydantic v2."""

import os
from typing import List
from pydantic import BaseModel, Field, model_validator


class Settings(BaseModel):
    PROJECT_NAME: str = "AI Identity & Digital Trust Automation Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    BACKEND_HOST: str = Field(default_factory=lambda: os.getenv("BACKEND_HOST", "0.0.0.0" if os.getenv("ENVIRONMENT") in ["staging", "production"] else "127.0.0.1"))
    BACKEND_PORT: int = Field(default_factory=lambda: int(os.getenv("BACKEND_PORT", "8000")))

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
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

    # Helpers
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    def is_staging(self) -> bool:
        return self.ENVIRONMENT.lower() == "staging"

    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() in ["development", "dev", "test", "local"]

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Strict validation for staging and production deployments."""
        env = self.ENVIRONMENT.lower()
        if env in ["production", "staging"]:
            # Disallow insecure default mock secrets in production/staging
            insecure_defaults = [
                "mock-service-role-key",
                "mock-anon-key",
                "super-secret-jwt-key-minimum-32-characters-test",
            ]
            if env == "production":
                if self.SUPABASE_JWT_SECRET in insecure_defaults or len(self.SUPABASE_JWT_SECRET) < 32:
                    raise ValueError(
                        f"CRITICAL: Production deployment rejected. Insecure or default SUPABASE_JWT_SECRET detected. "
                        f"Production secret must be >= 32 characters and cryptographically random."
                    )
                if not self.SUPABASE_URL.startswith("https://") or "mock.supabase.co" in self.SUPABASE_URL:
                    raise ValueError(
                        f"CRITICAL: Production deployment rejected. Insecure or mock SUPABASE_URL detected ({self.SUPABASE_URL}). "
                        f"Production requires HTTPS endpoint."
                    )
        return self


settings = Settings()
