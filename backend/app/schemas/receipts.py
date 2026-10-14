"""Schemas for Cryptographic Evidence Receipts."""

from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ReceiptIssuer(BaseModel):
    platform_id: str
    public_key_fingerprint: str


class ReceiptClaim(BaseModel):
    case_id: str
    claim_type: str
    evidence_sha256: str


class ReceiptDetermination(BaseModel):
    decision: str
    reason_codes: List[str]
    policy_version: str
    confidence_score: float


class ReceiptIntegrity(BaseModel):
    merkle_root: str
    algorithm: str = "ECDSA_P256_SHA256"
    signature: str


class EvidenceReceiptResponse(BaseModel):
    schema_url: str = Field(alias="$schema", default="https://identity-trust.platform/schemas/v1/receipt.json")
    receipt_id: str
    issued_at: datetime
    issuer: ReceiptIssuer
    claim: ReceiptClaim
    determination: ReceiptDetermination
    integrity: ReceiptIntegrity
