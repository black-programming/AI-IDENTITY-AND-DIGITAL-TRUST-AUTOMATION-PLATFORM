-- Migration: 20261014000011_phase17_security_hardening_privacy.sql
-- Description: Phase 17 Security Hardening, Privacy Erasure/Correction, and Data Retention Policies with strict RLS

-- 1. Create Privacy Requests Table
CREATE TABLE IF NOT EXISTS public.privacy_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    request_type TEXT NOT NULL CHECK (request_type IN ('ERASURE', 'CORRECTION', 'DATA_EXPORT')),
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED')),
    tombstone_hash TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    completed_at TIMESTAMPTZ
);

-- Index for subject queries
CREATE INDEX IF NOT EXISTS idx_privacy_requests_user ON public.privacy_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_privacy_requests_status ON public.privacy_requests(status);

-- 2. Create Retention Policies Table
CREATE TABLE IF NOT EXISTS public.retention_policies (
    category TEXT PRIMARY KEY,
    retention_days INT NOT NULL CHECK (retention_days > 0),
    auto_purge_enabled BOOLEAN NOT NULL DEFAULT true,
    legal_basis TEXT NOT NULL,
    description TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Seed Default Retention Schedules
INSERT INTO public.retention_policies (category, retention_days, auto_purge_enabled, legal_basis, description)
VALUES 
    ('QUARANTINE_EVIDENCE', 30, true, 'GDPR Art 5(1)(e) Storage Limitation', 'Unverified, quarantined evidence files are purged automatically after 30 days.'),
    ('VERIFIED_CREDENTIALS', 365, false, 'AML/KYC Regulatory Identity Compliance', 'Verified identity credentials retained for active verification validity period (1 year).'),
    ('REJECTED_OR_CORRUPT_UPLOADS', 14, true, 'Data Minimization Principle (GDPR Art 5(1)(c))', 'Rejected or unreadable documents automatically destroyed after 14-day appeal window.'),
    ('CRYPTOGRAPHIC_AUDIT_LOGS', 2555, false, 'Statutory Trust & Financial Audit Compliance', 'Tamper-evident SHA-256 hash chains preserved immutably for 7 years.'),
    ('DELEGATED_AUTHORIZATION_GRANTS', 90, true, 'Principle of Least Privilege & Expiration Control', 'Revoked or expired agent delegation grants purged after 90 days.')
ON CONFLICT (category) DO NOTHING;

-- 3. Enable Row-Level Security
ALTER TABLE public.privacy_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.retention_policies ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policies for Privacy Requests

-- Subjects can insert their own privacy requests
CREATE POLICY "Subjects can submit their own privacy requests"
    ON public.privacy_requests
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- Subjects can view only their own privacy requests
CREATE POLICY "Subjects can view their own privacy requests"
    ON public.privacy_requests
    FOR SELECT
    TO authenticated
    USING (
        auth.uid() = user_id
        OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN'
        OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_AUDITOR'
    );

-- System Administrators can update privacy request processing status
CREATE POLICY "Admins can manage privacy requests"
    ON public.privacy_requests
    FOR UPDATE
    TO authenticated
    USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN')
    WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN');

-- 5. RLS Policies for Retention Policies

-- All authenticated users can read retention schedules
CREATE POLICY "Authenticated users can view retention policies"
    ON public.retention_policies
    FOR SELECT
    TO authenticated
    USING (true);

-- Only System Administrators can alter retention policies
CREATE POLICY "Admins can alter retention policies"
    ON public.retention_policies
    FOR ALL
    TO authenticated
    USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN')
    WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'role') = 'ROLE_SYS_ADMIN');
