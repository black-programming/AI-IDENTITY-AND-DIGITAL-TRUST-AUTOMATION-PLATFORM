"""Review Service — Reviewer Queue Management, Field Corrections, and Decision Recording."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from app.api.v1.cases import _MOCK_CASES_DB, _record_timeline_event
from app.core.errors import InvalidStateTransitionException, NotFoundException, ValidationException
from app.services.evidence_service import EvidenceService, _MOCK_EVIDENCE_DB
from app.services.ocr_service import OCRService, _MOCK_EXTRACTED_FIELDS_DB
from app.services.validation_engine import ValidationEngine

# In-memory store for reviewer corrections and manual decisions
_MOCK_CORRECTIONS_DB: Dict[str, List[Dict[str, Any]]] = {}
_MOCK_DECISIONS_DB: Dict[str, Dict[str, Any]] = {}

PRIORITY_WEIGHTS = {"URGENT": 4, "HIGH": 3, "NORMAL": 2, "LOW": 1}


class ReviewService:
    @classmethod
    def get_review_queue(
        cls,
        assigned_to_reviewer_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch pending verification cases requiring manual review, sorted by priority and FIFO."""
        pending: List[Dict[str, Any]] = []

        for case_id, case in _MOCK_CASES_DB.items():
            if case["status"] in ("Under Review", "Submitted", "Processing", "Action Required"):
                # If reviewer filter provided, filter by assigned reviewer
                if assigned_to_reviewer_id and case.get("assigned_reviewer_id") != assigned_to_reviewer_id:
                    continue

                # Check if case has validation flags or reason codes
                val_report = ValidationEngine.get_latest_validation(case_id) or {}
                reasons = val_report.get("reason_codes", [])

                pending.append(
                    {
                        "case_id": case["case_id"],
                        "user_id": case["user_id"],
                        "claim_type": case["claim_type"],
                        "status": case["status"],
                        "priority": case.get("priority", "NORMAL"),
                        "reason_codes": reasons,
                        "validation_outcome": val_report.get("overall_outcome"),
                        "assigned_reviewer_id": case.get("assigned_reviewer_id"),
                        "created_at": case["created_at"],
                        "updated_at": case["updated_at"],
                    }
                )

        # Sort: Highest priority first, then earliest created_at (FIFO)
        pending.sort(
            key=lambda c: (
                -PRIORITY_WEIGHTS.get(c["priority"].upper(), 0),
                c["created_at"],
            )
        )
        return pending

    @classmethod
    def get_workbench_data(cls, case_id: str) -> Dict[str, Any]:
        """Compile complete workbench inspection bundle for side-by-side human review."""
        case = _MOCK_CASES_DB.get(case_id)
        if not case:
            raise NotFoundException(f"Verification case '{case_id}' not found")

        # 1. Fetch Evidence Files with signed preview download URLs
        evidence_items = EvidenceService.list_evidence_for_case(case_id)
        workbench_evidence: List[Dict[str, Any]] = []
        for ev in evidence_items:
            download_meta = EvidenceService.create_download_url(
                file_id=ev["file_id"],
                case_id=case_id,
                is_reviewer=True,
            )
            workbench_evidence.append(
                {
                    "file_id": ev["file_id"],
                    "file_name": ev["file_name"],
                    "mime_type": ev["mime_type"],
                    "sha256_hash": ev["sha256_hash"],
                    "quarantine_status": ev["quarantine_status"],
                    "download_url": download_meta.get("download_url") if download_meta else None,
                }
            )

        # 2. Extracted Fields & Provenance
        summary = OCRService.get_case_summary(case_id)
        extracted_fields = summary.get("extracted_fields", {})
        fields_detail = summary.get("fields_detail", [])

        # 3. Deterministic Validation Report
        val_report = ValidationEngine.get_latest_validation(case_id)

        # 4. Corrections History
        corrections = _MOCK_CORRECTIONS_DB.get(case_id, [])

        return {
            "case_id": case["case_id"],
            "user_id": case["user_id"],
            "claim_type": case["claim_type"],
            "status": case["status"],
            "priority": case.get("priority", "NORMAL"),
            "assigned_reviewer_id": case.get("assigned_reviewer_id"),
            "created_at": case["created_at"],
            "evidence": workbench_evidence,
            "extracted_fields": extracted_fields,
            "fields_detail": fields_detail,
            "validation_report": val_report,
            "corrections_history": corrections,
            "permitted_decisions": ["ALLOW", "VERIFY", "RESTRICT", "BLOCK"],
        }

    @classmethod
    def apply_corrections(
        cls,
        case_id: str,
        reviewer_id: str,
        corrections: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Apply reviewer corrections to extracted fields and record tamper-evident audit trail."""
        case = _MOCK_CASES_DB.get(case_id)
        if not case:
            raise NotFoundException(f"Verification case '{case_id}' not found")

        if case["status"] in ("Verified", "Rejected", "Cancelled"):
            raise InvalidStateTransitionException(
                f"Cannot correct fields on terminal case with status '{case['status']}'"
            )

        case_summary = OCRService.get_case_summary(case_id)
        current_fields = case_summary.get("extracted_fields", {})
        now = datetime.now(timezone.utc)

        applied_records: List[Dict[str, Any]] = []

        if case_id not in _MOCK_CORRECTIONS_DB:
            _MOCK_CORRECTIONS_DB[case_id] = []

        for item in corrections:
            key = item["field_key"]
            new_val = item["corrected_value"]
            justification = item["justification"]
            prev_val = str(current_fields.get(key, ""))

            correction_record = {
                "correction_id": str(uuid.uuid4()),
                "case_id": case_id,
                "reviewer_id": reviewer_id,
                "field_key": key,
                "previous_value": prev_val,
                "corrected_value": new_val,
                "justification": justification,
                "corrected_at": now,
            }

            _MOCK_CORRECTIONS_DB[case_id].append(correction_record)
            applied_records.append(correction_record)

            # Update in-memory extracted fields store
            for file_fields in _MOCK_EXTRACTED_FIELDS_DB.values():
                for f in file_fields:
                    if f["field_key"] == key:
                        f["field_value"] = new_val
                        f["ocr_engine"] = f"Manual-Correction-by-{reviewer_id[:8]}"

            current_fields[key] = new_val

            # Log audit event in case timeline
            _record_timeline_event(
                case_id=case_id,
                from_status=case["status"],
                to_status=case["status"],
                triggered_by=reviewer_id,
                comment=f"Reviewer corrected field '{key}' from '{prev_val}' to '{new_val}'. Reason: {justification}",
            )

        return {
            "case_id": case_id,
            "reviewer_id": reviewer_id,
            "corrections_applied": applied_records,
            "updated_fields": current_fields,
            "corrected_at": now,
        }

    @classmethod
    def request_additional_evidence(
        cls,
        case_id: str,
        reviewer_id: str,
        reason_code: str,
        guidance: str,
    ) -> Dict[str, Any]:
        """Flag case as Action Required, prompting the user for new/cleaner evidence."""
        case = _MOCK_CASES_DB.get(case_id)
        if not case:
            raise NotFoundException(f"Verification case '{case_id}' not found")

        if case["status"] in ("Verified", "Rejected", "Cancelled"):
            raise InvalidStateTransitionException(
                f"Cannot request evidence on terminal case with status '{case['status']}'"
            )

        old_status = case["status"]
        case["status"] = "Action Required"
        case["current_decision"] = "VERIFY"
        case["updated_at"] = datetime.now(timezone.utc)

        _record_timeline_event(
            case_id=case_id,
            from_status=old_status,
            to_status="Action Required",
            triggered_by=reviewer_id,
            comment=f"Additional evidence requested ({reason_code}): {guidance}",
        )

        return {
            "case_id": case_id,
            "reviewer_id": reviewer_id,
            "status": "Action Required",
            "reason_code": reason_code,
            "guidance": guidance,
        }

    @classmethod
    def record_decision(
        cls,
        case_id: str,
        reviewer_id: str,
        decision: str,
        reason_code: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record manual review decision with mandatory reason code and execute state transition."""
        case = _MOCK_CASES_DB.get(case_id)
        if not case:
            raise NotFoundException(f"Verification case '{case_id}' not found")

        if case["status"] in ("Verified", "Rejected", "Cancelled"):
            raise InvalidStateTransitionException(
                f"Cannot record decision on terminal case with status '{case['status']}'"
            )

        valid_decisions = ("ALLOW", "VERIFY", "RESTRICT", "BLOCK")
        if decision.upper() not in valid_decisions:
            raise ValidationException(f"Invalid decision '{decision}'. Permitted: {valid_decisions}")

        old_status = case["status"]
        now = datetime.now(timezone.utc)

        # State transition mapping based on manual outcome
        decision_upper = decision.upper()
        if decision_upper == "ALLOW":
            new_status = "Verified"
        elif decision_upper == "BLOCK":
            new_status = "Rejected"
        elif decision_upper == "RESTRICT":
            new_status = "Restricted"
        else:  # VERIFY
            new_status = "Action Required"

        case["status"] = new_status
        case["current_decision"] = decision_upper
        case["assigned_reviewer_id"] = reviewer_id
        case["updated_at"] = now

        decision_record = {
            "decision_id": str(uuid.uuid4()),
            "case_id": case_id,
            "reviewer_id": reviewer_id,
            "decision": decision_upper,
            "reason_code": reason_code,
            "notes": notes or "",
            "new_status": new_status,
            "decided_at": now,
        }
        _MOCK_DECISIONS_DB[case_id] = decision_record

        _record_timeline_event(
            case_id=case_id,
            from_status=old_status,
            to_status=new_status,
            triggered_by=reviewer_id,
            comment=f"Reviewer manual decision: {decision_upper} (Reason: {reason_code}). Notes: {notes or 'None'}",
        )

        return decision_record
