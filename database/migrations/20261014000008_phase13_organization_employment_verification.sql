-- ==============================================================================
-- AI Identity & Digital Trust Automation Platform
-- Migration: 20261014000008_phase13_organization_employment_verification.sql
-- Description: Organization registry enhancements, employment claims table,
--              assertion types (SELF_ASSERTED vs ORGANIZATION_CONFIRMED),
--              provenance tracking, and multi-tenant RLS policies.
-- ==============================================================================

-- -----------------------------------------------------------------------------
-- 1. Enhance Organizations Table
-- -----------------------------------------------------------------------------
ALTER TABLE public.organizations
    ADD COLUMN IF NOT EXISTS registration_number TEXT,
    ADD COLUMN IF NOT EXISTS country_region TEXT DEFAULT 'GLOBAL',
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true;

-- -----------------------------------------------------------------------------
-- 2. Employment Claims Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.employment_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    job_title TEXT NOT NULL,
    department TEXT NOT NULL,
    employee_id TEXT,
    employment_status TEXT NOT NULL DEFAULT 'ACTIVE' 
        CHECK (employment_status IN ('ACTIVE', 'PROBATIONARY', 'SUSPENDED', 'TERMINATED')),
    assertion_type TEXT NOT NULL DEFAULT 'SELF_ASSERTED' 
        CHECK (assertion_type IN ('SELF_ASSERTED', 'ORGANIZATION_CONFIRMED', 'INDEPENDENTLY_VERIFIED', 'REJECTED')),
    work_email TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    credential_expires_at TIMESTAMPTZ,
    evidence_hashes TEXT[] DEFAULT '{}',
    confirmed_by_user_id UUID REFERENCES auth.users(id),
    confirmed_at TIMESTAMPTZ,
    rejection_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- -----------------------------------------------------------------------------
-- 3. Performance Indexes
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_employment_org_user ON public.employment_claims(organization_id, user_id);
CREATE INDEX IF NOT EXISTS idx_employment_assertion ON public.employment_claims(assertion_type);
CREATE INDEX IF NOT EXISTS idx_employment_work_email ON public.employment_claims(work_email);
CREATE INDEX IF NOT EXISTS idx_employment_user_id ON public.employment_claims(user_id);

-- -----------------------------------------------------------------------------
-- 4. Row-Level Security (RLS) Configuration
-- -----------------------------------------------------------------------------
ALTER TABLE public.employment_claims ENABLE ROW LEVEL SECURITY;

-- Subjects can view their own employment claims
CREATE POLICY "Subjects can view own employment claims"
    ON public.employment_claims FOR SELECT
    USING (auth.uid() = user_id);

-- Subjects can submit self-asserted employment claims
CREATE POLICY "Subjects can create self-asserted employment claims"
    ON public.employment_claims FOR INSERT
    WITH CHECK (auth.uid() = user_id AND assertion_type = 'SELF_ASSERTED');

-- Organization members and admins can view claims belonging to their organization
CREATE POLICY "Organization members can view their organization claims"
    ON public.employment_claims FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.organization_memberships om
            WHERE om.organization_id = employment_claims.organization_id
              AND om.user_id = auth.uid()
        )
        OR ((auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN')
    );

-- Only Organization Admins and Sys Admins can confirm or reject employment claims
CREATE POLICY "Organization Admins can confirm or update claims"
    ON public.employment_claims FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.organization_memberships om
            WHERE om.organization_id = employment_claims.organization_id
              AND om.user_id = auth.uid()
              AND om.role = 'ROLE_ORG_ADMIN'
        )
        OR ((auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN')
    );
