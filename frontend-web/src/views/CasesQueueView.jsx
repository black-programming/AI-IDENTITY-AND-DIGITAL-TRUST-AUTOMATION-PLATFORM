import React, { useState } from 'react';
import { 
  Layers, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  ArrowRight, 
  FileText, 
  User, 
  Calendar,
  Shield,
  Eye
} from 'lucide-react';

export default function CasesQueueView() {
  const [filter, setFilter] = useState('ALL');
  const [selectedCase, setSelectedCase] = useState(null);

  const initialCases = [
    {
      id: 'CASE-2026-9479',
      applicant: 'Marcus Vance',
      docType: 'Driving Licence',
      flagReason: 'Partial glare on validity expiry line. Requires human visual confirmation.',
      riskScore: 0.48,
      status: 'PENDING_REVIEW',
      submittedAt: '14 mins ago',
      assignedTo: 'Officer #491 (You)'
    },
    {
      id: 'CASE-2026-9483',
      applicant: 'Devi Sundaram',
      docType: 'Aadhaar Card',
      flagReason: 'Address change declaration discrepancy vs submitted utility receipt.',
      riskScore: 0.36,
      status: 'PENDING_REVIEW',
      submittedAt: '28 mins ago',
      assignedTo: 'Officer #491 (You)'
    },
    {
      id: 'CASE-2026-9481',
      applicant: 'Dr. Aris Thorne',
      docType: 'Aadhaar Card',
      flagReason: 'None (Autonomous Pass)',
      riskScore: 0.02,
      status: 'AUTONOMOUS_PASS',
      submittedAt: '2 mins ago',
      assignedTo: 'Automated Orchestrator'
    },
    {
      id: 'CASE-2026-9477',
      applicant: 'Kenji Takahashi',
      docType: 'Driving Licence',
      flagReason: 'High frequency texture anomaly detected around license number.',
      riskScore: 0.94,
      status: 'FLAGGED_SUSPICIOUS',
      submittedAt: '34 mins ago',
      assignedTo: 'Forensic Review Queue'
    }
  ];

  const filteredCases = initialCases.filter(c => {
    if (filter === 'PENDING') return c.status === 'PENDING_REVIEW';
    if (filter === 'PASS') return c.status === 'AUTONOMOUS_PASS';
    if (filter === 'FLAGGED') return c.status === 'FLAGGED_SUSPICIOUS';
    return true;
  });

  return (
    <div className="view-container">
      <div className="cyber-card cases-header-card">
        <div className="cases-header-left">
          <div className="badge-status badge-status-warning">
            <Layers size={13} />
            <span>HUMAN-IN-THE-LOOP WORKBENCH</span>
          </div>
          <h2>Verification Review Queue</h2>
          <p className="text-muted">
            Cases flagged by the deterministic policy engine or borderline ML risk scores.
          </p>
        </div>

        <div className="queue-filter-buttons">
          <button 
            className={`filter-btn ${filter === 'ALL' ? 'active' : ''}`}
            onClick={() => setFilter('ALL')}
          >
            All ({initialCases.length})
          </button>
          <button 
            className={`filter-btn ${filter === 'PENDING' ? 'active' : ''}`}
            onClick={() => setFilter('PENDING')}
          >
            Pending Review (2)
          </button>
          <button 
            className={`filter-btn ${filter === 'FLAGGED' ? 'active' : ''}`}
            onClick={() => setFilter('FLAGGED')}
          >
            Suspicious (1)
          </button>
          <button 
            className={`filter-btn ${filter === 'PASS' ? 'active' : ''}`}
            onClick={() => setFilter('PASS')}
          >
            Autonomous (1)
          </button>
        </div>
      </div>

      <div className="cases-grid">
        {filteredCases.map((c) => (
          <div key={c.id} className="cyber-card case-item-card">
            <div className="case-card-header">
              <span className="case-id-badge font-mono">{c.id}</span>
              {c.status === 'PENDING_REVIEW' && (
                <span className="badge-status badge-status-warning">
                  <AlertCircle size={12} />
                  <span>ACTION NEEDED</span>
                </span>
              )}
              {c.status === 'AUTONOMOUS_PASS' && (
                <span className="badge-status badge-status-success">
                  <CheckCircle size={12} />
                  <span>AUTONOMOUS PASS</span>
                </span>
              )}
              {c.status === 'FLAGGED_SUSPICIOUS' && (
                <span className="badge-status badge-status-danger">
                  <XCircle size={12} />
                  <span>SUSPICIOUS</span>
                </span>
              )}
            </div>

            <div className="case-applicant-row">
              <User size={16} className="text-cyan" />
              <span className="applicant-name">{c.applicant}</span>
              <span className="doc-pill font-mono">{c.docType}</span>
            </div>

            <div className="case-flag-reason font-mono">
              <strong>Flag:</strong> {c.flagReason}
            </div>

            <div className="case-meta-footer">
              <div className="case-time text-dim font-mono">{c.submittedAt}</div>
              <div className="case-assigned text-muted font-mono">{c.assignedTo}</div>
            </div>

            <div className="case-actions-bar">
              {c.status === 'PENDING_REVIEW' ? (
                <>
                  <button 
                    className="btn-cyber-primary btn-sm"
                    onClick={() => alert(`Approved ${c.id}. Cryptographic receipt signed and minted.`)}
                  >
                    <CheckCircle size={14} />
                    <span>Approve Case</span>
                  </button>
                  <button 
                    className="btn-cyber-secondary btn-sm"
                    onClick={() => alert(`Escalated ${c.id} for secondary biometric verification.`)}
                  >
                    <Shield size={14} />
                    <span>Request Re-scan</span>
                  </button>
                </>
              ) : (
                <button 
                  className="btn-cyber-secondary btn-sm"
                  onClick={() => alert(`Showing audit trail for ${c.id}`)}
                >
                  <Eye size={14} />
                  <span>View Case Audit Trail</span>
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
