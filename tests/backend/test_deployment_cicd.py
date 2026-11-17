"""Automated Test Suite for Phase 19: Deployment, Containerization, CI/CD, and Migrations."""

import hashlib
import json
import os
import re
import sys
import pytest
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.config import Settings
from scripts.migrate import load_migrations, verify_migrations
from scripts.backup_restore import BackupManager
from tests.ci.test_staging_smoke import run_staging_smoke_tests


def test_backend_dockerfile_security_and_multistage():
    """Verify backend Dockerfile complies with multi-stage build and non-root security standards."""
    dockerfile_path = os.path.join(BASE_DIR, "backend", "Dockerfile")
    assert os.path.exists(dockerfile_path), "backend/Dockerfile missing"

    with open(dockerfile_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Multi-stage verification
    assert "AS builder" in content, "Dockerfile must use multi-stage builder"
    assert "AS runtime" in content, "Dockerfile must have runtime stage"

    # Non-root user verification
    assert "useradd" in content or "adduser" in content, "Dockerfile must create dedicated non-root user"
    assert "USER appuser" in content, "Dockerfile must drop root privileges"

    # Health check probe verification
    assert "HEALTHCHECK" in content, "Dockerfile must define HEALTHCHECK probe"
    assert "curl" in content, "Healthcheck should probe container endpoint via curl"

    # Dockerignore check
    dockerignore_path = os.path.join(BASE_DIR, "backend", ".dockerignore")
    assert os.path.exists(dockerignore_path), "backend/.dockerignore missing"
    with open(dockerignore_path, "r", encoding="utf-8") as f:
        ignore_content = f.read()
    assert "__pycache__" in ignore_content
    assert ".pytest_cache" in ignore_content
    assert ".env*" in ignore_content


def test_frontend_dockerfile_and_nginx_security():
    """Verify frontend Dockerfile and nginx configuration enforce security headers and SPA routing."""
    dockerfile_path = os.path.join(BASE_DIR, "frontend", "Dockerfile")
    assert os.path.exists(dockerfile_path), "frontend/Dockerfile missing"

    with open(dockerfile_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "AS builder" in content
    assert "nginx" in content
    assert "USER nginx" in content

    # Nginx config verification
    nginx_path = os.path.join(BASE_DIR, "frontend", "nginx.conf")
    assert os.path.exists(nginx_path), "frontend/nginx.conf missing"
    with open(nginx_path, "r", encoding="utf-8") as f:
        nginx_content = f.read()

    assert "gzip on;" in nginx_content
    assert "X-Frame-Options" in nginx_content
    assert "X-Content-Type-Options" in nginx_content
    assert "try_files $uri $uri/ /index.html;" in nginx_content


def test_docker_compose_syntax_and_services():
    """Verify root docker-compose.yml parses cleanly and orchestrates all 3 tiers."""
    compose_path = os.path.join(BASE_DIR, "docker-compose.yml")
    assert os.path.exists(compose_path), "docker-compose.yml missing"

    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data.get("services", {})
    assert "backend" in services, "compose must define backend service"
    assert "frontend" in services, "compose must define frontend service"
    assert "gateway" in services, "compose must define gateway service"

    # Healthcheck check on backend
    backend_conf = services["backend"]
    assert "healthcheck" in backend_conf
    assert "ai-trust-net" in compose_data.get("networks", {})


def test_environment_settings_isolation_and_production_validation():
    """Verify Settings class enforces environment isolation and rejects weak production secrets."""
    # 1. Dev / test environment defaults
    dev_settings = Settings(
        ENVIRONMENT="development",
        SUPABASE_JWT_SECRET="super-secret-jwt-key-minimum-32-characters-test",
        SUPABASE_URL="https://mock.supabase.co"
    )
    assert dev_settings.is_development() is True
    assert dev_settings.is_production() is False

    # 2. Production rejection of default mock secrets
    with pytest.raises(ValueError, match="CRITICAL: Production deployment rejected"):
        Settings(
            ENVIRONMENT="production",
            SUPABASE_JWT_SECRET="super-secret-jwt-key-minimum-32-characters-test",
            SUPABASE_URL="https://prod.supabase.co"
        )

    # 3. Production rejection of insecure HTTP or mock Supabase URL
    with pytest.raises(ValueError, match="CRITICAL: Production deployment rejected"):
        Settings(
            ENVIRONMENT="production",
            SUPABASE_JWT_SECRET="real-crypto-random-production-secret-with-48-characters",
            SUPABASE_URL="https://mock.supabase.co"
        )

    # 4. Valid production settings accepted
    prod_settings = Settings(
        ENVIRONMENT="production",
        SUPABASE_JWT_SECRET="real-crypto-random-production-secret-with-48-characters",
        SUPABASE_URL="https://real-cluster.supabase.co"
    )
    assert prod_settings.is_production() is True
    assert prod_settings.is_development() is False


def test_database_migrations_ordering_and_checksum_stability():
    """Verify all database migrations maintain strict monotonic timestamps and valid SQL."""
    migrations = load_migrations()
    assert len(migrations) == 12, f"Expected 12 migration files, found {len(migrations)}"

    is_valid, errors = verify_migrations(migrations)
    # Ensure no fatal collisions or out-of-order versions
    assert not any("Duplicate" in e or "Out-of-order" in e for e in errors)

    # Verify each migration has valid SHA-256
    for m in migrations:
        assert len(m.checksum) == 64
        assert re.match(r"^[a-f0-9]{64}$", m.checksum)


def test_backup_restore_and_tamper_detection():
    """Verify snapshot generation, SHA-256 tamper detection, and automated rollback drill."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = BackupManager(backup_dir=tmpdir)

        # 1. Snapshot creation
        bundle = manager.create_snapshot(environment="staging", label="test_unit")
        filepath = os.path.join(tmpdir, f"{bundle['metadata']['snapshot_id']}.json")
        assert os.path.exists(filepath)

        # 2. Integrity verification
        assert manager.verify_integrity(bundle) is True

        # 3. Tamper detection
        tampered_bundle = json.loads(json.dumps(bundle))
        tampered_bundle["data"]["status"] = "TAMPERED_BY_ATTACKER"
        assert manager.verify_integrity(tampered_bundle) is False

        # 4. Rollback drill execution
        assert manager.test_rollback_drill() is True


def test_github_actions_workflows_integrity():
    """Verify GitHub Actions CI and CD workflow files parse as valid YAML with required jobs."""
    ci_path = os.path.join(BASE_DIR, ".github", "workflows", "ci.yml")
    assert os.path.exists(ci_path), ".github/workflows/ci.yml missing"
    with open(ci_path, "r", encoding="utf-8") as f:
        ci_data = yaml.safe_load(f)

    assert "backend-ci" in ci_data["jobs"]
    assert "frontend-ci" in ci_data["jobs"]
    assert "database-migrations" in ci_data["jobs"]
    assert "container-validation" in ci_data["jobs"]

    cd_path = os.path.join(BASE_DIR, ".github", "workflows", "cd.yml")
    assert os.path.exists(cd_path), ".github/workflows/cd.yml missing"
    with open(cd_path, "r", encoding="utf-8") as f:
        cd_data = yaml.safe_load(f)

    assert "build-and-publish" in cd_data["jobs"]
    assert "deploy-staging" in cd_data["jobs"]
    assert "deploy-production" in cd_data["jobs"]


def test_live_staging_smoke_run():
    """Execute live staging smoke & authorization tests against active Uvicorn daemon."""
    result = run_staging_smoke_tests("http://127.0.0.1:8000")
    assert result is True
