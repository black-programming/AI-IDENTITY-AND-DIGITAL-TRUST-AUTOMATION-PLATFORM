import React from 'react';
import { 
  LayoutDashboard, 
  FileCheck2, 
  Cpu, 
  Layers, 
  FileText, 
  ShieldAlert, 
  Network,
  CheckCircle2,
  ChevronRight,
  Database,
  Radio
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const navItems = [
    {
      id: 'overview',
      label: 'Command Center',
      sub: 'Real-time telemetry & KPIs',
      icon: LayoutDashboard,
      badge: null
    },
    {
      id: 'verify',
      label: 'Live Verification Hub',
      sub: 'Aadhaar, PAN & DL Inspector',
      icon: FileCheck2,
      badge: 'LIVE YOLO',
      badgeColor: 'cyan'
    },
    {
      id: 'risk',
      label: 'AI Risk Engine',
      sub: 'Platt calibration & models',
      icon: Cpu,
      badge: 'v1.2.0',
      badgeColor: 'violet'
    },
    {
      id: 'cases',
      label: 'Review Workbench',
      sub: 'Human-in-the-loop triage',
      icon: Layers,
      badge: '4 PENDING',
      badgeColor: 'warning'
    },
    {
      id: 'audit',
      label: 'Audit & Receipts',
      sub: 'Signed Merkle ledger logs',
      icon: FileText,
      badge: null
    },
    {
      id: 'security',
      label: 'Threat Defense',
      sub: 'Adaptive 2FA & alerts',
      icon: ShieldAlert,
      badge: 'SHIELD ON',
      badgeColor: 'emerald'
    },
    {
      id: 'api',
      label: 'API Explorer',
      sub: 'FastAPI v1 endpoints',
      icon: Network,
      badge: '17 ROUTERS',
      badgeColor: null
    }
  ];

  return (
    <aside className="cyber-sidebar" id="main-sidebar">
      <div className="sidebar-section-title">PLATFORM NAVIGATION</div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              id={`nav-${item.id}`}
              className={`nav-button ${isActive ? 'nav-button-active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <div className="nav-icon-wrap">
                <Icon size={18} className={isActive ? 'text-cyan' : 'text-muted'} />
              </div>

              <div className="nav-label-group">
                <div className="nav-primary-label">
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className={`badge-pill badge-pill-${item.badgeColor || 'default'}`}>
                      {item.badge}
                    </span>
                  )}
                </div>
                <div className="nav-sub-label">{item.sub}</div>
              </div>

              {isActive && (
                <div className="nav-active-pip">
                  <div className="pip-glow"></div>
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Model & System Health Footer Card */}
      <div className="sidebar-health-footer">
        <div className="sidebar-health-header">
          <Radio size={14} className="text-cyan pulse-icon" />
          <span>NEURAL PIPELINE STATUS</span>
        </div>
        <div className="sidebar-health-metrics">
          <div className="health-row">
            <span className="health-label">Inference Engine:</span>
            <span className="health-val text-cyan">YOLOv8 + Paddle</span>
          </div>
          <div className="health-row">
            <span className="health-label">Risk Classifier:</span>
            <span className="health-val text-emerald">Platt Calibrated</span>
          </div>
          <div className="health-row">
            <span className="health-label">Storage Engine:</span>
            <span className="health-val text-violet">Supabase Quarantined</span>
          </div>
        </div>
        <div className="health-progress-wrap">
          <div className="health-progress-bar" style={{ width: '99.4%' }}></div>
        </div>
        <div className="health-uptime-row">
          <span>SLA Uptime</span>
          <span className="font-mono text-emerald">99.98% OK</span>
        </div>
      </div>
    </aside>
  );
}
