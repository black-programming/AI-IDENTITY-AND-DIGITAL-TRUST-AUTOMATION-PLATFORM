-- =============================================================================
-- Migration: 20261014000005_phase10_human_review_workflow.sql
-- Description: Phase 10 — Human Reviewer Queue, Corrections, and Decisions
-- Environment: Supabase PostgreSQL
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Reviewer Field Corrections Table (Audit Trail)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.reviewer_field_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES public.verification_cases(id) ON DELETE CASCADE,
    field_key TEXT NOT NULL,
    previous_value TEXT NOT NULL,
    corrected_value TEXT NOT NULL,
    justification TEXT NOT NULL,
    reviewer_id UUID NOT NULL,
    corrected_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_corrections_case_id ON public.reviewer_field_corrections(case_id);
CREATE INDEX IF NOT EXISTS idx_corrections_reviewer_id ON public.reviewer_field_corrections(reviewer_id);

-- -----------------------------------------------------------------------------
-- 2. Reviewer Manual Decisions Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.reviewer_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES public.verification_cases(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL,
    decision_outcome TEXT NOT NULL CHECK (decision_outcome IN ('ALLOW', 'VERIFY', 'RESTRICT', 'BLOCK')),
    reason_code TEXT NOT NULL,
    notes TEXT,
    decided_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reviewer_decisions_case_id ON public.reviewer_decisions(case_id);
CREATE INDEX IF NOT EXISTS idx_reviewer_decisions_outcome ON public.reviewer_decisions(decision_outcome);

-- -----------------------------------------------------------------------------
-- 3. Row-Level Security (RLS) Configuration
-- -----------------------------------------------------------------------------
ALTER TABLE public.reviewer_field_corrections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviewer_decisions ENABLE ROW LEVEL SECURITY;

-- Policy 1: Reviewers & Admins can read and insert field corrections
DROP POLICY IF EXISTS "Reviewers can manage corrections" ON public.reviewer_field_corrections;
CREATE POLICY "Reviewers can manage corrections"
    ON public.reviewer_field_corrections FOR ALL
    USING ((auth.jwt() -> 'app_metadata' ->> 'role') IN ('ROLE_VERIFIER', 'ROLE_SYS_ADMIN', 'ROLE_AUDITOR'))
    WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'role') IN ('ROLE_VERIFIER', 'ROLE_SYS_ADMIN'));

-- Policy 2: Reviewers & Admins can record and view decisions
DROP POLICY IF EXISTS "Reviewers can manage decisions" ON public.reviewer_decisions;
CREATE POLICY "Reviewers can manage decisions"
    ON public.reviewer_decisions FOR ALL
    USING ((auth.jwt() -> 'app_metadata' ->> 'role') IN ('ROLE_VERIFIER', 'ROLE_SYS_ADMIN', 'ROLE_AUDITOR'))
    WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'role') IN ('ROLE_VERIFIER', 'ROLE_SYS_ADMIN'));

-- Policy 3: Case Owners can view manual decisions for their own cases
DROP POLICY IF EXISTS "Case owners can view their case decisions" ON public.reviewer_decisions;
CREATE POLICY "Case owners can view their case decisions"
    ON public.reviewer_decisions FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.verification_cases vc
            WHERE vc.id = reviewer_decisions.case_id AND vc.user_id = auth.uid()
        )
    );

-- Policy 4: Disallow decision updates (immutability)
DROP POLICY IF EXISTS "Disallow decision updates" ON public.reviewer_decisions;
CREATE POLICY "Disallow decision updates"
    ON public.reviewer_decisions FOR UPDATE
    USING (false);
