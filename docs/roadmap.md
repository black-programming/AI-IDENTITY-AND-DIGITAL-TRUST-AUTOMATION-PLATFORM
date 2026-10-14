# AI Identity & Digital Trust Automation Platform
## Master Project Roadmap

**Version:** 1.0  
**Last Updated:** 14 October 2026  
**Development Environment:** Antigravity  
**Development Style:** Vibe Coding with phase-by-phase verification

---

## 1. Project Vision

Build a secure, privacy-conscious AI Identity & Digital Trust Automation Platform that evaluates identity-related claims, digital documents, organization and employment claims, AI-agent identities, and access permissions.

The platform will provide explainable trust decisions:

- `ALLOW` — the requested action satisfies the applicable policy.
- `VERIFY` — more evidence or human review is required.
- `RESTRICT` — only limited, explicitly scoped access is permitted.
- `BLOCK` — the requested action is denied under the current policy.

These decisions apply to a specific action and context. They must not be treated as definitive judgments about a person's identity or character.

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Flutter, Dart, Material 3 |
| State Management | Riverpod |
| Navigation | GoRouter |
| API Client | Dio |
| Backend API | Python, FastAPI |
| Database | Supabase PostgreSQL |
| Authentication | Supabase Auth |
| File Storage | Supabase Storage |
| Database Security | PostgreSQL RLS |
| OCR | PaddleOCR or Tesseract |
| Image Processing | OpenCV |
| AI/ML | Scikit-learn; optional XGBoost |
| Background Jobs | Optional Redis and Celery/RQ |
| Containerization | Docker |
| Version Control | Git and GitHub |
| CI/CD | GitHub Actions |
| Cloud Deployment | Azure or another approved hosting provider |

**Architecture rule:** Supabase remains the source of truth for authentication, database records, and evidence storage. FastAPI handles trusted business logic and AI/OCR orchestration.

---

## 3. Phase-by-Phase Roadmap

### Phase 0 — Existing Project Audit
- Inspect the existing repository and folder structure.
- Review completed UI screens, routes, and dependencies.
- Inspect Supabase migrations, database objects, RLS policies, and Storage configuration.
- Review existing API endpoints, tests, environment files, and documentation.
- Identify completed, partially completed, and missing features.
- Check local-versus-remote migration history.

**Deliverable:** `PROJECT_CURRENT_STATE.md`

**Completion gate:** Audit findings are documented before implementation changes begin.

### Phase 1 — Requirements and Scope
- Finalize project objectives and problem statement.
- Define user roles and permissions.
- Document functional and non-functional requirements.
- Establish MVP scope and excluded features.
- Define success criteria and acceptance tests.

**Deliverable:** Requirements and scope documentation.

### Phase 2 — System Architecture
- Create system context and component diagrams.
- Define Flutter, FastAPI, Supabase, and OCR communication.
- Identify trust boundaries and sensitive data flows.
- Document authentication and authorization paths.
- Define failure handling and human-review escalation.

**Deliverable:** Architecture diagrams and technical design.

### Phase 3 — Repository Foundation
- Organize frontend, backend, database, AI, tests, and documentation.
- Configure linting, formatting, and environment templates.
- Establish Git branching and commit conventions.
- Add baseline automated tests.
- Keep secrets out of source control.

**Deliverable:** A reproducible development foundation.

### Phase 4 — Authentication
- Integrate Supabase Auth.
- Implement registration, login, logout, and recovery.
- Handle session persistence and token refresh.
- Add email verification where configured.
- Introduce MFA for privileged or sensitive actions where appropriate.

**Completion gate:** Authentication and session tests pass.

### Phase 5 — Authorization and Database Security
- Define user roles and organization memberships.
- Validate access tokens in FastAPI.
- Enable and review RLS policies.
- Protect reviewer and administrator operations.
- Test cross-user and cross-organization access restrictions.

**Completion gate:** Unauthorized access tests pass.

### Phase 6 — Verification Case Management
- Create verification cases.
- Implement case listing and detail views.
- Add status transitions and reviewer assignment.
- Track case ownership and purpose.
- Prevent unauthorized state changes.

**Deliverable:** Working case-management workflow.

### Phase 7 — Secure Evidence Upload
- Configure private Supabase Storage buckets.
- Validate file size, type, and file signatures.
- Introduce quarantine and processing states.
- Record file checksums and metadata.
- Use short-lived signed URLs after authorization.
- Handle retries and duplicate uploads safely.

**Completion gate:** Unauthorized file access is blocked.

### Phase 8 — OCR Integration
- Integrate PaddleOCR or Tesseract.
- Use synthetic, watermarked test documents.
- Extract text and supported document fields.
- Store extraction provenance and engine versions.
- Handle unreadable, rotated, incomplete, and low-quality files.

**Deliverable:** OCR extraction pipeline.

### Phase 9 — Document Validation
- Validate required fields and formats.
- Check expiry dates when applicable.
- Detect conflicting extracted fields.
- Record image-quality and document-consistency indicators.
- Generate reason codes for inconclusive results.
- Route ambiguous cases for human review.

**Completion gate:** Checks are explainable and do not claim unsupported identity verification.

### Phase 10 — Human Review Workflow
- Build the reviewer queue.
- Display authorized evidence and extracted fields.
- Support corrections and additional-evidence requests.
- Record reviewer decisions and reason codes.
- Add correction and appeal workflows.

**Deliverable:** End-to-end reviewer workflow.

### Phase 11 — Trust and Policy Engine
- Define versioned policy rules.
- Evaluate subject, action, resource, scope, expiry, and context.
- Generate `ALLOW`, `VERIFY`, `RESTRICT`, and `BLOCK` decisions.
- Include reason codes and missing requirements.
- Fail safely when authorization or policy evaluation fails.
- Never approve a request merely because OCR or an AI service failed.

**Completion gate:** Policy unit and integration tests pass.

### Phase 12 — Audit Trail and Evidence Receipts
- Record security-relevant actions.
- Track actor, target, timestamp, outcome, and correlation ID.
- Reference relevant evidence and policy versions.
- Protect audit records against unauthorized modification.
- Generate access-controlled evidence receipts.
- Avoid storing raw documents or secrets inside audit payloads.

**Deliverable:** Auditable decision history.

### Phase 13 — Organization and Employment Verification
- Register organizations.
- Manage organization memberships and roles.
- Store organization and employment claims.
- Distinguish self-asserted claims from independently confirmed claims.
- Restrict verification actions to authorized parties.
- Track evidence provenance and expiry.

**Completion gate:** Organization-level isolation is verified.

### Phase 14 — AI-Agent Identity Registry
- Register AI agents and their owners.
- Maintain versioned agent manifests.
- Record public-key fingerprints when implemented.
- Track agent status, expiry, and revocation.
- Define supported agent capabilities.
- Audit registration and credential changes.

**Deliverable:** AI-agent registry.

### Phase 15 — Delegated Authorization
- Create scoped capability grants.
- Define permitted actions, resources, and audiences.
- Enforce expiry and revocation.
- Validate signatures and replay protections where implemented.
- Reject requests outside the granted scope.
- Log authorization decisions.

**Completion gate:** Invalid, expired, revoked, and out-of-scope requests are rejected.

### Phase 16 — AI/ML Risk Evaluation
- Establish a documented, representative evaluation dataset.
- Create a rule-based baseline.
- Evaluate optional classification models only when justified.
- Measure false positives and false negatives.
- Assess calibration, limitations, and relevant subgroup performance.
- Document model versions and evaluation results.
- Keep human review and a safe fallback.

**Deliverable:** Dataset card, model card, and evaluation report.

**Important:** Do not fabricate accuracy results or use AI predictions as definitive proof of fraud.

### Phase 17 — Security Hardening
- Conduct a threat-model review.
- Test authorization and RLS boundaries.
- Protect against malicious uploads and parser failures.
- Add rate limiting and abuse controls.
- Review secrets, dependencies, CORS, and security headers.
- Test audit integrity and agent revocation.
- Review privacy, retention, correction, and deletion processes.

**Completion gate:** Critical security findings are resolved or explicitly accepted by the project owner.

### Phase 18 — Monitoring and Reliability
- Add structured, redacted logs.
- Track request IDs and processing status.
- Monitor API, database, and OCR failures.
- Implement safe retries and idempotency.
- Configure alerts for important failures.
- Test dependency outages and recovery.

**Deliverable:** Operational monitoring and incident procedures.

### Phase 19 — Deployment and CI/CD
- Containerize the FastAPI service.
- Configure GitHub Actions.
- Run tests and security checks before deployment.
- Separate development, staging, and production environments.
- Configure TLS and protected secrets.
- Review database migrations before release.
- Test backup restoration and rollback procedures.

**Completion gate:** A staging deployment passes smoke and authorization tests.

### Phase 20 — Final Testing and Release
- Complete end-to-end testing.
- Conduct user acceptance testing.
- Verify accessibility and responsive layouts.
- Test Tamil/English localization if included.
- Review privacy notices and provider integration claims.
- Verify retention and deletion workflows.
- Prepare user documentation and known limitations.
- Obtain project-owner approval.

**Deliverable:** Release candidate and final project documentation.

---

## 4. Recommended MVP Priority

Build one complete workflow before expanding the feature set:

1. Authentication.
2. Authorization and RLS.
3. Verification case creation.
4. Secure synthetic-document upload.
5. OCR extraction.
6. Deterministic validation.
7. Human review.
8. Trust decision.
9. Audit receipt.
10. Automated security and integration tests.

Only after this workflow is verified should organization verification, advanced agent authorization, and optional predictive ML be expanded.

---

## 5. Antigravity Development Rules

1. Inspect existing code before editing.
2. Read relevant documentation before implementing a phase.
3. Preserve completed UI screens and working functionality.
4. Implement only the currently approved phase.
5. Avoid unnecessary dependencies and architecture changes.
6. Use synthetic identity documents during development.
7. Never expose server-only secrets in Flutter or browser builds.
8. Never disable RLS to fix an access problem.
9. Never run risky database migrations without reviewing local and remote states.
10. Add tests for new functionality and authorization failures.
11. Update documentation with implementation changes.
12. Report exact test results and known limitations.
13. Stop at the phase gate and wait for approval.

---

## 6. Definition of Done

A phase is complete only when:

- [ ] The approved scope is implemented.
- [ ] Relevant automated tests pass.
- [ ] Authorization and failure paths are tested.
- [ ] Database changes are reviewed.
- [ ] Security and privacy implications are documented.
- [ ] Existing functionality remains intact.
- [ ] Documentation is updated.
- [ ] Exact test output and limitations are reported.
- [ ] The project owner approves progression to the next phase.

A planned or locally implemented feature must not be described as production-verified unless the relevant environment and behavior have actually been tested.

---

## 7. Phase Report Template

For each completed phase, record:

- Phase number and objective
- Files created or modified
- Database migrations and remote status
- Commands executed
- Tests passed and failed
- Manual verification performed
- Security and privacy review
- Remaining issues and limitations
- Rollback or disable procedure
- Status: `PASS`, `FAIL`, `BLOCKED`, or `NOT VERIFIED`
- Approval required for the next phase

---

## 8. Final Project Goal

Deliver a modular, secure, testable, and explainable AI Identity & Digital Trust Automation Platform using Flutter, FastAPI, and Supabase.

The system should protect sensitive evidence, enforce scoped authorization, support human review, provide traceable decisions, and clearly communicate uncertainty.

**Development principle:** One phase at a time. Verify before proceeding.
