-- ==============================================================================
-- AI Identity & Digital Trust Automation Platform
-- Seed Data for Local Development & Testing
-- ==============================================================================

-- Sample profiles for development (UUIDs match standard test accounts)
-- Note: In production or real Supabase, users are inserted via auth.users first.

-- 1. Insert test verification case template (synthetic)
INSERT INTO public.verification_cases (id, user_id, claim_type, status, priority, current_decision)
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'SYNTH_NAT_ID_V1', 'Draft', 'NORMAL', NULL),
    ('00000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'SYNTH_DL_V1', 'Under Review', 'HIGH', 'VERIFY')
ON CONFLICT (id) DO NOTHING;

-- 2. Insert test organizations (Phase 5)
INSERT INTO public.organizations (id, name, slug, verified_domain, tier)
VALUES
    ('c0000000-0000-0000-0000-000000000001', 'Acme Trust Technologies', 'acme-trust', 'acme.org', 'ENTERPRISE'),
    ('c0000000-0000-0000-0000-000000000002', 'Globex Security Corp', 'globex-corp', 'globex.com', 'STANDARD')
ON CONFLICT (slug) DO NOTHING;
