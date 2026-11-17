-- ==============================================================================
-- AI Identity & Digital Trust Automation Platform
-- Migration: 20261014000001_phase5_authorization_rls.sql
-- Description: Phase 5 - Organizations, Memberships, Multi-Tenancy & Advanced RLS
-- ==============================================================================

-- -----------------------------------------------------------------------------
-- 1. Organizations Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    verified_domain TEXT,
    tier TEXT NOT NULL DEFAULT 'STANDARD' CHECK (tier IN ('STANDARD', 'ENTERPRISE', 'GOVERNMENT')),
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- -----------------------------------------------------------------------------
-- 2. Organization Memberships Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.organization_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'ROLE_ORG_MEMBER' CHECK (role IN ('ROLE_ORG_ADMIN', 'ROLE_ORG_MEMBER', 'ROLE_ORG_VERIFIER')),
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT uq_organization_user UNIQUE (organization_id, user_id)
);

-- -----------------------------------------------------------------------------
-- 3. Add organization_id reference to verification_cases
-- -----------------------------------------------------------------------------
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'verification_cases' 
          AND column_name = 'organization_id'
    ) THEN
        ALTER TABLE public.verification_cases 
        ADD COLUMN organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL;
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Indexes for Multi-Tenant Access
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_org_memberships_user_id ON public.organization_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_org_memberships_org_id ON public.organization_memberships(organization_id);
CREATE INDEX IF NOT EXISTS idx_cases_org_id ON public.verification_cases(organization_id);

-- -----------------------------------------------------------------------------
-- Enable Row Level Security (RLS)
-- -----------------------------------------------------------------------------
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_memberships ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- RLS Policies: Organizations
-- -----------------------------------------------------------------------------
-- Members can view their organization
CREATE POLICY "Members can view their own organizations"
    ON public.organizations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.organization_memberships
            WHERE organization_memberships.organization_id = organizations.id
              AND organization_memberships.user_id = auth.uid()
        )
        OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN'
    );

-- Only System Admins can create organizations globally
CREATE POLICY "System Admins can insert organizations"
    ON public.organizations FOR INSERT
    WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN');

-- Org Admins or System Admins can update their organization
CREATE POLICY "Org Admins can update own organization"
    ON public.organizations FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.organization_memberships
            WHERE organization_memberships.organization_id = organizations.id
              AND organization_memberships.user_id = auth.uid()
              AND organization_memberships.role = 'ROLE_ORG_ADMIN'
        )
        OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN'
    );

-- -----------------------------------------------------------------------------
-- RLS Policies: Organization Memberships
-- -----------------------------------------------------------------------------
-- Users can view memberships within their own organization
CREATE POLICY "Users can view members of their organization"
    ON public.organization_memberships FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.organization_memberships my_mem
            WHERE my_mem.organization_id = organization_memberships.organization_id
              AND my_mem.user_id = auth.uid()
        )
        OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN'
    );

-- Org Admins can manage memberships in their organization
CREATE POLICY "Org Admins can manage organization memberships"
    ON public.organization_memberships FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.organization_memberships admin_mem
            WHERE admin_mem.organization_id = organization_memberships.organization_id
              AND admin_mem.user_id = auth.uid()
              AND admin_mem.role = 'ROLE_ORG_ADMIN'
        )
        OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN'
    );

CREATE POLICY "Org Admins can delete organization memberships"
    ON public.organization_memberships FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.organization_memberships admin_mem
            WHERE admin_mem.organization_id = organization_memberships.organization_id
              AND admin_mem.user_id = auth.uid()
              AND admin_mem.role = 'ROLE_ORG_ADMIN'
        )
        OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN'
    );

-- -----------------------------------------------------------------------------
-- RLS Policies: Multi-Tenant Case Access
-- -----------------------------------------------------------------------------
-- Update verification_cases RLS to permit organization member access
CREATE POLICY "Organization members can view organization cases"
    ON public.verification_cases FOR SELECT
    USING (
        organization_id IS NOT NULL AND
        EXISTS (
            SELECT 1 FROM public.organization_memberships
            WHERE organization_memberships.organization_id = verification_cases.organization_id
              AND organization_memberships.user_id = auth.uid()
        )
    );
