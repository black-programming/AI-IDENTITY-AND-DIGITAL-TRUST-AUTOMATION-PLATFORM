"""Evidence Receipts API."""

from datetime import datetime, timezone
import hashlib
from fastapi import APIRouter, Depends

from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.receipts import (
    EvidenceReceiptResponse,
    ReceiptClaim,
    ReceiptDetermination,
    ReceiptIntegrity,
    ReceiptIssuer,
)

router = APIRouter()


@router.get("/receipts/{case_id}", response_model=EvidenceReceiptResponse, tags=["Receipts"])
async def get_receipt(
    case_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvidenceReceiptResponse:
    dummy_payload = f"{case_id}:{current_user.user_id}:v1.0.0"
    merkle_root = hashlib.sha256(dummy_payload.encode()).hexdigest()
    return EvidenceReceiptResponse(
        receipt_id=f"urn:uuid:{case_id}",
        issued_at=datetime.now(timezone.utc),
        issuer=ReceiptIssuer(
            platform_id="ai-identity-trust-engine-v1",
            public_key_fingerprint="SHA256:7e8a9f0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f",
        ),
        claim=ReceiptClaim(
            case_id=case_id,
            claim_type="SYNTH_NAT_ID_V1",
            evidence_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ),
        determination=ReceiptDetermination(
            decision="ALLOW",
            reason_codes=["DEC_ALLOW_SATISFIED"],
            policy_version="v1.0.0",
            confidence_score=0.96,
        ),
        integrity=ReceiptIntegrity(
            merkle_root=merkle_root,
            algorithm="ECDSA_P256_SHA256",
            signature="MEQCIQDe...4Xg==",
        ),
    )
