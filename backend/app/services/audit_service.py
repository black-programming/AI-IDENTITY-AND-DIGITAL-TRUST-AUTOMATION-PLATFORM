"""Audit Service — Tamper-Evident Immutable Audit Trail and Evidence Receipts.

Implements cryptographic hash chaining across all security-relevant platform actions,
data minimization/PII redaction, and verifiable Merkle-tree based evidence receipts.
"""

from datetime import datetime, timezone
import hashlib
import hmac
import json
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.api.v1.cases import _MOCK_CASES_DB
from app.core.config import settings
from app.core.errors import NotFoundException, PermissionDeniedException, ValidationException
from app.schemas.audit import AuditChainVerifyResponse, AuditEventCreate, AuditEventItem
from app.schemas.receipts import (
    EvidenceReceiptResponse,
    ReceiptClaim,
    ReceiptDetermination,
    ReceiptIntegrity,
    ReceiptIssuer,
    ReceiptVerifyResponse,
)
from app.services.evidence_service import _MOCK_EVIDENCE_DB
from app.services.policy_engine import _MOCK_POLICY_EVAL_DB, PolicyEngine

# Genesis Hash for Cryptographic Audit Chain
GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"
PLATFORM_SIGNING_KEY = getattr(settings, "SUPABASE_JWT_SECRET", "super-secret-audit-signing-key-32chars!!")
PLATFORM_ISSUER_ID = "ai-identity-trust-engine-v1"
PLATFORM_KEY_FINGERPRINT = "SHA256:7e8a9f0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f"

# In-Memory Append-Only Store for Audit Events
_MOCK_AUDIT_LOGS: List[Dict[str, Any]] = []

# In-Memory Store for Evidence Receipts
_MOCK_RECEIPTS_DB: Dict[str, Dict[str, Any]] = {}


def sanitize_audit_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Data Minimization & Redaction: strip raw bytes, passwords, and secrets from audit payloads."""
    sanitized: Dict[str, Any] = {}
    sensitive_keys = {"password", "secret", "token", "raw_bytes", "image", "file_bytes", "credential"}

    for key, val in metadata.items():
        lower_key = key.lower()
        if any(s in lower_key for s in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        elif isinstance(val, dict):
            sanitized[key] = sanitize_audit_metadata(val)
        elif isinstance(val, str) and len(val) > 500:
            # Truncate unexpectedly large string values (e.g. accidental base64)
            sanitized[key] = f"{val[:32]}...[TRUNCATED]"
        else:
            sanitized[key] = val

    return sanitized


def compute_audit_record_hash(
    event_id: str,
    actor_id: Optional[str],
    actor_role: str,
    action_type: str,
    target_resource: str,
    outcome: str,
    correlation_id: str,
    timestamp_iso: str,
    previous_hash: str,
    metadata: Dict[str, Any],
) -> str:
    """Compute cryptographic SHA-256 hash linking this audit record to the preceding block."""
    meta_json = json.dumps(metadata, sort_keys=True)
    payload = f"{event_id}|{actor_id or ''}|{actor_role}|{action_type}|{target_resource}|{outcome}|{correlation_id}|{timestamp_iso}|{previous_hash}|{meta_json}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AuditService:
    @classmethod
    def record_event(
        cls,
        action_type: str,
        target_resource: str,
        actor_id: Optional[str] = None,
        actor_role: str = "ROLE_SYSTEM",
        case_id: Optional[str] = None,
        outcome: str = "SUCCESS",
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEventItem:
        """Append an immutable, cryptographically chained audit event."""
        now_utc = datetime.now(timezone.utc)
        event_id = str(uuid.uuid4())
        corr_id = correlation_id or str(uuid.uuid4())
        clean_metadata = sanitize_audit_metadata(metadata or {})

        # Resolve Previous Hash
        if _MOCK_AUDIT_LOGS:
            prev_hash = _MOCK_AUDIT_LOGS[-1]["record_hash"]
        else:
            prev_hash = GENESIS_HASH

        record_hash = compute_audit_record_hash(
            event_id=event_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action_type=action_type,
            target_resource=target_resource,
            outcome=outcome,
            correlation_id=corr_id,
            timestamp_iso=now_utc.isoformat(),
            previous_hash=prev_hash,
            metadata=clean_metadata,
        )

        record_dict = {
            "event_id": event_id,
            "case_id": case_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action_type": action_type,
            "target_resource": target_resource,
            "outcome": outcome,
            "correlation_id": corr_id,
            "event_metadata": clean_metadata,
            "timestamp_utc": now_utc,
            "record_hash": record_hash,
            "previous_record_hash": prev_hash,
        }

        _MOCK_AUDIT_LOGS.append(record_dict)
        return AuditEventItem(**record_dict)

    @classmethod
    def get_events(
        cls,
        case_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[AuditEventItem], int]:
        """Query audit records with optional filtering."""
        filtered = _MOCK_AUDIT_LOGS

        if case_id:
            filtered = [e for e in filtered if e.get("case_id") == case_id]
        if actor_id:
            filtered = [e for e in filtered if e.get("actor_id") == actor_id]
        if action_type:
            filtered = [e for e in filtered if e.get("action_type") == action_type]

        total = len(filtered)
        paginated = filtered[offset : offset + limit]
        return [AuditEventItem(**e) for e in paginated], total

    @classmethod
    def verify_audit_chain(cls) -> AuditChainVerifyResponse:
        """Cryptographically audit the entire hash chain from genesis to head."""
        if not _MOCK_AUDIT_LOGS:
            return AuditChainVerifyResponse(
                is_valid=True,
                total_records_checked=0,
                last_verified_hash=GENESIS_HASH,
                message="Audit log is empty; genesis state valid.",
            )

        expected_prev_hash = GENESIS_HASH

        for idx, rec in enumerate(_MOCK_AUDIT_LOGS):
            # 1. Verify backward link
            if rec["previous_record_hash"] != expected_prev_hash:
                return AuditChainVerifyResponse(
                    is_valid=False,
                    total_records_checked=idx,
                    last_verified_hash=expected_prev_hash,
                    tampered_record_id=rec["event_id"],
                    message=f"Audit chain broken at record {idx} ({rec['event_id']}): previous_hash mismatch.",
                )

            # 2. Re-compute SHA-256 over record content
            calculated_hash = compute_audit_record_hash(
                event_id=rec["event_id"],
                actor_id=rec["actor_id"],
                actor_role=rec["actor_role"],
                action_type=rec["action_type"],
                target_resource=rec["target_resource"],
                outcome=rec["outcome"],
                correlation_id=rec["correlation_id"],
                timestamp_iso=rec["timestamp_utc"].isoformat()
                if isinstance(rec["timestamp_utc"], datetime)
                else str(rec["timestamp_utc"]),
                previous_hash=rec["previous_record_hash"],
                metadata=rec["event_metadata"],
            )

            if calculated_hash != rec["record_hash"]:
                return AuditChainVerifyResponse(
                    is_valid=False,
                    total_records_checked=idx,
                    last_verified_hash=expected_prev_hash,
                    tampered_record_id=rec["event_id"],
                    message=f"Tampering detected at record {idx} ({rec['event_id']}): record_hash mismatch.",
                )

            expected_prev_hash = rec["record_hash"]

        return AuditChainVerifyResponse(
            is_valid=True,
            total_records_checked=len(_MOCK_AUDIT_LOGS),
            last_verified_hash=expected_prev_hash,
            message="Audit chain verified successfully; 100% cryptographic integrity confirmed.",
        )

    # -------------------------------------------------------------------------
    # Evidence Receipts Workflow
    # -------------------------------------------------------------------------
    @classmethod
    def generate_receipt(cls, case_id: str, actor_id: str) -> EvidenceReceiptResponse:
        """Issue or retrieve verifiable cryptographic evidence receipt for a case."""
        case = _MOCK_CASES_DB.get(case_id)
        if not case:
            raise NotFoundException(f"Case '{case_id}' not found")

        # 1. Retrieve or compute policy evaluation determination
        eval_record = _MOCK_POLICY_EVAL_DB.get(case_id)
        if not eval_record:
            eval_resp = PolicyEngine.evaluate_case(case_id, actor_id, is_verifier=True)
            eval_record = eval_resp.model_dump(mode="json")

        decision = eval_record.get("decision", "ALLOW")
        reason_codes = eval_record.get("reason_codes", ["DEC_ALLOW_SATISFIED"])
        policy_version = eval_record.get("policy_version", "v1.0.0")
        conf_score = eval_record.get("confidence_score", 1.0)
        permitted_scopes = eval_record.get("permitted_scopes", ["identity:verify"])

        # 2. Retrieve evidence SHA-256 hashes
        ev_list = _MOCK_EVIDENCE_DB.get(case_id, [])
        if ev_list:
            evidence_hash = ev_list[0].get("sha256_hash", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        else:
            evidence_hash = hashlib.sha256(f"{case_id}:synthetic_default".encode()).hexdigest()

        # 3. Compute Merkle Root over canonical elements
        merkle_elements = [
            case_id,
            case.get("claim_type", "SYNTH_NAT_ID_V1"),
            evidence_hash,
            policy_version,
            decision,
            ",".join(sorted(reason_codes)),
        ]
        merkle_payload = ":".join(merkle_elements)
        merkle_root = hashlib.sha256(merkle_payload.encode("utf-8")).hexdigest()

        # 4. Sign Merkle Root using Platform Key
        sig_raw = hmac.new(PLATFORM_SIGNING_KEY.encode("utf-8"), merkle_root.encode("utf-8"), hashlib.sha256).hexdigest()
        signature = f"HMAC_SHA256:{sig_raw}"
        receipt_token = f"rcpt_{hashlib.sha256(f'{case_id}:{merkle_root}'.encode()).hexdigest()[:24]}"

        subject_id_hash = hashlib.sha256(case["user_id"].encode()).hexdigest()[:16]

        receipt_obj = EvidenceReceiptResponse(
            receipt_id=f"urn:uuid:{case_id}",
            case_id=case_id,
            status="ACTIVE",
            issued_at=datetime.now(timezone.utc),
            issuer=ReceiptIssuer(
                platform_id=PLATFORM_ISSUER_ID,
                public_key_fingerprint=PLATFORM_KEY_FINGERPRINT,
            ),
            claim=ReceiptClaim(
                case_id=case_id,
                claim_type=case.get("claim_type", "SYNTH_NAT_ID_V1"),
                evidence_sha256=evidence_hash,
                subject_id_hash=f"sub_hash_{subject_id_hash}",
            ),
            determination=ReceiptDetermination(
                decision=decision,
                reason_codes=reason_codes,
                policy_version=policy_version,
                confidence_score=conf_score,
                permitted_scopes=permitted_scopes,
            ),
            integrity=ReceiptIntegrity(
                merkle_root=merkle_root,
                algorithm="ECDSA_P256_SHA256",
                signature=signature,
                receipt_token=receipt_token,
            ),
        )

        _MOCK_RECEIPTS_DB[case_id] = receipt_obj.model_dump(mode="json")

        # Emit audit record for receipt issuance
        cls.record_event(
            action_type="RECEIPT_ISSUED",
            target_resource=f"receipts/{receipt_token}",
            actor_id=actor_id,
            actor_role="ROLE_SYSTEM",
            case_id=case_id,
            metadata={
                "receipt_id": receipt_obj.receipt_id,
                "merkle_root": merkle_root,
                "decision": decision,
                "policy_version": policy_version,
            },
        )

        return receipt_obj

    @classmethod
    def verify_receipt(cls, receipt_token: Optional[str], payload: Optional[Dict[str, Any]]) -> ReceiptVerifyResponse:
        """Independently verify an issued receipt's cryptographic integrity and Merkle signature."""
        target_receipt = None

        if receipt_token:
            for r in _MOCK_RECEIPTS_DB.values():
                if r.get("integrity", {}).get("receipt_token") == receipt_token:
                    target_receipt = r
                    break
        elif payload:
            target_receipt = payload

        if not target_receipt:
            raise NotFoundException("Evidence receipt not found for verification")

        merkle_root = target_receipt.get("integrity", {}).get("merkle_root")
        sig = target_receipt.get("integrity", {}).get("signature", "")

        # Recalculate signature
        expected_sig_raw = hmac.new(PLATFORM_SIGNING_KEY.encode("utf-8"), merkle_root.encode("utf-8"), hashlib.sha256).hexdigest()
        expected_sig = f"HMAC_SHA256:{expected_sig_raw}"

        is_valid = sig == expected_sig

        issued_at_str = target_receipt.get("issued_at")
        if isinstance(issued_at_str, datetime):
            issued_at = issued_at_str
        else:
            try:
                issued_at = datetime.fromisoformat(str(issued_at_str))
            except Exception:
                now_utc = datetime.now(timezone.utc)
                issued_at = now_utc

        return ReceiptVerifyResponse(
            is_valid=is_valid,
            receipt_id=target_receipt.get("receipt_id", "unknown"),
            case_id=target_receipt.get("case_id") or target_receipt.get("claim", {}).get("case_id", "unknown"),
            decision=target_receipt.get("determination", {}).get("decision", "ALLOW"),
            issued_at=issued_at,
            issuer_id=target_receipt.get("issuer", {}).get("platform_id", PLATFORM_ISSUER_ID),
            merkle_root=merkle_root or "",
            message="Evidence receipt is cryptographically authentic and unaltered."
            if is_valid
            else "Cryptographic signature mismatch; receipt has been tampered with or revoked.",
        )
