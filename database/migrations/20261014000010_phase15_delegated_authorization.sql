-- ==============================================================================
-- AI Identity & Digital Trust Automation Platform
-- Migration: 20261014000010_phase15_delegated_authorization.sql
-- Description: Delegated Authorization schema, scoped capability grants,
--              replay-protection nonces, audience validation, and RLS policies.
-- ==============================================================================

-- -----------------------------------------------------------------------------
-- 1. Scoped Capability Delegation Grants Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.delegation_grants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grantor_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    grantee_id TEXT NOT NULL, -- UUID for human delegate OR agent slug/UUID for AI agent
    grantee_type TEXT NOT NULL DEFAULT 'AI_AGENT'
        CHECK (grantee_type IN ('AI_AGENT', 'HUMAN_DELEGATE')),
    actions TEXT[] NOT NULL DEFAULT '{}',
    resources TEXT[] NOT NULL DEFAULT '{}',
    audiences TEXT[] NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'REVOKED', 'EXPIRED')),
    delegation_token TEXT NOT NULL,
    token_fingerprint TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    revoked_by UUID REFERENCES auth.users(id),
    revocation_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- -----------------------------------------------------------------------------
-- 2. Delegation Nonces Table for Replay Protection
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.delegation_nonces (
    nonce TEXT PRIMARY KEY,
    grant_id UUID NOT NULL REFERENCES public.delegation_grants(id) ON DELETE CASCADE,
    consumed_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);

-- -----------------------------------------------------------------------------
-- 3. Performance Indexes
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_delegation_grantor ON public.delegation_grants(grantor_id);
CREATE INDEX IF NOT EXISTS idx_delegation_grantee ON public.delegation_grants(grantee_id);
CREATE INDEX IF NOT EXISTS idx_delegation_status ON public.delegation_grants(status);
CREATE INDEX IF NOT EXISTS idx_delegation_expires ON public.delegation_grants(expires_at);
CREATE INDEX IF NOT EXISTS idx_delegation_nonces_exp ON public.delegation_nonces(expires_at);

-- -----------------------------------------------------------------------------
-- 4. Triggers for Updated Timestamp
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_delegation_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_delegation_updated_at ON public.delegation_grants;
CREATE TRIGGER trg_delegation_updated_at
    BEFORE UPDATE ON public.delegation_grants
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_delegation_updated_at();

-- -----------------------------------------------------------------------------
-- 5. Row-Level Security (RLS) Configuration
-- -----------------------------------------------------------------------------
ALTER TABLE public.delegation_grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.delegation_nonces ENABLE ROW LEVEL SECURITY;

-- Grantors can view and manage their own capability grants
CREATE POLICY "Grantors can view own grants"
    ON public.delegation_grants FOR SELECT
    USING (auth.uid() = grantor_id);

CREATE POLICY "Grantors can create grants"
    ON public.delegation_grants FOR INSERT
    WITH CHECK (auth.uid() = grantor_id);

CREATE POLICY "Grantors can revoke own grants"
    ON public.delegation_grants FOR UPDATE
    USING (auth.uid() = grantor_id AND status <> 'REVOKED')
    WITH CHECK (auth.uid() = grantor_id);

-- Grantees can view grants delegated to them
CREATE POLICY "Grantees can view granted delegations"
    ON public.delegation_grants FOR SELECT
    USING (grantee_id = auth.uid()::text);

-- Reviewers, Auditors, and Platform Admins can inspect all delegation grants
CREATE POLICY "Auditors can inspect delegation grants"
    ON public.delegation_grants FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid()
            AND ur.role IN ('ROLE_AUDITOR', 'ROLE_VERIFIER', 'ROLE_SYS_ADMIN')
        )
    );
