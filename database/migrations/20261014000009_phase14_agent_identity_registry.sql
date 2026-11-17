-- ==============================================================================
-- AI Identity & Digital Trust Automation Platform
-- Migration: 20261014000009_phase14_agent_identity_registry.sql
-- Description: AI-Agent Identity Registry schema, versioned agent manifests,
--              cryptographic public key fingerprints, status lifecycles, and RLS.
-- ==============================================================================

-- -----------------------------------------------------------------------------
-- 1. Agent Identity Registry Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'SUSPENDED', 'REVOKED', 'EXPIRED')),
    current_manifest_version INT NOT NULL DEFAULT 1,
    public_key_pem TEXT,
    public_key_fingerprint TEXT,
    key_algorithm TEXT DEFAULT 'ED25519'
        CHECK (key_algorithm IN ('ED25519', 'RSA-2048', 'RSA-4096', 'ECDSA-P256')),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    revoked_by UUID REFERENCES auth.users(id),
    revocation_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- -----------------------------------------------------------------------------
-- 2. Versioned Agent Manifests Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.agent_manifests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
    manifest_version INT NOT NULL,
    capabilities TEXT[] NOT NULL DEFAULT '{}',
    model_provider TEXT NOT NULL,
    model_id TEXT NOT NULL,
    runtime_environment TEXT DEFAULT 'CONTAINER',
    system_prompt_hash TEXT,
    code_hash TEXT,
    published_by UUID NOT NULL REFERENCES auth.users(id),
    change_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT uq_agent_manifest_version UNIQUE (agent_id, manifest_version)
);

-- -----------------------------------------------------------------------------
-- 3. Performance Indexes
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_agents_owner ON public.agents(owner_id);
CREATE INDEX IF NOT EXISTS idx_agents_org ON public.agents(organization_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON public.agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_slug ON public.agents(agent_slug);
CREATE INDEX IF NOT EXISTS idx_agent_manifests_agent_ver ON public.agent_manifests(agent_id, manifest_version);

-- -----------------------------------------------------------------------------
-- 4. Triggers for Updated Timestamp
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_agent_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_agents_updated_at ON public.agents;
CREATE TRIGGER trg_agents_updated_at
    BEFORE UPDATE ON public.agents
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_agent_updated_at();

-- -----------------------------------------------------------------------------
-- 5. Row-Level Security (RLS) Configuration
-- -----------------------------------------------------------------------------
ALTER TABLE public.agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_manifests ENABLE ROW LEVEL SECURITY;

-- Agents RLS: Owners, organization members, and platform reviewers/auditors
CREATE POLICY "Owners can view own agents"
    ON public.agents FOR SELECT
    USING (auth.uid() = owner_id);

CREATE POLICY "Owners can insert agents"
    ON public.agents FOR INSERT
    WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Owners can update own agents unless revoked"
    ON public.agents FOR UPDATE
    USING (auth.uid() = owner_id AND status <> 'REVOKED')
    WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Reviewers and Auditors can inspect agents"
    ON public.agents FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid()
            AND ur.role IN ('ROLE_VERIFIER', 'ROLE_AUDITOR', 'ROLE_SYS_ADMIN')
        )
    );

-- Manifests RLS
CREATE POLICY "View manifests if agent visible"
    ON public.agent_manifests FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.agents a
            WHERE a.id = agent_manifests.agent_id
            AND (
                a.owner_id = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM public.user_roles ur
                    WHERE ur.user_id = auth.uid()
                    AND ur.role IN ('ROLE_VERIFIER', 'ROLE_AUDITOR', 'ROLE_SYS_ADMIN')
                )
            )
        )
    );

CREATE POLICY "Owners can insert new manifest versions"
    ON public.agent_manifests FOR INSERT
    WITH CHECK (
        published_by = auth.uid() AND
        EXISTS (
            SELECT 1 FROM public.agents a
            WHERE a.id = agent_manifests.agent_id
            AND a.owner_id = auth.uid()
            AND a.status <> 'REVOKED'
        )
    );
