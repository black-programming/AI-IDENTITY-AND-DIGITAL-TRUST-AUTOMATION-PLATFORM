# AI Identity & Digital Trust Automation Platform
## Platform User Guide & Operator Manual

**Version:** 1.0.0  
**Target Release:** Production Release Candidate (v1.0.0)  
**Applicable Roles:** Individual Applicants, Enterprise Administrators, Trust Officers / Reviewers, Compliance Auditors, and System Operators

---

## 1. System Overview & Philosophy

The **AI Identity & Digital Trust Automation Platform** is an enterprise-grade platform designed to evaluate identity claims, document authenticity, organizational employment, and autonomous AI-agent authorizations.

### Core Philosophy: Contextual Trust Decisions
Platform decisions evaluate a **specific action and context**, strictly avoiding definitive judgments on a person's character or identity. The 4 standard outcomes are:
- `ALLOW`: The requested action fully satisfies applicable policies and evidence criteria.
- `VERIFY`: Inconclusive evidence, requiring human reviewer inspection or supplemental documentation.
- `RESTRICT`: The action is permitted under strictly reduced, time-bounded privileges.
- `BLOCK`: The requested action is denied under the active security policy.

---

## 2. User Journey Guides by Persona

### 2.1 Individual Subject / Applicant

#### Step 1: Case Inception
1. Authenticate using Supabase credentials (email/password or verified OAuth).
2. Submit a new verification case via `POST /api/v1/cases`:
   ```json
   {
     "title": "Identity Claim Verification",
     "claim_type": "SYNTH_NAT_ID_V1",
     "priority": "HIGH"
   }
   ```
3. An immutable `case_id` is assigned and entered into `Draft` / `SUBMITTED` state.

#### Step 2: Evidence Upload & Quarantine Security
1. Request a time-limited presigned upload URL via `POST /api/v1/cases/{case_id}/evidence/upload-url` or upload directly via `POST /api/v1/cases/{case_id}/evidence/upload`.
2. All uploads are placed in the private `evidence-quarantine` storage bucket.
3. Automated inspection verifies magic byte signatures (PNG, JPEG, PDF), enforces 10 MB payload limits, blocks path traversal characters, and calculates SHA-256 hashes.

#### Step 3: OCR & Validation Progress Tracking
1. The multi-engine OCR pipeline extracts textual fields, detects watermarks, measures image blur, and performs orientation correction.
2. The deterministic validation engine validates MRZ checksums, standard formats, and document expiration dates.
3. View timeline events and status updates via `GET /api/v1/cases/{case_id}`.

#### Step 4: Verification Receipts
1. Upon policy evaluation or review completion, issue a signed Merkle-backed receipt via `POST /api/v1/receipts/cases/{case_id}/issue`.
2. Anyone (including third parties without authentication) can cryptographically verify the receipt via `POST /api/v1/receipts/verify` using the `receipt_token`.

---

### 2.2 Trust Officer / Human Reviewer

Human reviewers provide essential oversight for ambiguous or low-confidence cases.

#### Reviewer Workbench Operations:
1. **Access Queue:** Authenticated reviewers (`ROLE_VERIFIER`) query `GET /api/v1/review/queue` to inspect pending cases sorted by priority (`URGENT` -> `HIGH` -> `NORMAL` -> `LOW`).
2. **Claim Case:** Atomically claim a case via `POST /api/v1/review/{case_id}/claim` to prevent reviewer collisions.
3. **Inspect Document & OCR Fields:** Query `GET /api/v1/review/{case_id}` for side-by-side evidence images, extracted bounding boxes, and validation flags.
4. **Annotate Field Corrections:** Submit manual overrides for unreadable or misread fields via `POST /api/v1/review/{case_id}/fields/{field_id}/override`.
5. **Record Decision:** Submit final determination via `POST /api/v1/review/{case_id}/decision`:
   ```json
   {
     "decision": "ALLOW",
     "notes": "Verified holographic watermark and valid issuing authority signature.",
     "field_overrides": {}
   }
   ```

---

### 2.3 Enterprise Organization Administrator

Enterprise administrators manage corporate identity, employee verification, and member scopes.

1. **Register Organization:** Submit corporate details via `POST /api/v1/organizations` (`name`, `slug`, `verified_domain`, `registration_number`).
2. **Manage Members:** Add or remove team members via `POST /api/v1/organizations/{org_id}/members` with roles (`ROLE_ORG_ADMIN` or `ROLE_ORG_MEMBER`).
3. **Confirm Employment Claims:**
   - Employees self-assert their affiliation via `POST /api/v1/organizations/{org_id}/claims` (status: `SELF_ASSERTED`).
   - Org Admins confirm and sign claims via `POST /api/v1/organizations/{org_id}/claims/{claim_id}/confirm` (status: `CONFIRMED`).

---

### 2.4 Autonomous AI Agent Operator

Platform operators can register AI agents, grant temporary delegated capability scopes, and enforce instant kill-switch revocation.

1. **Register Agent Identity:** Submit agent manifest via `POST /api/v1/agents`:
   - Declare capabilities (`extract:ocr`, `validate:rules`, `evaluate:policy`).
   - Associate model metadata (provider, model ID, system prompt fingerprint).
   - Register public key in PEM format (ED25519, RSA, or ECDSA).
2. **Issue Delegated Capability Grant:** Grant time-bounded authority via `POST /api/v1/delegation/grants` with `grantee_id`, `actions`, `resources`, and `audiences`. A cryptographically signed delegation token is issued.
3. **Emergency Revocation:** Immediately revoke compromised or decommissioned agents via `POST /api/v1/agents/{agent_id}/revoke`. Revocation is permanent; all delegated tokens are immediately rendered invalid.

---

### 2.5 Compliance Auditor & Data Protection Officer

Auditors verify cryptographic integrity, compliance records, and privacy mandates.

1. **Audit Chain Verification:** Verify SHA-256 backward hash chaining across all recorded security blocks via `POST /api/v1/audit/verify-chain`. Returns `is_valid: true`, previous/latest block hashes, and total record counts.
2. **GDPR / CCPA Right to Erasure:** Execute subject erasure requests via `POST /api/v1/privacy/erasure-request`. Replaces PII with irreversible cryptographic tombstones while preserving audit chain continuity.
3. **Data Retention & Export:**
   - Inspect data retention schedules via `GET /api/v1/privacy/retention-policy`.
   - Export machine-readable subject data bundles via `GET /api/v1/privacy/export-data`.

---

## 3. Operational Monitoring & Resiliency

### Health Probes & Telemetry:
- **Liveness & Readiness:** `GET /api/v1/health` (HTTP 200 with `X-Process-Time-Ms`).
- **Subsystem Diagnostics:** `GET /api/v1/monitoring/health` (evaluates API, database, storage, OCR engine, and audit chain).
- **Traffic Telemetry:** `GET /api/v1/monitoring/metrics` (tracks 2xx/4xx/5xx counts, average latency, and active queues).
- **Circuit Breaker:** `GET /api/v1/monitoring/circuit-breaker`. Automatically trips to `OPEN` on 3 upstream failures, engaging synthetic document fallback without downtime.
- **Incident Alerts:** `GET /api/v1/monitoring/alerts` and `POST /api/v1/monitoring/alerts/{id}/resolve`.

---

## 4. Security & Authentication Reference

All authenticated endpoints require an RFC 6750 Bearer token:
```http
Authorization: Bearer <SUPABASE_JWT_TOKEN>
```

### Mutating Request Idempotency
To guarantee safe retries and eliminate duplicate case submissions, include an `Idempotency-Key` header on mutating requests (`POST`, `PUT`, `PATCH`):
```http
Idempotency-Key: <UUID4_OR_UNIQUE_CLIENT_KEY>
```
- First request: Processed normally (`X-Cache-Lookup: MISS`).
- Subsequent requests with same key: Replays cached response (`X-Cache-Lookup: HIT`).
