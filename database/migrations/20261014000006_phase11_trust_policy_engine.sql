-- ==============================================================================
-- AI Identity & Digital Trust Automation Platform
-- Migration: 20261014000006_phase11_trust_policy_engine.sql
-- Description: Trust & Policy Engine versioned policy rules, multi-dimensional
--              evaluation records, and Row-Level Security policies.
-- ==============================================================================

-- -----------------------------------------------------------------------------
-- 1. Trust & Policy Rules Table (Versioned Catalog)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.trust_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id TEXT NOT NULL,
    version TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    target_action TEXT NOT NULL,
    target_resource TEXT NOT NULL,
    required_scopes TEXT[] NOT NULL DEFAULT '{}',
    confidence_threshold NUMERIC(4,3) NOT NULL DEFAULT 0.850 CHECK (confidence_threshold >= 0.000 AND confidence_threshold <= 1.000),
    rule_spec JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT uq_policy_id_version UNIQUE (policy_id, version)
);

-- -----------------------------------------------------------------------------
-- 2. Enhance Policy Evaluations Table
-- -----------------------------------------------------------------------------
ALTER TABLE public.policy_evaluations 
    ADD COLUMN IF NOT EXISTS policy_id TEXT,
    ADD COLUMN IF NOT EXISTS permitted_scopes TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS restricted_scopes TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS missing_requirements TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS confidence_score NUMERIC(4,3) DEFAULT 1.000,
    ADD COLUMN IF NOT EXISTS requires_human_review BOOLEAN DEFAULT false;

-- -----------------------------------------------------------------------------
-- 3. Indexes for Policy Queries
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_trust_policies_id_ver ON public.trust_policies(policy_id, version);
CREATE INDEX IF NOT EXISTS idx_trust_policies_action_resource ON public.trust_policies(target_action, target_resource);
CREATE INDEX IF NOT EXISTS idx_policy_eval_case_id ON public.policy_evaluations(case_id);
CREATE INDEX IF NOT EXISTS idx_policy_eval_decision ON public.policy_evaluations(decision_outcome);

-- -----------------------------------------------------------------------------
-- 4. Row-Level Security (RLS)
-- -----------------------------------------------------------------------------
ALTER TABLE public.trust_policies ENABLE ROW LEVEL SECURITY;

-- Anyone authenticated can view active policies
CREATE POLICY "Authenticated users can view active trust policies"
    ON public.trust_policies FOR SELECT
    USING (auth.role() = 'authenticated' AND is_active = true);

-- Only Sys Admins can create or modify trust policies
CREATE POLICY "Sys Admins can manage trust policies"
    ON public.trust_policies FOR ALL
    USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN')
    WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN');

-- Policy evaluations viewable by case owner or verifiers
CREATE POLICY "Users can view evaluations for own cases"
    ON public.policy_evaluations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.verification_cases 
            WHERE id = policy_evaluations.case_id AND user_id = auth.uid()
        )
        OR ((auth.jwt() -> 'app_metadata' ->> 'role') IN ('ROLE_VERIFIER', 'ROLE_SYS_ADMIN'))
    );

-- -----------------------------------------------------------------------------
-- 5. Seed Core Versioned Policies
-- -----------------------------------------------------------------------------
INSERT INTO public.trust_policies (policy_id, version, name, description, target_action, target_resource, required_scopes, confidence_threshold, rule_spec)
VALUES 
    (
        'POL-IDENTITY-BASIC-V1', 
        '1.0.0', 
        'Basic Identity Claim Verification Policy', 
        'Evaluates standard identity claims against unexpired national IDs, driver licenses, or passports.',
        'identity.verify',
        'claims:synthetic_identity',
        ARRAY['identity:read', 'identity:verify'],
        0.850,
        '{
            "min_age": 18,
            "allowed_claims": ["SYNTH_NAT_ID_V1", "SYNTH_DL_V1", "SYNTH_PASSPORT_V1"],
            "require_unexpired": true,
            "require_checksum": true
        }'::jsonb
    ),
    (
        'POL-HIGH-ASSURANCE-V1', 
        '1.0.0', 
        'High Assurance Multi-Credential Policy', 
        'Requires high-confidence OCR, verified profile matching, and no discrepancy flags for elevated financial or corporate access.',
        'access.elevated',
        'resource:financial_vault',
        ARRAY['identity:verify', 'vault:access'],
        0.900,
        '{
            "min_age": 21,
            "allowed_claims": ["SYNTH_PASSPORT_V1", "SYNTH_DL_V1"],
            "disallow_flags": ["FLAG_PROFILE_NAME_MISMATCH", "FLAG_VIZ_MRZ_CONFLICT"],
            "require_unexpired": true
        }'::jsonb
    ),
    (
        'POL-RESTRICTED-PROBATIONARY-V1', 
        '1.0.0', 
        'Restricted Access Probationary Policy', 
        'Provides temporary scoped access for accounts with valid documents expiring within 30 days or pending secondary confirmation.',
        'access.probationary',
        'scope:read_only',
        ARRAY['identity:read'],
        0.800,
        '{
            "max_validity_days": 30,
            "permitted_scopes": ["read_only", "provisional_identity"],
            "restricted_scopes": ["financial_transfer", "admin_escalation"]
        }'::jsonb
    )
ON CONFLICT (policy_id, version) DO NOTHING;
