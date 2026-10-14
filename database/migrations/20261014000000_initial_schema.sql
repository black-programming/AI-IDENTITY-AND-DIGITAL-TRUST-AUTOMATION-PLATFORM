-- ==============================================================================
-- AI Identity & Digital Trust Automation Platform
-- Migration: 20261014000000_initial_schema.sql
-- Description: Core relational schema, foreign keys, indexes, and RLS policies
-- ==============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- 1. Profiles Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    country_region TEXT DEFAULT 'GLOBAL',
    user_type TEXT NOT NULL DEFAULT 'INDIVIDUAL' CHECK (user_type IN ('INDIVIDUAL', 'ORGANIZATION', 'AGENT')),
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- -----------------------------------------------------------------------------
-- 2. Verification Cases Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.verification_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    claim_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Submitted', 'Processing', 'Under Review', 'Action Required', 'Verified', 'Rejected', 'Restricted')),
    priority TEXT NOT NULL DEFAULT 'NORMAL' CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')),
    assigned_reviewer_id UUID REFERENCES auth.users(id),
    current_decision TEXT CHECK (current_decision IN ('ALLOW', 'VERIFY', 'RESTRICT', 'BLOCK')),
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- -----------------------------------------------------------------------------
-- 3. Evidence Files Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.evidence_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES public.verification_cases(id) ON DELETE CASCADE,
    bucket_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    mime_type TEXT NOT NULL CHECK (mime_type IN ('image/jpeg', 'image/png', 'application/pdf')),
    file_size_bytes BIGINT NOT NULL CHECK (file_size_bytes <= 10485760), -- 10 MB Max
    sha256_hash TEXT NOT NULL,
    quarantine_status TEXT NOT NULL DEFAULT 'QUARANTINED' CHECK (quarantine_status IN ('QUARANTINED', 'CLEARED', 'REJECTED')),
    uploaded_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- -----------------------------------------------------------------------------
-- 4. Extracted Fields Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.extracted_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES public.verification_cases(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES public.evidence_files(id) ON DELETE CASCADE,
    field_key TEXT NOT NULL,
    field_value TEXT NOT NULL,
    confidence NUMERIC(4,3) NOT NULL CHECK (confidence >= 0.000 AND confidence <= 1.000),
    bounding_box JSONB,
    ocr_engine TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    extracted_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- -----------------------------------------------------------------------------
-- 5. Policy Evaluations Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.policy_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES public.verification_cases(id) ON DELETE CASCADE,
    policy_version TEXT NOT NULL,
    decision_outcome TEXT NOT NULL CHECK (decision_outcome IN ('ALLOW', 'VERIFY', 'RESTRICT', 'BLOCK')),
    reason_codes TEXT[] NOT NULL DEFAULT '{}',
    evaluation_context JSONB DEFAULT '{}'::jsonb,
    evaluated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- -----------------------------------------------------------------------------
-- 6. Evidence Receipts Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.evidence_receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID NOT NULL REFERENCES public.policy_evaluations(id) ON DELETE CASCADE UNIQUE,
    receipt_token TEXT NOT NULL UNIQUE,
    evidence_merkle_root TEXT NOT NULL,
    signature TEXT NOT NULL,
    receipt_payload JSONB NOT NULL,
    issued_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- -----------------------------------------------------------------------------
-- 7. Case Timeline Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.case_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES public.verification_cases(id) ON DELETE CASCADE,
    from_status TEXT,
    to_status TEXT NOT NULL,
    triggered_by TEXT NOT NULL,
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- -----------------------------------------------------------------------------
-- 8. Audit Events Table (Append-Only)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID,
    actor_role TEXT NOT NULL,
    action_type TEXT NOT NULL,
    target_resource TEXT NOT NULL,
    correlation_id UUID NOT NULL,
    event_metadata JSONB DEFAULT '{}'::jsonb,
    timestamp_utc TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- -----------------------------------------------------------------------------
-- Performance Indexes
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_cases_user_id ON public.verification_cases(user_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON public.verification_cases(status);
CREATE INDEX IF NOT EXISTS idx_evidence_case_id ON public.evidence_files(case_id);
CREATE INDEX IF NOT EXISTS idx_extracted_case_id ON public.extracted_fields(case_id);
CREATE INDEX IF NOT EXISTS idx_eval_case_id ON public.policy_evaluations(case_id);
CREATE INDEX IF NOT EXISTS idx_timeline_case_id ON public.case_timeline(case_id);
CREATE INDEX IF NOT EXISTS idx_audit_correlation_id ON public.audit_events(correlation_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON public.audit_events(timestamp_utc DESC);

-- -----------------------------------------------------------------------------
-- Row-Level Security (RLS) Configuration
-- -----------------------------------------------------------------------------
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.verification_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evidence_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extracted_fields ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.policy_evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evidence_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.case_timeline ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_events ENABLE ROW LEVEL SECURITY;

-- 1. Profiles RLS
CREATE POLICY "Users can view own profile" 
    ON public.profiles FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own profile" 
    ON public.profiles FOR UPDATE USING (auth.uid() = user_id);

-- 2. Verification Cases RLS
CREATE POLICY "Users can view own cases" 
    ON public.verification_cases FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own cases" 
    ON public.verification_cases FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Reviewers can view assigned or queued cases" 
    ON public.verification_cases FOR SELECT 
    USING ((auth.jwt() -> 'app_metadata' ->> 'role') IN ('ROLE_VERIFIER', 'ROLE_SYS_ADMIN'));

-- 3. Evidence Files RLS
CREATE POLICY "Users can view own evidence" 
    ON public.evidence_files FOR SELECT 
    USING (EXISTS (SELECT 1 FROM public.verification_cases WHERE id = evidence_files.case_id AND user_id = auth.uid()));

-- 4. Case Timeline RLS
CREATE POLICY "Users can view own case timeline" 
    ON public.case_timeline FOR SELECT 
    USING (EXISTS (SELECT 1 FROM public.verification_cases WHERE id = case_timeline.case_id AND user_id = auth.uid()));

-- 5. Evidence Receipts RLS
CREATE POLICY "Users can view own evidence receipts" 
    ON public.evidence_receipts FOR SELECT 
    USING (EXISTS (
        SELECT 1 FROM public.policy_evaluations pe 
        JOIN public.verification_cases vc ON vc.id = pe.case_id 
        WHERE pe.id = evidence_receipts.evaluation_id AND vc.user_id = auth.uid()
    ));

-- 6. Audit Events (Admins Only)
CREATE POLICY "System Admins can view audit logs" 
    ON public.audit_events FOR SELECT 
    USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN');
