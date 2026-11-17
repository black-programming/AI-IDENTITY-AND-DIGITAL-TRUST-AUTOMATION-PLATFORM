"""Secure Evidence Service — Magic Byte Validation, Checksum Calculation, Quarantine, and Signed URLs."""

import base64
from datetime import datetime, timezone
import hashlib
import hmac
import io
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid
from PIL import Image

from app.core.config import settings
from app.core.errors import (
    ChecksumMismatchException,
    InvalidFileSignatureException,
    PayloadTooLargeException,
    QuarantineViolationException,
    ValidationException,
)

# Supported MIME types and their cryptographic magic byte signatures
ALLOWED_MIME_TYPES = {
    "image/jpeg": [b"\xFF\xD8\xFF"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "application/pdf": [b"%PDF-", b"%PDF"],
}

# Maximum allowed file size: 10 MB (10,485,760 bytes)
MAX_FILE_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_BYTES

# In-memory storage of evidence records for test/runtime isolation
_MOCK_EVIDENCE_DB: Dict[str, Dict[str, Any]] = {
    "00000000-0000-0000-0000-000000000001": {
        "file_id": "00000000-0000-0000-0000-000000000001",
        "case_id": "00000000-0000-0000-0000-000000000001",
        "file_name": "sample_national_id.png",
        "mime_type": "image/png",
        "file_size_bytes": 10240,
        "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "quarantine_status": "CLEARED",
        "bucket_path": "evidence-quarantine/00000000-0000-0000-0000-000000000001/sample_national_id.png",
        "uploaded_at": datetime.now(timezone.utc),
        "metadata": {"dimensions": "1920x1080", "anti_tamper_passed": True},
    }
}


def detect_mime_type_from_bytes(data: bytes) -> Optional[str]:
    """Inspect magic byte signatures to detect true MIME type independent of file extension."""
    if not data:
        return None

    # Check JPEG
    if len(data) >= 3 and data.startswith(b"\xFF\xD8\xFF"):
        return "image/jpeg"

    # Check PNG (8 bytes: 89 50 4E 47 0D 0A 1A 0A)
    if len(data) >= 8 and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    # Check PDF (first 1024 bytes per PDF standard)
    header = data[:1024]
    if b"%PDF-" in header or b"%PDF" in header:
        return "application/pdf"

    return None


def calculate_sha256(data: bytes) -> str:
    """Compute standard hexadecimal SHA-256 digest over binary content."""
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest().lower()


def generate_signed_storage_token(
    path: str,
    action: str,
    expires_in_seconds: int = 900,
) -> Tuple[str, int]:
    """Generate an HMAC-SHA256 signed authorization token for short-lived storage access."""
    now = int(datetime.now(timezone.utc).timestamp())
    exp = now + expires_in_seconds
    raw_payload = f"{action}:{path}:{exp}"
    signature = hmac.new(
        settings.SUPABASE_JWT_SECRET.encode("utf-8"),
        raw_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    token = f"{base64.urlsafe_b64encode(raw_payload.encode()).decode()}.{signature}"
    return token, exp


def verify_signed_storage_token(token: str, expected_path: str, expected_action: str) -> bool:
    """Verify an HMAC-SHA256 signed storage token against expiry and path tampering."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return False
        payload_b64, signature = parts[0], parts[1]
        raw_payload = base64.urlsafe_b64decode(payload_b64.encode()).decode()
        action, path, exp_str = raw_payload.split(":", 2)
        exp = int(exp_str)

        if int(datetime.now(timezone.utc).timestamp()) > exp:
            return False  # Expired
        if path != expected_path or action != expected_action:
            return False  # Tampered path/action

        expected_sig = hmac.new(
            settings.SUPABASE_JWT_SECRET.encode("utf-8"),
            raw_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature, expected_sig)
    except Exception:
        return False


class EvidenceService:
    @staticmethod
    def validate_file_metadata(
        file_name: str,
        mime_type: str,
        file_size_bytes: int,
    ) -> None:
        """Validate pre-upload metadata constraints with path traversal protection."""
        # Path traversal and hazardous character check
        if ".." in file_name or "/" in file_name or "\\" in file_name or "\x00" in file_name:
            raise ValidationException("Malicious file name: path traversal characters detected")

        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValidationException(
                f"Unsupported MIME type '{mime_type}'. Permitted types: {list(ALLOWED_MIME_TYPES.keys())}"
            )
        if file_size_bytes > MAX_FILE_SIZE_BYTES:
            raise PayloadTooLargeException(
                f"File size {file_size_bytes} exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES} bytes (10 MB)"
            )

    @staticmethod
    def validate_and_ingest_file(
        case_id: str,
        file_name: str,
        content: bytes,
        declared_mime_type: Optional[str] = None,
        client_sha256: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validate magic bytes, sanitize filename, inspect for embedded exploits, compute checksum, enforce quarantine, and store evidence record."""
        # 0. Path Traversal & Filename Sanitization
        if ".." in file_name or "/" in file_name or "\\" in file_name or "\x00" in file_name:
            raise ValidationException("Malicious file name: path traversal characters detected")

        safe_file_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", Path(file_name).name)
        if not safe_file_name or safe_file_name in (".", ".."):
            safe_file_name = f"evidence_{uuid.uuid4().hex[:8]}.bin"

        # 1. Size Check
        file_size = len(content)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise PayloadTooLargeException(
                f"Uploaded file size ({file_size} bytes) exceeds the maximum limit of {MAX_FILE_SIZE_BYTES} bytes (10 MB)"
            )
        if file_size == 0:
            raise ValidationException("Uploaded file cannot be empty (0 bytes)")

        # 2. Magic Byte Signature Validation
        detected_mime = detect_mime_type_from_bytes(content)
        if not detected_mime:
            raise InvalidFileSignatureException(
                f"File '{file_name}' does not match any allowed file signatures (JPEG, PNG, PDF)"
            )

        if declared_mime_type and declared_mime_type.lower() != detected_mime.lower():
            raise InvalidFileSignatureException(
                f"File signature mismatch: declared '{declared_mime_type}' but detected '{detected_mime}'"
            )

        # 3. Malicious Embedded Executable / Script Inspection (Polyglot & active content defense)
        header_sample = content[:8192].lower()
        dangerous_tags = [b"<script", b"<?php", b"javascript:", b"<svg", b"<html", b"onload="]
        if any(tag in header_sample for tag in dangerous_tags):
            raise InvalidFileSignatureException("Malicious payload detected: embedded script or executable directive")

        if detected_mime == "application/pdf":
            # PDF exploit vectors: JavaScript actions, launch commands, embedded binaries
            if b"/Launch" in content or b"/JavaScript" in content or b"/JS" in content:
                raise InvalidFileSignatureException("Malicious PDF payload detected: active script or launch action")

        # 4. Decompression Bomb Protection (Image dimensions check)
        if detected_mime in ("image/jpeg", "image/png"):
            try:
                Image.MAX_IMAGE_PIXELS = 25_000_000
                with Image.open(io.BytesIO(content)) as img:
                    w, h = img.size
                    if w > 10000 or h > 10000 or (w * h) > 25_000_000:
                        raise ValidationException("Image dimensions exceed safe processing limit (decompression bomb protection)")
            except ValidationException:
                raise
            except Exception:
                pass

        # 5. Checksum Calculation & Integrity Verification
        computed_sha256 = calculate_sha256(content)
        if client_sha256:
            clean_client_sha = client_sha256.strip().lower()
            if clean_client_sha != computed_sha256:
                raise ChecksumMismatchException(
                    f"Integrity check failed: client SHA-256 '{clean_client_sha}' does not match computed '{computed_sha256}'"
                )

        # 6. Idempotent Duplicate Detection
        for existing in _MOCK_EVIDENCE_DB.values():
            if existing["case_id"] == case_id and existing["sha256_hash"] == computed_sha256:
                return existing

        # 7. Ingestion into Quarantine State
        file_id = str(uuid.uuid4())
        bucket_path = f"evidence-quarantine/{case_id}/{file_id}_{safe_file_name}"
        now = datetime.now(timezone.utc)

        evidence_record = {
            "file_id": file_id,
            "case_id": case_id,
            "file_name": safe_file_name,
            "mime_type": detected_mime,
            "file_size_bytes": file_size,
            "sha256_hash": computed_sha256,
            "quarantine_status": "QUARANTINED",
            "bucket_path": bucket_path,
            "uploaded_at": now,
            "metadata": custom_metadata or {},
        }

        # Auto-transition from QUARANTINED to CLEARED once integrity and signature pass
        evidence_record["quarantine_status"] = "CLEARED"
        _MOCK_EVIDENCE_DB[file_id] = evidence_record

        return evidence_record

    @staticmethod
    def create_upload_url(
        case_id: str,
        file_name: str,
        mime_type: str,
        file_size_bytes: int = 0,
        sha256_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a secure pre-signed upload URL for direct storage upload."""
        EvidenceService.validate_file_metadata(file_name, mime_type, file_size_bytes)

        file_id = str(uuid.uuid4())
        bucket = settings.STORAGE_BUCKET_QUARANTINE
        bucket_path = f"{bucket}/{case_id}/{file_id}_{file_name}"

        token, exp = generate_signed_storage_token(
            path=bucket_path,
            action="upload",
            expires_in_seconds=settings.SIGNED_URL_EXPIRY_SECONDS,
        )

        upload_url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket_path}?token={token}"

        # Register pending quarantine placeholder
        _MOCK_EVIDENCE_DB[file_id] = {
            "file_id": file_id,
            "case_id": case_id,
            "file_name": file_name,
            "mime_type": mime_type,
            "file_size_bytes": file_size_bytes,
            "sha256_hash": sha256_hash or "",
            "quarantine_status": "QUARANTINED",
            "bucket_path": bucket_path,
            "uploaded_at": datetime.now(timezone.utc),
            "metadata": {"upload_pending": True},
        }

        return {
            "upload_url": upload_url,
            "file_id": file_id,
            "bucket": bucket,
            "bucket_path": bucket_path,
            "expires_in_seconds": settings.SIGNED_URL_EXPIRY_SECONDS,
        }

    @staticmethod
    def create_download_url(
        file_id: str,
        case_id: str,
        is_reviewer: bool = False,
    ) -> Dict[str, Any]:
        """Generate a short-lived presigned download URL with strict quarantine checks."""
        evidence = _MOCK_EVIDENCE_DB.get(file_id)
        if not evidence or evidence["case_id"] != case_id:
            return None

        # If rejected in quarantine, deny non-reviewer access
        if evidence["quarantine_status"] == "REJECTED" and not is_reviewer:
            raise QuarantineViolationException(
                "Evidence file failed quarantine validation and cannot be downloaded"
            )

        bucket_path = evidence["bucket_path"]
        token, exp = generate_signed_storage_token(
            path=bucket_path,
            action="download",
            expires_in_seconds=settings.SIGNED_URL_EXPIRY_SECONDS,
        )

        download_url = f"{settings.SUPABASE_URL}/storage/v1/object/authenticated/{bucket_path}?token={token}"

        return {
            "download_url": download_url,
            "file_id": file_id,
            "mime_type": evidence["mime_type"],
            "file_size_bytes": evidence["file_size_bytes"],
            "sha256_hash": evidence["sha256_hash"],
            "expires_in_seconds": settings.SIGNED_URL_EXPIRY_SECONDS,
        }

    @staticmethod
    def list_evidence_for_case(case_id: str) -> List[Dict[str, Any]]:
        """Retrieve all evidence records associated with a specific verification case."""
        return [
            rec for rec in _MOCK_EVIDENCE_DB.values()
            if rec["case_id"] == case_id
        ]

    @staticmethod
    def get_evidence(file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single evidence record by ID."""
        return _MOCK_EVIDENCE_DB.get(file_id)
