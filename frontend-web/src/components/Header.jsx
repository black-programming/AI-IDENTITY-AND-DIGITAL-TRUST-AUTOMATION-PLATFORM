import React from 'react';
import { 
  ShieldCheck, 
  Activity, 
  Search, 
  Bell, 
  Terminal, 
  Cpu, 
  Sparkles,
  Lock,
  ExternalLink
} from 'lucide-react';

export default function Header({ activeTab, setActiveTab, onOpenCommand }) {
  return (
    <header className="cyber-header" id="main-header">
      <div className="header-left">
        <div className="brand-cluster" onClick={() => setActiveTab('overview')}>
          <div className="shield-logo-wrap">
            <ShieldCheck className="shield-icon" size={26} />
            <div className="shield-ring-pulse"></div>
          </div>
          <div className="brand-text">
            <div className="brand-title">
              AEGIS<span className="brand-highlight">TRUST</span>
              <span className="brand-tag">AI CORE</span>
            </div>
            <div className="brand-subtitle">Autonomous Identity & Trust Protocol</div>
          </div>
        </div>

        <div className="node-status-chip">
          <span className="pulse-dot" style={{ color: 'var(--emerald-success)' }}></span>
          <span className="node-text">CLUSTER: <span className="font-mono text-emerald">ONLINE</span></span>
          <span className="divider-v"></span>
          <Activity size={13} className="text-cyan" />
          <span className="font-mono text-dim">14ms • ASIA-SOUTH1</span>
        </div>
      </div>

      <div className="header-center">
        <div className="cyber-search-bar" onClick={onOpenCommand} id="header-search-input">
          <Search size={15} className="text-dim search-icon" />
          <input 
            type="text" 
            placeholder="Search verified hash, case ID, Aadhaar / PAN format (Press ⌘K)..." 
            readOnly
          />
          <kbd className="cmd-badge">⌘K</kbd>
        </div>
      </div>

      <div className="header-right">
        <button 
          className="btn-header-action"
          id="btn-quick-verify"
          onClick={() => setActiveTab('verify')}
          title="Start Live Document Verification"
        >
          <Sparkles size={14} className="text-cyan" />
          <span>Quick Verify</span>
        </button>

        <a 
          href="http://localhost:8000/docs" 
          target="_blank" 
          rel="noreferrer"
          className="btn-header-ghost"
          id="btn-fastapi-docs"
          title="FastAPI Swagger Documentation"
        >
          <Terminal size={14} />
          <span>FastAPI /docs</span>
          <ExternalLink size={12} className="text-dim" />
        </a>

        <div className="notification-bell-wrap" title="3 Unresolved Security Alerts">
          <Bell size={18} className="text-muted" />
          <span className="notif-badge">3</span>
        </div>

        <div className="officer-profile-card">
          <div className="officer-avatar">
            <Lock size={14} className="text-cyan" />
          </div>
          <div className="officer-details">
            <div className="officer-name">SecOfficer #491</div>
            <div className="officer-clearance">L3 Cryptographic Clear</div>
          </div>
        </div>
      </div>
    </header>
  );
}
