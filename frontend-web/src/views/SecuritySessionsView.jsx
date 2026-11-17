import React, { useState } from 'react';
import { 
  ShieldAlert, 
  Key, 
  Smartphone, 
  Globe, 
  Trash2, 
  CheckCircle, 
  AlertTriangle,
  Lock,
  RefreshCw
} from 'lucide-react';
import { MOCK_SECURITY_THREATS } from '../data/mockData';

export default function SecuritySessionsView() {
  const [sessions, setSessions] = useState([
    {
      id: 'SESS-901',
      device: 'MacBook Pro 16" (Sonoma) • Chrome 124',
      ip: '106.51.72.19 (Chennai, India)',
      status: 'CURRENT_SESSION',
      lastActive: 'Active Now',
      isCurrent: true
    },
    {
      id: 'SESS-892',
      device: 'Ubuntu Workstation 22.04 LTS • CLI Agent',
      ip: '13.235.11.45 (AWS ap-south-1)',
      status: 'ACTIVE_TOKEN',
      lastActive: '12m ago',
      isCurrent: false
    },
    {
      id: 'SESS-844',
      device: 'iPhone 15 Pro • iOS 18 Safari',
      ip: '49.37.112.9 (Bengaluru, India)',
      status: 'IDLE',
      lastActive: '3 hours ago',
      isCurrent: false
    }
  ]);

  const handleRevoke = (id) => {
    setSessions(sessions.filter(s => s.id !== id));
  };

  return (
    <div className="view-container">
      <div className="cyber-card security-header-card">
        <div className="badge-status badge-status-danger">
          <ShieldAlert size={13} />
          <span>ZERO-TRUST SECURITY PERIMETER</span>
        </div>
        <h2>Active Security Sessions & Anomaly Defense</h2>
        <p className="text-muted">
          Continuous device profiling, JWT refresh token rotation with reuse detection, and adaptive cryptographic challenges.
        </p>
      </div>

      <div className="dashboard-double-grid">
        {/* Active Sessions Panel */}
        <div className="cyber-card">
          <div className="card-header-bar">
            <div className="card-title-group">
              <Key size={18} className="text-cyan" />
              <h3 className="card-title">Authorized Officer Sessions</h3>
            </div>
            <span className="badge-status badge-status-cyan font-mono">
              {sessions.length} ACTIVE TOKENS
            </span>
          </div>

          <div className="sessions-list">
            {sessions.map((sess) => (
              <div key={sess.id} className="session-item-card">
                <div className="session-icon-wrap">
                  <Globe size={18} className="text-cyan" />
                </div>
                <div className="session-info">
                  <div className="session-name">
                    <span>{sess.device}</span>
                    {sess.isCurrent && (
                      <span className="badge-status badge-status-success font-mono">THIS DEVICE</span>
                    )}
                  </div>
                  <div className="session-ip font-mono text-dim">
                    {sess.ip} • <span className="text-muted">{sess.lastActive}</span>
                  </div>
                </div>

                {!sess.isCurrent && (
                  <button 
                    className="btn-revoke-session"
                    onClick={() => handleRevoke(sess.id)}
                    title="Revoke and Invalidate Session"
                  >
                    <Trash2 size={14} />
                    <span>Revoke</span>
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Security Posture & 2FA Setup */}
        <div className="cyber-card">
          <div className="card-header-bar">
            <div className="card-title-group">
              <Lock size={18} className="text-emerald" />
              <h3 className="card-title">Identity Defensive Posture</h3>
            </div>
            <span className="badge-status badge-status-success">100% ARMORED</span>
          </div>

          <div className="posture-items-list">
            <div className="posture-box">
              <div className="posture-top">
                <span className="posture-title">TOTP Multi-Factor Authentication</span>
                <span className="badge-status badge-status-success font-mono">ENFORCED</span>
              </div>
              <p className="posture-desc font-mono text-dim">
                Hardware token or RFC 6238 TOTP authenticator required for all policy actions.
              </p>
            </div>

            <div className="posture-box">
              <div className="posture-top">
                <span className="posture-title">Cryptographic Token Binding</span>
                <span className="badge-status badge-status-cyan font-mono">ED25519</span>
              </div>
              <p className="posture-desc font-mono text-dim">
                Tokens cryptographically pinned to client TLS fingerprints to thwart session hijacking.
              </p>
            </div>

            <div className="posture-box">
              <div className="posture-top">
                <span className="posture-title">Row-Level Security (RLS) Isolation</span>
                <span className="badge-status badge-status-violet font-mono">STRICT TENANT</span>
              </div>
              <p className="posture-desc font-mono text-dim">
                Zero cross-tenant leakage; queries strictly scoped via PostgreSQL session identity.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
