-- =============================================================================
-- Migration: 20261014000004_phase9_document_validation.sql
-- Description: Phase 9 — Deterministic Document Validation Records & RLS
-- Environment: Supabase PostgreSQL
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Document Validations Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.document_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES public.verification_cases(id) ON DELETE CASCADE,
    file_id UUID REFERENCES public.evidence_files(id) ON DELETE CASCADE,
    validation_passed BOOLEAN NOT NULL,
    overall_outcome TEXT NOT NULL CHECK (overall_outcome IN ('PASS', 'FAIL', 'FLAGGED')),
    flags TEXT[] NOT NULL DEFAULT '{}',
    reason_codes TEXT[] NOT NULL DEFAULT '{}',
    rule_results JSONB NOT NULL DEFAULT '[]'::jsonb,
    validated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_validations_case_id ON public.document_validations(case_id);
CREATE INDEX IF NOT EXISTS idx_validations_passed ON public.document_validations(validation_passed);
CREATE INDEX IF NOT EXISTS idx_validations_outcome ON public.document_validations(overall_outcome);
CREATE INDEX IF NOT EXISTS idx_validations_validated_at ON public.document_validations(validated_at DESC);

-- -----------------------------------------------------------------------------
-- 2. Row-Level Security (RLS) Configuration
-- -----------------------------------------------------------------------------
ALTER TABLE public.document_validations ENABLE ROW LEVEL SECURITY;

-- Policy 1: Case Owners can view validation records for their own cases
DROP POLICY IF EXISTS "Case owners can view validation records" ON public.document_validations;
CREATE POLICY "Case owners can view validation records"
    ON public.document_validations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.verification_cases vc
            WHERE vc.id = document_validations.case_id
              AND (
                  vc.user_id = auth.uid()
                  OR (
                      vc.organization_id IS NOT NULL 
                      AND EXISTS (
                          SELECT 1 FROM public.organization_memberships om
                          WHERE om.organization_id = vc.organization_id
                            AND om.user_id = auth.uid()
                      )
                  )
              )
        )
    );

-- Policy 2: Reviewers and Auditors can inspect validation records across all cases
DROP POLICY IF EXISTS "Reviewers can inspect validation records" ON public.document_validations;
CREATE POLICY "Reviewers can inspect validation records"
    ON public.document_validations FOR SELECT
    USING (
        (auth.jwt() -> 'app_metadata' ->> 'role') IN ('ROLE_VERIFIER', 'ROLE_SYS_ADMIN', 'ROLE_AUDITOR')
    );

-- Policy 3: Append-only insert restricted to backend / service role
DROP POLICY IF EXISTS "Backend service can insert validation records" ON public.document_validations;
CREATE POLICY "Backend service can insert validation records"
    ON public.document_validations FOR INSERT
    WITH CHECK (
        (auth.jwt() -> 'app_metadata' ->> 'role') IN ('ROLE_SYS_ADMIN', 'service_role')
    );

-- Policy 4: Disallow client updates (tamper resistance)
DROP POLICY IF EXISTS "Disallow updates to validation records" ON public.document_validations;
CREATE POLICY "Disallow updates to validation records"
    ON public.document_validations FOR UPDATE
    USING (false);
