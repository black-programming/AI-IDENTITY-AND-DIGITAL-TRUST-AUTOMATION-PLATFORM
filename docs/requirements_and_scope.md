# AI Identity & Digital Trust Automation Platform
## Phase 1 — Requirements and Scope Specification

**Document Version:** 1.0  
**Phase:** 1 (Requirements and Scope)  
**Status:** Complete / Ready for Review  
**Date:** 14 October 2026  
**Author:** AI System Architect & Antigravity Assistant  
**Approved By:** Pending Project Owner Approval  

---

## 1. Executive Summary & Problem Statement

### 1.1 Context
In modern digital ecosystems, verifying identity claims, credentials, corporate affiliations, and autonomous AI-agent authorizations has become fragmented, opaque, and prone to severe security and privacy vulnerabilities. Users are repeatedly forced to overshare high-risk personal data, organizations struggle with unverified claims, and autonomous AI agents operate without standardized trust boundaries or cryptographic delegations.

### 1.2 Problem Statement
Existing identity solutions suffer from three fundamental flaws:
1. **Binary & Inflexible Decisions:** Systems force binary "Pass/Fail" outcomes without contextual nuance, preventing step-up authentication (`VERIFY`) or least-privilege containment (`RESTRICT`).
2. **Opaque "Black-Box" Determinations:** Automated algorithms reject claims without clear, machine-readable reason codes or actionable human remediation pathways.
3. **Overexposure of Sensitive PII:** Full identity documents and unredacted credentials are leaked across services and stored in audit logs, creating severe compliance and privacy risks.

### 1.3 Project Objective
The AI Identity & Digital Trust Automation Platform delivers an explainable, privacy-first, modular platform that validates identity-related claims, digital documents, organization credentials, and AI-agent permissions.

The system issues contextual, policy-driven decisions:
- **`ALLOW`** — The requested action satisfies the applicable policy.
- **`VERIFY`** — Additional evidence, step-up verification, or human review is required.
- **`RESTRICT`** — Only limited, explicitly scoped, least-privilege access is permitted.
- **`BLOCK`** — The requested action is denied under the current policy.

> [!IMPORTANT]
> **Core Axiom:** These decisions apply strictly to a specific action, resource, and context. They must never be interpreted as definitive moral or character judgments regarding a human subject.

---

## 2. User Roles and Permissions Matrix

The platform enforces a hybrid Role-Based and Attribute-Based Access Control (RBAC/ABAC) model. All access is governed by Supabase Row-Level Security (RLS) at the database layer and token validation within the FastAPI backend.

### 2.1 Role Definitions

| Role ID | Role Name | Description | Key Actors |
|---|---|---|---|
| `ROLE_SUBJECT` | **Individual Subject / User** | Authenticated end-user submitting their own claims and documents. | Citizen, employee, applicant |
| `ROLE_ORG_ADMIN` | **Organization Administrator** | Manages organization profiles, domains, employee claims, and delegations. | HR admin, IT compliance officer |
| `ROLE_VERIFIER` | **Verifier / Reviewer** | Human-in-the-loop specialist authorized to inspect evidence, correct OCR, and rule on ambiguous cases. | Compliance analyst, KYC reviewer |
| `ROLE_SYS_ADMIN` | **System Administrator** | Oversees platform health, policy versions, security configurations, and audit integrity. | SecOps engineer, platform admin |
| `ROLE_AI_AGENT` | **AI Agent / Service Principal** | Non-human autonomous actor operating under scoped, time-bound cryptographic capability grants. | Verification bot, API client |

### 2.2 Permissions Matrix

| Platform Action / Capability | `ROLE_SUBJECT` | `ROLE_ORG_ADMIN` | `ROLE_VERIFIER` | `ROLE_SYS_ADMIN` | `ROLE_AI_AGENT` |
|---|:---:|:---:|:---:|:---:|:---:|
| **Register & Authenticate** | ✅ (Self) | ✅ (Self) | ✅ (Assigned) | ✅ (Assigned) | ✅ (Key/Token) |
| **Manage Profile & Consent** | ✅ (Self) | ✅ (Org Scope) | ❌ | ❌ | ❌ |
| **Create Verification Case** | ✅ (Self) | ✅ (Org Members) | ❌ | ❌ | ✅ (Scoped) |
| **Upload Evidence Documents** | ✅ (Self) | ✅ (Org Members) | ❌ | ❌ | ❌ |
| **View Own Case Status & History** | ✅ (Self) | ✅ (Org Members) | ✅ (All Queue) | ✅ (All) | ✅ (Scoped) |
| **Trigger OCR Extraction & Validation** | ❌ (Automated) | ❌ (Automated) | ✅ (Re-run) | ✅ (Re-run) | ❌ (Automated) |
| **Inspect Unredacted Evidence** | ✅ (Self) | ❌ | ✅ (Assigned) | ❌ (Unless Auditing) | ❌ |
| **Correct Extracted OCR Fields** | ❌ | ❌ | ✅ (With Log) | ✅ (With Log) | ❌ |
| **Render Manual Review Decision** | ❌ | ❌ | ✅ | ✅ | ❌ |
| **Execute Trust & Policy Engine** | ❌ (System) | ❌ (System) | ✅ (Trigger) | ✅ (Trigger) | ❌ (System) |
| **Download Cryptographic Evidence Receipt** | ✅ (Self) | ✅ (Org Scope) | ✅ | ✅ | ✅ (Scoped) |
| **Configure System Policies & Rules** | ❌ | ❌ | ❌ | ✅ | ❌ |
| **View Immutable Audit Logs** | ❌ | ❌ (Org Audit) | ❌ | ✅ (Full System) | ❌ |
| **Register & Revoke AI Agents** | ❌ | ✅ (Org Scope) | ❌ | ✅ | ❌ |
| **Execute Delegated Scoped Actions** | ❌ | ❌ | ❌ | ❌ | ✅ (Within Grant) |

---

## 3. Functional Requirements (FR)

### Module 1: Authentication & Identity Management
- **FR-01.1 (Supabase Auth Integration):** The platform shall authenticate individual users via Supabase Auth using email/password, email verification, and secure session management.
- **FR-01.2 (Session Persistence & Token Lifecycle):** Flutter clients and API clients shall manage JWT tokens securely. Access tokens must expire within 1 hour; refresh tokens must be securely stored and rotated.
- **FR-01.3 (Multi-Factor Authentication - MFA):** Reviewers and System Administrators shall be required to enroll in TOTP-based MFA prior to accessing verification queues or administrative consoles.
- **FR-01.4 (Account Recovery & Password Updates):** Users shall be able to initiate self-service account recovery via time-limited, single-use email tokens without revealing account existence.

### Module 2: User Profile & Privacy-Conscious Consent
- **FR-02.1 (Profile Segregation):** Basic profile information (display name, contact email, region, user type) must be stored separately from sensitive identity evidence.
- **FR-02.2 (Explicit Consent Management):** Before submitting any evidence, the user must explicitly grant informed, granular consent for document processing, OCR extraction, and policy evaluation.
- **FR-02.3 (Consent Audit Record):** Every consent transaction must record the timestamp, consent version, IP/user-agent context, and scope.
- **FR-02.4 (Data Deletion & Retention):** Users must be able to request evidence deletion. The platform must purge raw document assets from storage upon case closure or expiration while retaining immutable, anonymized audit receipts.

### Module 3: Verification Case Management
- **FR-03.1 (Case Initialization):** An authenticated user can initiate a verification case by specifying the claim category (e.g., Personal Identity, Employment, Organization Membership).
- **FR-03.2 (Case State Machine):** Verification cases shall strictly transition through validated states:
  $$\text{Draft} \longrightarrow \text{Submitted} \longrightarrow \text{Processing} \longrightarrow \begin{cases} \text{Verified} \\ \text{Action Required} \\ \text{Under Review} \\ \text{Rejected} \end{cases}$$
- **FR-03.3 (Case Detail & Status Tracking):** The platform shall expose the verification timeline, current state, actionable feedback, and next steps to the case owner (matching Flutter Screen 027).
- **FR-03.4 (Reviewer Assignment):** Cases requiring human review must be queued in FIFO order with manual or automated assignment to certified reviewers.

### Module 4: Secure Evidence Ingestion & Quarantine
- **FR-04.1 (Private Storage Ingestion):** Evidence files must be uploaded directly to private, RLS-protected Supabase Storage buckets. Direct public URLs must be strictly prohibited.
- **FR-04.2 (Server-Side Validation):** Uploaded files must be validated for allowed MIME types (`image/jpeg`, `image/png`, `application/pdf`), maximum size (10 MB), and magic byte signatures to prevent extension spoofing.
- **FR-04.3 (Quarantine & Cryptographic Checksum):** Uploaded assets must enter a `quarantine` state. The platform shall compute and store a SHA-256 checksum immediately upon receipt to guarantee immutability.
- **FR-04.4 (Short-Lived Signed URLs):** Access to raw evidence by authorized reviewers or backend OCR processors shall require time-limited signed URLs expiring in $\le 15\text{ minutes}$.

### Module 5: OCR Extraction & Provenance Tracking
- **FR-05.1 (OCR Engine Orchestration):** FastAPI backend shall orchestrate document text extraction using PaddleOCR or Tesseract on synthetic test documents and authorized user evidence.
- **FR-05.2 (Structured Field Extraction):** The engine shall extract key fields: Document Number, Full Name, Date of Birth, Issue Date, Expiration Date, Issuing Authority/Country.
- **FR-05.3 (Extraction Provenance & Confidence):** Every extracted field must be persisted with the bounding box coordinates, extraction confidence score ($0.00 - 1.00$), OCR engine name, and engine version.
- **FR-05.4 (Handling Inconclusive Extractions):** Files with low resolution, high blur, unsupported orientation, or extraction confidence $< 0.60$ shall automatically transition to `Action Required` or `Under Review` with descriptive error reason codes.

### Module 6: Deterministic Document Validation
- **FR-06.1 (Required Field Completeness):** Check whether all mandatory fields for the document schema are present.
- **FR-06.2 (Temporal Validity Check):** Compare extracted document expiration date against the current UTC date. Expired documents must fail deterministic validation.
- **FR-06.3 (Algorithmic Checksums):** Validate Machine Readable Zone (MRZ) checksums and format regular expressions (e.g., standard national ID formats) where applicable.
- **FR-06.4 (Cross-Field Consistency):** Verify that extracted names, birth dates, and document numbers are mutually consistent with profile assertions and show no conflicting values.

### Module 7: Human Review & Escalation Workflow
- **FR-07.1 (Reviewer Workbench Queue):** Reviewers shall have access to an assigned queue displaying case metadata, extracted fields, validation flags, and side-by-side evidence previews.
- **FR-07.2 (Field Override & Corrections):** A reviewer may correct an erroneous OCR extraction, provided the system records the reviewer ID, previous value, new value, and reason for change in the audit trail.
- **FR-07.3 (Request Additional Evidence):** A reviewer can flag a case as `Action Required`, prompting the user to upload clearer evidence or supporting documents with specific guidance.
- **FR-07.4 (Reviewer Decision Recording):** Manual decisions must include one of the standard outcomes (`ALLOW`, `VERIFY`, `RESTRICT`, `BLOCK`) accompanied by mandatory standardized reason codes.

### Module 8: Trust & Policy Decision Engine
- **FR-08.1 (Rule-Based Policy Execution):** The policy engine evaluates rules against the subject, evidence confidence, deterministic checks, context, and requested action.
- **FR-08.2 (Standard Decision Outcomes):**
  - `ALLOW`: All required claims verified, confidence $\ge 0.85$, valid unexpired documents, no anomalies.
  - `VERIFY`: Inconclusive extraction, minor discrepancy, or high-risk transaction requiring step-up authentication or human approval.
  - `RESTRICT`: Verified identity but unconfirmed high-privilege claims; access granted only to a sandboxed or least-privilege scope.
  - `BLOCK`: Detected tampering, blacklisted credential, failed checksum, or explicit policy violation.
- **FR-08.3 (Mandatory Reason Codes):** Every decision must provide human-readable and machine-readable reason codes (e.g., `DOC_EXPIRED`, `MRZ_CHECKSUM_FAILED`, `OCR_CONFIDENCE_LOW`, `POLICY_SATISFIED`).
- **FR-08.4 (Fail-Safe Defaults):** Any system exception, network failure, or unhandled rule state must fail closed (`BLOCK` or `VERIFY`), never defaulting to `ALLOW`.

### Module 9: Audit Trail & Tamper-Evident Evidence Receipts
- **FR-09.1 (Append-Only Event Sinks):** All security-relevant actions (submission, upload, OCR run, reviewer edit, policy decision) must be recorded in an append-only audit log table.
- **FR-09.2 (Audit Metadata):** Each record must capture: `event_id`, `actor_id`, `actor_role`, `target_resource`, `action_type`, `correlation_id`, `policy_version`, `timestamp_utc`, and `decision_outcome`.
- **FR-09.3 (Cryptographic Evidence Receipts):** Upon final trust evaluation, the system shall generate a JSON/PDF Evidence Receipt containing the case ID, decision outcome, SHA-256 hash of submitted evidence, policy hash, and timestamp.
- **FR-09.4 (PII Redaction in Audit Logs):** Audit logs and receipts must never contain raw document images, passwords, or full plaintext unmasked national identifiers.

### Module 10: Organization & AI-Agent Identity Registry (Foundation)
- **FR-10.1 (Organization Profile & Domain Claims):** Enable organizations to register verified corporate identities and associate authorized domains.
- **FR-10.2 (AI Agent Registry):** Maintain an inventory of authorized AI agents, their human/organization owners, registered capabilities, and status (`Active`, `Suspended`, `Revoked`).
- **FR-10.3 (Scoped Capability Grants):** Grant agents time-bound, scoped tokens specifying explicit permitted resources and actions.

---

## 4. Non-Functional Requirements (NFR)

### 4.1 Security & Cryptography (NFR-SEC)
- **NFR-SEC-01 (Row-Level Security):** 100% of database tables containing user data must have PostgreSQL Row-Level Security enabled and verified. Direct client queries must only return data owned by `auth.uid()`.
- **NFR-SEC-02 (Zero Trust Secret Management):** Supabase `service_role` keys, encryption secrets, and private signing keys must reside strictly on the FastAPI server environment. Flutter Web builds must only contain the public `anon` key.
- **NFR-SEC-03 (Input Sanitization & Injection Prevention):** All API inputs must be validated using Pydantic models. SQL statements must be parameterized. File uploads must be checked for payload safety.
- **NFR-SEC-04 (CORS & CSP Controls):** FastAPI must enforce strict CORS allowing only registered frontend domains. Web delivery must include Content Security Policy (CSP), `X-Content-Type-Options: nosniff`, and `Strict-Transport-Security`.

### 4.2 Privacy & Compliance (NFR-PRIV)
- **NFR-PRIV-01 (Data Minimization):** Extracted PII must be masked in UI views and logs (e.g., displaying `XXXX-XXXX-1234` for identifiers).
- **NFR-PRIV-02 (Synthetic Data by Default):** All automated development tests, integration pipelines, and demonstration environments must strictly use synthetic, watermarked identity documents.
- **NFR-PRIV-03 (Right to Rectification & Erasure):** Mechanisms must exist to redact or delete document assets upon verified user request while retaining non-identifying cryptographic audit receipts.

### 4.3 Performance & Scalability (NFR-PERF)
- **NFR-PERF-01 (API Latency):** Non-OCR REST API endpoints must respond with $p95 < 250\text{ ms}$ under normal operational load.
- **NFR-PERF-02 (Asynchronous OCR Execution):** OCR extraction and heavy document processing must execute asynchronously without blocking API threads, returning immediate task IDs for polling or websocket updates.
- **NFR-PERF-03 (Database Indexing):** All foreign keys, case status columns, and timestamp queries must be backed by database indexes.

### 4.4 Reliability & Maintainability (NFR-REL)
- **NFR-REL-01 (Fail-Closed Architecture):** In the event of an OCR service outage, database timeout, or external dependency failure, the platform must fail closed (`VERIFY` or `BLOCK`).
- **NFR-REL-02 (Idempotency):** Case creation, document upload finalization, and policy evaluation endpoints must accept an `Idempotency-Key` to safely prevent duplicate submissions.
- **NFR-REL-03 (Test Coverage):** Core business logic, policy engine rules, and authorization boundaries must maintain $\ge 80\%$ automated unit and integration test coverage.

### 4.5 Usability & Accessibility (NFR-UX)
- **NFR-UX-01 (WCAG 2.1 AA Compliance):** Flutter Web UI screens must meet WCAG 2.1 AA standards for color contrast, screen reader compatibility, and keyboard navigation.
- **NFR-UX-02 (Responsive Design):** The interface must gracefully support desktop screens ($\ge 1200\text{px}$), tablets ($768\text{px} - 1199\text{px}$), and mobile viewports ($\le 767\text{px}$).
- **NFR-UX-03 (State Clarity):** Every screen must provide unambiguous UI feedback for `loading`, `empty`, `error with recovery action`, and `successful completion` states.

---

## 5. MVP Scope vs. Excluded Features

To ensure delivery of a robust, production-grade foundation, the project is structured into an immediate **Phase 1 MVP Scope** and explicitly defined **Post-MVP Features**.

### 5.1 In-Scope for Minimum Viable Product (MVP)
The MVP implements one complete, verified end-to-end trust pipeline:

```
[1. User Registration / Auth]
             │
             ▼
[2. Verification Case Creation (Screen 027)]
             │
             ▼
[3. Secure Synthetic Document Upload (Quarantine & Hash)]
             │
             ▼
[4. FastAPI OCR Orchestration (PaddleOCR / Tesseract)]
             │
             ▼
[5. Deterministic Validation (Expiry, Regex, Checksums)]
             │
             ▼
[6. Human Review Workbench (Assign, Inspect, Correct)]
             │
             ▼
[7. Trust & Policy Engine (ALLOW / VERIFY / RESTRICT / BLOCK)]
             │
             ▼
[8. Cryptographic Evidence Receipt & Audit Record]
```

1. **Authentication:** Supabase Auth (email/password, verification, password recovery, session handling).
2. **Security & Authorization:** Full PostgreSQL RLS policies for user data isolation, role-based checks for Reviewers.
3. **Verification Cases:** Creation, detail view, status progression (`Draft`, `Submitted`, `Under Review`, `Verified`, `Action Required`, `Rejected`), and tracking UI (Screen 027).
4. **Secure Evidence Ingestion:** Private Supabase Storage bucket, file type/signature sniffing, SHA-256 checksumming, short-lived signed URLs.
5. **OCR Extraction:** FastAPI microservice integrating PaddleOCR/Tesseract on synthetic identity cards and driver licenses.
6. **Deterministic Rule Engine:** Expiry validation, field presence, MRZ/national ID regex, cross-field consistency.
7. **Human Review Queue:** Reviewer dashboard to inspect redacted evidence, view OCR confidence, correct extractions, and record decisions.
8. **Trust Policy Engine:** Core evaluation generating `ALLOW`, `VERIFY`, `RESTRICT`, `BLOCK` with standard reason codes.
9. **Audit Trail & Receipts:** Append-only audit logging and generation of verifiable JSON/PDF receipts.
10. **Automated Testing Suite:** Unit tests, RLS negative authorization tests, and end-to-end workflow validation.

### 5.2 Explicitly Excluded Features (Post-MVP / Roadmap Phases 13–20)

| Feature | Justification for MVP Exclusion | Planned Phase |
|---|---|:---:|
| **Live Government Database / Credit Bureau Integration** | High third-party cost, complex legal agreements, not required to prove core trust engine mechanics. | Phase 20 |
| **Biometric Facial Recognition & Video Liveness Detection** | High false-rejection risks, complex edge-case handling, requires specialized biometric SDKs. | Phase 16 / Post-Launch |
| **Decentralized Identifiers (DIDs) & Verifiable Credentials on Public Blockchains** | Adds excessive blockchain latency, gas fees, and network volatility. Internal cryptographic hash-chaining is sufficient. | Post-v1.0 |
| **Complex XGBoost / Deep Learning Risk Models** | Machine learning risk scoring requires an empirical, labeled dataset. Rule-based baselines must be established first. | Phase 16 |
| **Cross-Organization Multi-Tenant Billing & Metering** | Commercial enterprise billing is secondary to verifying security, RLS, and OCR accuracy. | Phase 13 |
| **Autonomous Multi-Hop Agent Delegation Chains** | Single-hop agent capability grants must be hardened before multi-agent delegation chains are permitted. | Phase 15 |

---

## 6. Success Criteria & Acceptance Tests

### 6.1 Acceptance Criteria Traceability

| ID | Criterion Description | Target Metric | Verification Method |
|---|---|---|---|
| **AC-01** | **User Data Isolation (RLS)** | $0\%$ unauthorized record visibility | Automated test querying another user's case via client token; must return empty set or 403. |
| **AC-02** | **Evidence Storage Protection** | 0 direct public reads allowed | Direct HTTP GET to Supabase Storage bucket without signed URL must yield HTTP 403/404. |
| **AC-03** | **Deterministic Rule Precision** | $100\%$ detection of expired synthetic documents | Synthetic documents with past expiry dates must be flagged with `DOC_EXPIRED` reason code. |
| **AC-04** | **Tamper Detection (Hash Check)** | $100\%$ detection of altered evidence | Modifying a single byte of uploaded evidence must cause SHA-256 checksum mismatch and trigger `BLOCK`. |
| **AC-05** | **Explainability of Decisions** | $100\%$ of decisions include valid reason codes | Every policy output must include $\ge 1$ standardized machine-readable reason code from the schema dictionary. |
| **AC-06** | **Fail-Safe Behavior** | $0$ false-allow grants on system failure | Simulated crash or network disconnect of OCR engine during pipeline execution must result in `VERIFY` or `BLOCK`. |
| **AC-07** | **Zero Secret Leakage** | 0 server keys in client bundle | Static analysis scan of compiled Flutter assets and source code must show no Supabase `service_role` keys. |

### 6.2 Acceptance Test Suites (Given-When-Then)

#### Test Case AT-01: End-to-End Successful Verification (Happy Path)
- **Given:** An authenticated individual user with an active Supabase session.
- **When:** The user creates a verification case, uploads a valid synthetic unexpired identity document, and submits it.
- **Then:** 
  1. File is stored in the private bucket with a valid SHA-256 checksum.
  2. Status transitions to `Submitted` then `Processing`.
  3. OCR extracts mandatory fields with confidence $\ge 0.85$.
  4. Deterministic validation confirms expiry is in the future and regex matches.
  5. Policy engine evaluates rules and issues decision `ALLOW`.
  6. Status transitions to `Verified`.
  7. An immutable audit record and evidence receipt are generated.

#### Test Case AT-02: Expired Document Invalidation (Negative Path)
- **Given:** An authenticated user submitting a synthetic document with an expiration date set to `2024-01-01` (past date).
- **When:** Deterministic validation rules execute.
- **Then:**
  1. Rule `VAL-EXPIRY` triggers a failure.
  2. Policy engine generates decision `BLOCK` (or `VERIFY` if human review required).
  3. The decision includes reason code `DOC_EXPIRED`.
  4. The user is presented with actionable guidance on Screen 027 stating the document has expired.

#### Test Case AT-03: Cross-User RLS Enforcement (Security Path)
- **Given:** Two distinct authenticated users, User A and User B.
- **When:** User B attempts to query verification cases, uploaded documents, or profile details belonging to User A via the Supabase client.
- **Then:**
  1. Supabase PostgreSQL RLS blocks the read.
  2. User B receives an empty result set (0 rows) or an access denied error.
  3. No metadata or evidence belonging to User A is leaked.

#### Test Case AT-04: Reviewer Field Correction & Audit Traceability (Reviewer Path)
- **Given:** A verification case flagged as `Under Review` due to low OCR confidence on the document number.
- **When:** An authenticated Verifier inspects the evidence via a signed URL, enters the corrected document number, and selects `Approve`.
- **Then:**
  1. The corrected value is persisted.
  2. An audit log entry is written containing: `verifier_id`, `original_value`, `new_value`, `timestamp`, and `correction_reason`.
  3. The case status updates to `Verified` with reviewer attribution.

#### Test Case AT-05: System Outage Fail-Closed Behavior (Resilience Path)
- **Given:** A verification case undergoing processing when the OCR engine or backend service throws an unexpected 500 error.
- **When:** The policy engine encounters the unhandled service failure.
- **Then:**
  1. The platform must never approve the claim or generate an `ALLOW` decision.
  2. The case is safely moved to `Under Review` or `Action Required` with reason code `EXTRACTION_SERVICE_UNAVAILABLE`.
  3. The error is logged to operational monitoring with a correlation ID.

---

## 7. Reason Code Schema Registry & Taxonomy

To ensure explainability, every automated or reviewer decision must attach one or more standardized, machine-readable reason codes from this versioned dictionary (`v1.0`).

### 7.1 Decision Reason Codes

| Decision | Reason Code | Category | Human-Readable Description | User Next Step / Guidance |
|---|---|---|---|---|
| **`ALLOW`** | `DEC_ALLOW_SATISFIED` | Success | All mandatory fields extracted and validated against policy. | Claim verified; proceed to authorized service. |
| **`ALLOW`** | `DEC_ALLOW_HUMAN_OVERRIDE` | Human Approval | Reviewer verified evidence and approved claim. | Review complete; claim approved. |
| **`VERIFY`** | `DEC_VERIFY_OCR_CONF_LOW` | Extraction Quality | OCR confidence on critical fields fell below threshold ($< 0.85$). | Case sent for manual review; no action required unless contacted. |
| **`VERIFY`** | `DEC_VERIFY_MRZ_CHECKSUM_MISMATCH` | Ambiguity | Extracted MRZ check digits do not match parsed string. | Routed to human reviewer for manual field inspection. |
| **`VERIFY`** | `DEC_VERIFY_IMAGE_BLUR` | Document Quality | Image failed blur/sharpness threshold test. | Please upload a clearer, well-lit photo of the document. |
| **`VERIFY`** | `DEC_VERIFY_ADDITIONAL_EVIDENCE_REQ` | Reviewer Request | Reviewer requested secondary identity document. | Upload requested secondary proof (e.g. utility bill / company ID). |
| **`RESTRICT`** | `DEC_RESTRICT_PARTIAL_CLAIMS` | Policy Scoping | Identity verified, but specific organization affiliation unconfirmed. | Access granted only to personal sandbox / standard tier. |
| **`RESTRICT`** | `DEC_RESTRICT_CONDITIONAL_APPROVAL` | Risk Mitigation | Valid document, but regional or temporal risk rules apply. | Limited access permitted for 14 days pending full review. |
| **`BLOCK`** | `DEC_BLOCK_DOC_EXPIRED` | Deterministic Validation | Document expiration date is prior to current UTC date. | Please provide an unexpired, currently valid document. |
| **`BLOCK`** | `DEC_BLOCK_CHECKSUM_TAMPER` | Security Integrity | File SHA-256 hash does not match submission metadata. | Upload rejected due to file integrity mismatch. Please re-upload. |
| **`BLOCK`** | `DEC_BLOCK_BLACKLISTED_IDENTIFIER` | Security Policy | Extracted document number appears on compromised/revoked list. | Access denied under security policy. Contact compliance support. |
| **`BLOCK`** | `DEC_BLOCK_UNSUPPORTED_MIME` | Ingestion Safety | File payload signature violates permitted MIME types. | Only JPEG, PNG, and PDF files are accepted. |

---

## 8. Supported Synthetic Document Schemas (MVP)

All development, automated testing, and initial demonstration workflows must strictly utilize synthetic documents conforming to the following schemas:

### 8.1 Synthetic National ID Card (Format: `SYNTH_NAT_ID_V1`)
- **Required Fields:**
  - `document_number`: Regex `^[A-Z]{1}[0-9]{8}$` (e.g., `A12345678`)
  - `full_name`: Alphabetic characters, spaces, hyphens ($2 - 60$ chars)
  - `date_of_birth`: ISO 8601 `YYYY-MM-DD` (Subject must be $\ge 18$ years of age)
  - `expiry_date`: ISO 8601 `YYYY-MM-DD` (Must be $> \text{today}$)
  - `issuing_country`: ISO 3166-1 alpha-3 code (e.g., `SGP`, `IND`, `USA`)
- **Image Requirements:** Minimum resolution $1200 \times 800\text{px}$, color or grayscale, watermark: *"SYNTHETIC TEST DOCUMENT — NOT REAL PII"*.

### 8.2 Synthetic Driver's License (Format: `SYNTH_DL_V1`)
- **Required Fields:**
  - `license_number`: Regex `^[A-Z]{2}-[0-9]{6}-[A-Z]{1}$` (e.g., `DL-849201-B`)
  - `full_name`: Matches user profile name
  - `issue_date`: ISO 8601 `YYYY-MM-DD` (Past date)
  - `expiry_date`: ISO 8601 `YYYY-MM-DD` (Future date)
  - `vehicle_classes`: Array of strings (e.g., `["A", "B", "C"]`)
- **Watermark:** Mandatory *"DEMO SYNTHETIC SPECIMEN"*.

### 8.3 Synthetic Passport Bio-Data Page (Format: `SYNTH_PASS_TD3`)
- **Required Fields:**
  - `passport_number`: Regex `^[0-9]{9}$`
  - `mrz_line_1`: 44-character ICAO Doc 9303 TD3 format (`P<UTO...`)
  - `mrz_line_2`: 44-character line containing passport number, birth date, expiry, check digits
  - `nationality`: ISO 3166-1 alpha-3
- **Validation Rule:** Algorithmic verification of MRZ check digits using modulo 10 with weights `7, 3, 1`.

---

## 9. Data Retention & Privacy Lifecycle Schedule

| Data Category | Quarantine Window | Post-Verification Retention | Purge Mechanism | Long-Term Retained Asset |
|---|---|---|---|---|
| **Raw Evidence Image** | 24 Hours | 30 Days (or immediate on user request) | Automated cron / S3 Lifecycle Rule deletes object from storage bucket | None (deleted permanently) |
| **Extracted Bounding Boxes & Raw OCR Text** | N/A | 30 Days | Purged from `extracted_fields` table upon case archival | Masked summary in `policy_evaluations` |
| **Reviewer Notes & Overrides** | N/A | 1 Year | Retained for compliance audit | Anonymized audit record (`review_actions`) |
| **Cryptographic Evidence Receipt** | N/A | Indefinite / 7 Years | Immutable JSON payload | SHA-256 Merkle root & digital signature |
| **Audit Log Entries** | N/A | Indefinite / 7 Years | Append-only database partition | Event type, actor ID, timestamp, outcome |

---

## 10. Phase 1 Definition of Done Checklist

- [x] **Project Objectives and Problem Statement Finalized:** Documented in Section 1.
- [x] **User Roles and Permissions Matrix Defined:** Documented in Section 2 with RBAC/ABAC mapping.
- [x] **Functional Requirements Documented:** 10 functional modules defined in Section 3.
- [x] **Non-Functional Requirements Documented:** Security, privacy, performance, reliability, and usability defined in Section 4.
- [x] **MVP Scope and Exclusions Established:** Explicitly delineated in Section 5.
- [x] **Success Criteria and Acceptance Tests Defined:** Traceable criteria and test specifications in Section 6.
- [x] **Reason Code Registry Established:** 12 normative reason codes defined in Section 7.
- [x] **Supported Document Schemas Specified:** 3 synthetic document standards defined in Section 8.
- [x] **Data Retention & Privacy Schedule Specified:** Concrete retention timeframes defined in Section 9.
- [x] **Alignment with Master Roadmap:** Preserves existing architecture (Flutter, FastAPI, Supabase) and Antigravity development rules.

---

## 11. Next Phase Gate

Upon approval of this Requirements and Scope document by the project owner:
- **Proceed to Phase 2:** System Architecture (System context, component diagrams, communication protocols, trust boundaries, sensitive data flows, and escalation paths).

