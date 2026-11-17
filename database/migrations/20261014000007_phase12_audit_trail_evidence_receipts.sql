-- ==============================================================================
-- AI Identity & Digital Trust Automation Platform
-- Migration: 20261014000007_phase12_audit_trail_evidence_receipts.sql
-- Description: Tamper-evident immutable audit log with cryptographic hash chaining,
--              access-controlled verifiable evidence receipts, and RLS policies.
-- ==============================================================================

-- -----------------------------------------------------------------------------
-- 1. Enhance Audit Events Table (Tamper-Evident Hash Chaining)
-- -----------------------------------------------------------------------------
ALTER TABLE public.audit_events
    ADD COLUMN IF NOT EXISTS outcome TEXT NOT NULL DEFAULT 'SUCCESS' CHECK (outcome IN ('SUCCESS', 'DENIED', 'ERROR')),
    ADD COLUMN IF NOT EXISTS case_id UUID REFERENCES public.verification_cases(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS record_hash TEXT,
    ADD COLUMN IF NOT EXISTS previous_record_hash TEXT;

-- -----------------------------------------------------------------------------
-- 2. Prevent Audit Log Tampering (Append-Only Trigger)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit records are append-only and cannot be updated or deleted.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_audit_update ON public.audit_events;
CREATE TRIGGER trg_prevent_audit_update
    BEFORE UPDATE ON public.audit_events
    FOR EACH ROW
    EXECUTE FUNCTION public.prevent_audit_modification();

DROP TRIGGER IF EXISTS trg_prevent_audit_delete ON public.audit_events;
CREATE TRIGGER trg_prevent_audit_delete
    BEFORE DELETE ON public.audit_events
    FOR EACH ROW
    EXECUTE FUNCTION public.prevent_audit_modification();

-- -----------------------------------------------------------------------------
-- 3. Enhance Evidence Receipts Table
-- -----------------------------------------------------------------------------
ALTER TABLE public.evidence_receipts
    ADD COLUMN IF NOT EXISTS case_id UUID REFERENCES public.verification_cases(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'REVOKED')),
    ADD COLUMN IF NOT EXISTS public_key_fingerprint TEXT;

-- -----------------------------------------------------------------------------
-- 4. Performance Indexes
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_audit_case_id ON public.audit_events(case_id);
CREATE INDEX IF NOT EXISTS idx_audit_action_type ON public.audit_events(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_actor_id ON public.audit_events(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_record_hash ON public.audit_events(record_hash);
CREATE INDEX IF NOT EXISTS idx_receipts_case_id ON public.evidence_receipts(case_id);
CREATE INDEX IF NOT EXISTS idx_receipts_token ON public.evidence_receipts(receipt_token);

-- -----------------------------------------------------------------------------
-- 5. Row-Level Security (RLS) Policies
-- -----------------------------------------------------------------------------
ALTER TABLE public.audit_events ENABLE ROW LEVEL SECURITY;

-- Auditors, Verifiers, and Sys Admins can inspect audit records
CREATE POLICY "Privileged roles can inspect all audit events"
    ON public.audit_events FOR SELECT
    USING ((auth.jwt() -> 'app_metadata' ->> 'role') IN ('ROLE_AUDITOR', 'ROLE_VERIFIER', 'ROLE_SYS_ADMIN'));

-- Subjects can inspect audit events pertaining to their own cases
CREATE POLICY "Subjects can view own case audit events"
    ON public.audit_events FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.verification_cases vc 
            WHERE vc.id = audit_events.case_id AND vc.user_id = auth.uid()
        )
    );

-- Evidence Receipts RLS: Subjects view own receipts, Verifiers view all
CREATE POLICY "Users can view own evidence receipts"
    ON public.evidence_receipts FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.verification_cases vc 
            WHERE vc.id = evidence_receipts.case_id AND vc.user_id = auth.uid()
        )
        OR ((auth.jwt() -> 'app_metadata' ->> 'role') IN ('ROLE_VERIFIER', 'ROLE_AUDITOR', 'ROLE_SYS_ADMIN'))
    );
