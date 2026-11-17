"""Main FastAPI Application entrypoint with unified Flutter Web serving."""

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import PlatformException, platform_exception_handler
from app.core.middleware import (
    IdempotencyMiddleware,
    RateLimiterMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Correlation Request ID and Execution Latency Tracker
    app.add_middleware(RequestIDMiddleware)

    # Idempotency Protection for Mutating State Requests
    app.add_middleware(IdempotencyMiddleware)

    # Defensive Security Headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Adaptive Rate Limiter & Abuse Control
    app.add_middleware(RateLimiterMiddleware)

    # Set up CORS with explicit origin constraints
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    app.add_exception_handler(PlatformException, platform_exception_handler)

    # Include V1 Routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Locate the built Flutter Web bundle
    # Root is two levels up from backend/app (i.e. workspace root / frontend / build / web)
    web_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "build" / "web"

    if web_dir.exists():
        assets_dir = web_dir / "assets"
        canvaskit_dir = web_dir / "canvaskit"
        icons_dir = web_dir / "icons"

        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="flutter_assets")
        if canvaskit_dir.exists():
            app.mount("/canvaskit", StaticFiles(directory=str(canvaskit_dir)), name="flutter_canvaskit")
        if icons_dir.exists():
            app.mount("/icons", StaticFiles(directory=str(icons_dir)), name="flutter_icons")

        # Top-level Flutter SPA route
        @app.get("/{full_path:path}")
        async def serve_flutter_spa(full_path: str):
            # Check if requested path is a specific static file in build/web
            target_file = web_dir / full_path
            if full_path and target_file.is_file():
                return FileResponse(target_file)
            # Default fallback: serve index.html for Single-Page Application routing
            return FileResponse(web_dir / "index.html")

    return app


app = create_application()
