"""Schemas for Cryptographic Evidence Receipts and Public Verification."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReceiptIssuer(BaseModel):
    platform_id: str
    public_key_fingerprint: str


class ReceiptClaim(BaseModel):
    case_id: str
    claim_type: str
    evidence_sha256: str
    subject_id_hash: Optional[str] = None


class ReceiptDetermination(BaseModel):
    decision: str
    reason_codes: List[str]
    policy_version: str
    confidence_score: float
    permitted_scopes: List[str] = Field(default_factory=list)


class ReceiptIntegrity(BaseModel):
    merkle_root: str
    algorithm: str = "ECDSA_P256_SHA256"
    signature: str
    receipt_token: Optional[str] = None


class EvidenceReceiptResponse(BaseModel):
    schema_url: str = Field(alias="$schema", default="https://identity-trust.platform/schemas/v1/receipt.json")
    receipt_id: str
    case_id: Optional[str] = None
    status: str = "ACTIVE"
    issued_at: datetime
    issuer: ReceiptIssuer
    claim: ReceiptClaim
    determination: ReceiptDetermination
    integrity: ReceiptIntegrity


class ReceiptVerifyRequest(BaseModel):
    """Payload to independently verify an issued evidence receipt."""
    receipt_token: Optional[str] = None
    receipt_payload: Optional[Dict[str, Any]] = None


class ReceiptVerifyResponse(BaseModel):
    """Cryptographic verification result for an evidence receipt."""
    is_valid: bool
    receipt_id: str
    case_id: str
    decision: str
    issued_at: datetime
    issuer_id: str
    merkle_root: str
    message: str
