-- =============================================================================
-- Migration: 20261014000003_phase8_ocr_pipeline.sql
-- Description: Phase 8 — OCR Extraction Pipeline, Provenance, and Security RLS
-- Environment: Supabase PostgreSQL
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Ensure Table Structure & Performance Indexes
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.extracted_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES public.verification_cases(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES public.evidence_files(id) ON DELETE CASCADE,
    field_key TEXT NOT NULL,
    field_value TEXT NOT NULL,
    confidence NUMERIC(4,3) NOT NULL CHECK (confidence >= 0.000 AND confidence <= 1.000),
    bounding_box JSONB DEFAULT '{}'::jsonb,
    ocr_engine TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    extracted_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Optimize queries for validation and policy checks
CREATE INDEX IF NOT EXISTS idx_extracted_fields_case_key ON public.extracted_fields(case_id, field_key);
CREATE INDEX IF NOT EXISTS idx_extracted_fields_file_id ON public.extracted_fields(file_id);
CREATE INDEX IF NOT EXISTS idx_extracted_fields_confidence ON public.extracted_fields(confidence);
CREATE INDEX IF NOT EXISTS idx_extracted_fields_engine ON public.extracted_fields(ocr_engine, engine_version);

-- -----------------------------------------------------------------------------
-- 2. Row-Level Security (RLS) Configuration
-- -----------------------------------------------------------------------------
ALTER TABLE public.extracted_fields ENABLE ROW LEVEL SECURITY;

-- Policy 1: Case Owners can read extracted fields for their own cases
DROP POLICY IF EXISTS "Case owners can view extracted fields" ON public.extracted_fields;
CREATE POLICY "Case owners can view extracted fields"
    ON public.extracted_fields FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.verification_cases vc
            WHERE vc.id = extracted_fields.case_id
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

-- Policy 2: Reviewers and Auditors can inspect extracted fields across all cases
DROP POLICY IF EXISTS "Reviewers can inspect extracted fields" ON public.extracted_fields;
CREATE POLICY "Reviewers can inspect extracted fields"
    ON public.extracted_fields FOR SELECT
    USING (
        (auth.jwt() -> 'app_metadata' ->> 'role') IN ('ROLE_VERIFIER', 'ROLE_SYS_ADMIN', 'ROLE_AUDITOR')
    );

-- Policy 3: Prevent direct client modifications (append-only via backend service)
DROP POLICY IF EXISTS "Disallow direct client modification of extracted fields" ON public.extracted_fields;
CREATE POLICY "Disallow direct client modification of extracted fields"
    ON public.extracted_fields FOR INSERT
    WITH CHECK (
        (auth.jwt() -> 'app_metadata' ->> 'role') IN ('ROLE_SYS_ADMIN', 'service_role')
    );

DROP POLICY IF EXISTS "Disallow client updates to extracted fields" ON public.extracted_fields;
CREATE POLICY "Disallow client updates to extracted fields"
    ON public.extracted_fields FOR UPDATE
    USING (false);

-- -----------------------------------------------------------------------------
-- 3. Aggregated Case Fields View
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW public.case_extracted_fields_summary AS
SELECT 
    case_id,
    file_id,
    jsonb_object_agg(field_key, field_value) AS extracted_fields,
    ROUND(AVG(confidence)::numeric, 3) AS average_confidence,
    MIN(confidence) AS min_confidence,
    COUNT(*) AS total_fields,
    MAX(extracted_at) AS last_extracted_at
FROM public.extracted_fields
GROUP BY case_id, file_id;
