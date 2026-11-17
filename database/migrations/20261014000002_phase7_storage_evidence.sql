-- =============================================================================
-- Migration: 20261014000002_phase7_storage_evidence.sql
-- Description: Phase 7 — Secure Evidence Storage Buckets, RLS, and Quarantine
-- Environment: Supabase PostgreSQL
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Storage Schema & Bucket Definitions
-- -----------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS storage;

-- Ensure storage.buckets table exists for portable migration execution
CREATE TABLE IF NOT EXISTS storage.buckets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner UUID REFERENCES auth.users,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    public BOOLEAN DEFAULT false,
    avif_autodetection BOOLEAN DEFAULT false,
    file_size_limit BIGINT DEFAULT 10485760, -- 10 MB Max
    allowed_mime_types TEXT[] DEFAULT ARRAY['image/jpeg', 'image/png', 'application/pdf']
);

-- Register private buckets for quarantine ingestion and verified vault
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES 
    ('evidence-quarantine', 'evidence-quarantine', false, 10485760, ARRAY['image/jpeg', 'image/png', 'application/pdf']),
    ('evidence-verified', 'evidence-verified', false, 10485760, ARRAY['image/jpeg', 'image/png', 'application/pdf'])
ON CONFLICT (id) DO UPDATE SET 
    public = false,
    file_size_limit = 10485760,
    allowed_mime_types = ARRAY['image/jpeg', 'image/png', 'application/pdf'];

-- -----------------------------------------------------------------------------
-- 2. Evidence Files Table Schema Hardening
-- -----------------------------------------------------------------------------
-- Ensure quarantine_status supports all Phase 7 states
DO $$
BEGIN
    ALTER TABLE public.evidence_files 
        DROP CONSTRAINT IF EXISTS evidence_files_quarantine_status_check;
        
    ALTER TABLE public.evidence_files 
        ADD CONSTRAINT evidence_files_quarantine_status_check 
        CHECK (quarantine_status IN ('QUARANTINED', 'PROCESSING', 'CLEARED', 'REJECTED'));
EXCEPTION
    WHEN undefined_table THEN
        NULL;
END $$;

-- Indexes for cryptographic deduplication and quarantine status queries
CREATE INDEX IF NOT EXISTS idx_evidence_sha256_hash ON public.evidence_files (sha256_hash);
CREATE INDEX IF NOT EXISTS idx_evidence_quarantine_status ON public.evidence_files (quarantine_status);
CREATE INDEX IF NOT EXISTS idx_evidence_case_sha256 ON public.evidence_files (case_id, sha256_hash);

-- -----------------------------------------------------------------------------
-- 3. Storage Object RLS Policies
-- -----------------------------------------------------------------------------
-- Ensure storage.objects exists and has RLS enabled
CREATE TABLE IF NOT EXISTS storage.objects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bucket_id TEXT REFERENCES storage.buckets(id),
    name TEXT NOT NULL,
    owner UUID REFERENCES auth.users,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    last_accessed_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    metadata JSONB DEFAULT '{}'::jsonb,
    path_tokens TEXT[] GENERATED ALWAYS AS (string_to_array(name, '/')) STORED
);

ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Helper functions for storage path folder name inspection
CREATE OR REPLACE FUNCTION storage.foldername(name text)
RETURNS text[] LANGUAGE plpgsql AS $$
DECLARE
    parts text[];
BEGIN
    SELECT string_to_array(name, '/') INTO parts;
    RETURN parts[1:array_length(parts, 1) - 1];
END $$;

-- Policy 1: Authenticated Case Owners can upload only into their own case folder in quarantine
DROP POLICY IF EXISTS "Case owners can upload evidence to quarantine" ON storage.objects;
CREATE POLICY "Case owners can upload evidence to quarantine"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'evidence-quarantine'
        AND auth.role() = 'authenticated'
        AND EXISTS (
            SELECT 1 FROM public.verification_cases vc
            WHERE vc.id::text = (storage.foldername(name))[1]
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

-- Policy 2: Case owners can read evidence from their own cases
DROP POLICY IF EXISTS "Case owners can read own evidence objects" ON storage.objects;
CREATE POLICY "Case owners can read own evidence objects"
    ON storage.objects FOR SELECT
    USING (
        bucket_id IN ('evidence-quarantine', 'evidence-verified')
        AND auth.role() = 'authenticated'
        AND EXISTS (
            SELECT 1 FROM public.verification_cases vc
            WHERE vc.id::text = (storage.foldername(name))[1]
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

-- Policy 3: Reviewers and Admins can read evidence objects across all cases
DROP POLICY IF EXISTS "Reviewers can inspect evidence objects" ON storage.objects;
CREATE POLICY "Reviewers can inspect evidence objects"
    ON storage.objects FOR SELECT
    USING (
        bucket_id IN ('evidence-quarantine', 'evidence-verified')
        AND (auth.jwt() -> 'app_metadata' ->> 'role') IN ('ROLE_VERIFIER', 'ROLE_SYS_ADMIN', 'ROLE_AUDITOR')
    );

-- Policy 4: Disallow object mutation (immutability)
DROP POLICY IF EXISTS "Disallow object updates" ON storage.objects;
CREATE POLICY "Disallow object updates"
    ON storage.objects FOR UPDATE
    USING (false);

-- Policy 5: Only System Admins can delete objects (e.g. for GDPR right to erasure)
DROP POLICY IF EXISTS "Only Sys Admins can delete evidence objects" ON storage.objects;
CREATE POLICY "Only Sys Admins can delete evidence objects"
    ON storage.objects FOR DELETE
    USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN');
