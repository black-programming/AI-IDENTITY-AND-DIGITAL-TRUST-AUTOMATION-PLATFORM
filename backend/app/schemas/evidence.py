"""Pydantic schemas for evidence file upload, quarantine, and signed URLs."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvidenceUploadUrlRequest(BaseModel):
    case_id: str = Field(..., description="ID of the verification case this file belongs to")
    file_name: str = Field(..., description="Original name of the evidence file")
    mime_type: str = Field(..., description="MIME type, e.g. image/jpeg, image/png, application/pdf")
    file_size_bytes: Optional[int] = Field(0, description="Declared file size in bytes (max 10MB)")
    sha256_hash: Optional[str] = Field(None, description="Pre-computed SHA-256 hash for integrity validation")


class EvidenceUploadUrlResponse(BaseModel):
    upload_url: str = Field(..., description="Time-limited presigned URL for direct storage upload")
    file_id: str = Field(..., description="Generated UUID for the evidence record")
    bucket: str = Field(..., description="Target private bucket (evidence-quarantine)")
    bucket_path: str = Field(..., description="Target object path within the private bucket")
    expires_in_seconds: int = Field(900, description="Validity lifetime of signed upload URL in seconds")


class EvidenceFileResponse(BaseModel):
    file_id: str
    case_id: str
    file_name: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str
    quarantine_status: str
    bucket_path: str
    uploaded_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceListResponse(BaseModel):
    evidence: List[EvidenceFileResponse]
    total: int


class EvidenceDownloadUrlResponse(BaseModel):
    download_url: str
    file_id: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str
    expires_in_seconds: int = 900


class EvidenceVerifyRequest(BaseModel):
    sha256_hash: str = Field(..., description="Computed client SHA-256 checksum to confirm against backend digest")
    file_size_bytes: Optional[int] = Field(None, description="Uploaded file size in bytes")


class EvidenceVerifyResponse(BaseModel):
    file_id: str
    sha256_verified: bool
    quarantine_status: str
    message: str
