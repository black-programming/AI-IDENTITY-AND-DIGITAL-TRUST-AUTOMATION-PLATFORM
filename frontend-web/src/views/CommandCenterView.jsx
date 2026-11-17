import React from 'react';
import { 
  Shield, 
  CheckCircle2, 
  AlertTriangle, 
  Zap, 
  ArrowUpRight, 
  TrendingUp, 
  FileCheck, 
  Clock, 
  Search, 
  Flame,
  Fingerprint,
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import { MOCK_SYSTEM_METRICS, MOCK_RECENT_VERIFICATIONS, MOCK_SECURITY_THREATS } from '../data/mockData';

export default function CommandCenterView({ onSelectTab, onInspectCase }) {
  return (
    <div className="view-container">
      {/* Top Hero Banner */}
      <div className="hero-cyber-banner cyber-card">
        <div className="hero-content">
          <div className="hero-badge">
            <span className="pulse-dot" style={{ color: 'var(--cyan-primary)' }}></span>
            <span>AUTONOMOUS TRUST OPERATING SYSTEM v3.4</span>
          </div>
          <h1 className="hero-title">
            Decentralized Identity & <br />
            <span className="text-gradient-cyan">Autonomous Digital Verification</span>
          </h1>
          <p className="hero-desc">
            End-to-end zero-knowledge compliance, neural OCR feature extraction (YOLOv8 + PaddleOCR),
            and Platt-calibrated fraud risk scoring with zero autonomous human rejections.
          </p>
          <div className="hero-actions">
            <button 
              className="btn-cyber-primary"
              id="hero-start-verify-btn"
              onClick={() => onSelectTab('verify')}
            >
              <Zap size={16} />
              <span>Launch Verification Hub</span>
            </button>
            <button 
              className="btn-cyber-secondary"
              id="hero-view-cases-btn"
              onClick={() => onSelectTab('cases')}
            >
              <FileCheck size={16} />
              <span>Review Queue (4 Active)</span>
            </button>
            <button 
              className="btn-cyber-secondary"
              id="hero-view-risk-btn"
              onClick={() => onSelectTab('risk')}
            >
              <Fingerprint size={16} />
              <span>Risk Calibration</span>
            </button>
          </div>
        </div>

        <div className="hero-metrics-orbit">
          <div className="orbit-card cyber-card">
            <div className="orbit-label">GLOBAL TRUST INDEX</div>
            <div className="orbit-value text-gradient-cyan">99.4%</div>
            <div className="orbit-sub font-mono text-emerald">
              <TrendingUp size={13} style={{ display: 'inline', marginRight: 4 }} />
              +1.8% vs Baseline
            </div>
            <div className="orbit-ring">
              <svg viewBox="0 0 100 100" className="radial-svg">
                <circle cx="50" cy="50" r="42" stroke="rgba(255,255,255,0.06)" strokeWidth="8" fill="none"/>
                <circle 
                  cx="50" 
                  cy="50" 
                  r="42" 
                  stroke="url(#cyanGlowGrad)" 
                  strokeWidth="8" 
                  fill="none"
                  strokeDasharray="264"
                  strokeDashoffset="18"
                  strokeLinecap="round"
                />
                <defs>
                  <linearGradient id="cyanGlowGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#00F0FF" />
                    <stop offset="100%" stopColor="#8B5CF6" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="kpi-grid">
        <div className="kpi-card cyber-card">
          <div className="kpi-header">
            <span className="kpi-title">TODAY'S VERIFICATIONS</span>
            <div className="kpi-icon-wrap text-cyan">
              <FileCheck size={18} />
            </div>
          </div>
          <div className="kpi-value font-mono">14,892</div>
          <div className="kpi-footer font-mono">
            <span className="text-emerald">+12.4%</span> volume spike detected
          </div>
        </div>

        <div className="kpi-card cyber-card">
          <div className="kpi-header">
            <span className="kpi-title">AUTONOMOUS PASS RATE</span>
            <div className="kpi-icon-wrap text-emerald">
              <CheckCircle2 size={18} />
            </div>
          </div>
          <div className="kpi-value font-mono text-emerald">94.2%</div>
          <div className="kpi-footer font-mono">
            <span>5.8%</span> routed to human triage
          </div>
        </div>

        <div className="kpi-card cyber-card">
          <div className="kpi-header">
            <span className="kpi-title">FRAUD INTERCEPT RATE</span>
            <div className="kpi-icon-wrap text-ruby">
              <Flame size={18} />
            </div>
          </div>
          <div className="kpi-value font-mono text-ruby">99.87%</div>
          <div className="kpi-footer font-mono">
            <span className="text-ruby">19 tampering</span> vectors blocked
          </div>
        </div>

        <div className="kpi-card cyber-card">
          <div className="kpi-header">
            <span className="kpi-title">P95 INFERENCE LATENCY</span>
            <div className="kpi-icon-wrap text-violet">
              <Clock size={18} />
            </div>
          </div>
          <div className="kpi-value font-mono text-violet">482 ms</div>
          <div className="kpi-footer font-mono">
            Target SLA: <span>&lt; 600ms</span>
          </div>
        </div>
      </div>

      {/* Middle Grid: Live Verification Feed & Threat Center */}
      <div className="dashboard-double-grid">
        {/* Live Verifications Stream */}
        <div className="cyber-card dashboard-feed-card">
          <div className="card-header-bar">
            <div className="card-title-group">
              <div className="pulse-dot" style={{ color: 'var(--cyan-primary)' }}></div>
              <h2 className="card-title">Real-Time Verification Stream</h2>
            </div>
            <button 
              className="btn-text-action"
              onClick={() => onSelectTab('verify')}
            >
              <span>Test Live Doc</span>
              <ArrowUpRight size={14} />
            </button>
          </div>

          <div className="verification-table-wrap">
            <table className="cyber-table">
              <thead>
                <tr>
                  <th>CASE / HASH</th>
                  <th>APPLICANT</th>
                  <th>DOC TYPE</th>
                  <th>STATUS</th>
                  <th>RISK</th>
                  <th>LATENCY</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_RECENT_VERIFICATIONS.map((item) => (
                  <tr key={item.caseId} className="table-row-hover">
                    <td>
                      <div className="case-id-cell font-mono">{item.caseId}</div>
                      <div className="case-hash-sub font-mono">{item.hash}</div>
                    </td>
                    <td className="font-semibold">{item.applicant}</td>
                    <td>
                      <span className="doc-pill">{item.docType}</span>
                    </td>
                    <td>
                      {item.status === 'VERIFIED' && (
                        <span className="badge-status badge-status-success">
                          <CheckCircle2 size={12} />
                          <span>VERIFIED</span>
                        </span>
                      )}
                      {item.status === 'REVIEW_NEEDED' && (
                        <span className="badge-status badge-status-warning">
                          <AlertTriangle size={12} />
                          <span>REVIEW</span>
                        </span>
                      )}
                      {item.status === 'REJECTED_SUSPICIOUS' && (
                        <span className="badge-status badge-status-danger">
                          <AlertTriangle size={12} />
                          <span>BLOCKED</span>
                        </span>
                      )}
                    </td>
                    <td>
                      <span className={`font-mono ${item.riskLevel.includes('LOW') ? 'text-emerald' : item.riskLevel.includes('CRITICAL') ? 'text-ruby' : 'text-amber'}`}>
                        {item.riskLevel}
                      </span>
                    </td>
                    <td className="font-mono text-dim">{item.latency}</td>
                    <td>
                      <button 
                        className="btn-inspect-mini"
                        onClick={() => onInspectCase(item)}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Live Threat & Anomaly Detection Panel */}
        <div className="cyber-card dashboard-threat-card">
          <div className="card-header-bar">
            <div className="card-title-group">
              <Shield size={18} className="text-ruby" />
              <h2 className="card-title">Threat Interception Matrix</h2>
            </div>
            <span className="badge-status badge-status-danger">ACTIVE DEFENSE</span>
          </div>

          <div className="threats-list">
            {MOCK_SECURITY_THREATS.map((threat) => (
              <div key={threat.id} className="threat-item-card">
                <div className="threat-top">
                  <span className="threat-type">{threat.type}</span>
                  <span className="badge-status badge-status-danger font-mono">{threat.severity}</span>
                </div>
                <div className="threat-details font-mono">
                  <div><strong>Origin:</strong> {threat.sourceIp}</div>
                  <div><strong>Vector:</strong> {threat.targetEndpoint}</div>
                  <div className="threat-mitigation text-emerald">
                    <strong>Mitigation:</strong> {threat.mitigation}
                  </div>
                </div>
                <div className="threat-time font-mono text-dim">{threat.time}</div>
              </div>
            ))}

            <div className="cryptographic-seal-box">
              <div className="seal-header">
                <Zap size={14} className="text-cyan" />
                <span>MERKLE ROOT ANCHOR</span>
              </div>
              <div className="font-mono seal-hash">
                0x71a2e89f...b01c9842 (Block #849,201)
              </div>
              <div className="seal-info">
                Signed by 3 validator nodes with threshold ECDSA consensus.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
