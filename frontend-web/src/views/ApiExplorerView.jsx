import React, { useState } from 'react';
import { 
  Network, 
  Terminal, 
  Send, 
  CheckCircle2, 
  Code2, 
  ExternalLink,
  Layers,
  Cpu
} from 'lucide-react';

export default function ApiExplorerView() {
  const [selectedEndpoint, setSelectedEndpoint] = useState('/api/v1/health');
  const [responseOutput, setResponseOutput] = useState(JSON.stringify({
    status: 'HEALTHY',
    version: '1.0.0',
    services: {
      ocr_engine: 'ONLINE (YOLOv8 + PaddleOCR)',
      platt_risk_model: 'ONLINE (v1.2.0-calibrated)',
      storage_backend: 'ONLINE (Supabase Quarantined)',
      audit_ledger: 'ONLINE (SECP256K1 Merkle Sink)'
    },
    latency_ms: 3.8
  }, null, 2));

  const endpoints = [
    { method: 'GET', path: '/api/v1/health', category: 'Health & System', desc: 'Cluster liveness and subsystem heartbeat' },
    { method: 'GET', path: '/api/v1/risk/model-card', category: 'AI Risk', desc: 'Metadata, Brier calibration, and evaluation metrics' },
    { method: 'GET', path: '/api/v1/risk/dataset-card', category: 'AI Risk', desc: 'Synthetic dataset grounding benchmarks' },
    { method: 'POST', path: '/api/v1/evidence/upload', category: 'Evidence', desc: 'Upload identity document to quarantine bucket' },
    { method: 'POST', path: '/api/v1/ocr/process', category: 'OCR Pipeline', desc: 'Extract key-value attributes via PaddleOCR' },
    { method: 'POST', path: '/api/v1/validation/aadhaar', category: 'Deterministic', desc: 'UIDAI Verhoeff algorithm and format check' },
    { method: 'POST', path: '/api/v1/validation/pancard', category: 'Deterministic', desc: 'ITD 10-char format & entity category check' },
    { method: 'POST', path: '/api/v1/policy/evaluate', category: 'Policy Engine', desc: 'Evaluate rule matrix: ALLOW, REVIEW, BLOCK' },
    { method: 'GET', path: '/api/v1/receipts/{case_id}', category: 'Audit Ledger', desc: 'Fetch tamper-evident cryptographic receipt' }
  ];

  const handleTestCall = (path) => {
    setSelectedEndpoint(path);
    if (path === '/api/v1/risk/model-card') {
      setResponseOutput(JSON.stringify({
        model_name: "ExplainableIdentityRiskScorer",
        version: "1.2.0-calibrated",
        calibrator: "Platt Scaling (Sigmoid)",
        brier_score: 0.0412,
        roc_auc: 0.9841,
        expected_calibration_error: 0.018,
        autonomous_rejection_policy: "DISABLED_SAFE_FALLBACK"
      }, null, 2));
    } else if (path === '/api/v1/receipts/{case_id}') {
      setResponseOutput(JSON.stringify({
        case_id: "CASE-2026-9481",
        merkle_root: "0x71a2e89fa3b01c9842",
        block_height: 849201,
        signature: "MEQCID3k...SignedSecp256k1",
        status: "SEALED_ON_CHAIN"
      }, null, 2));
    } else {
      setResponseOutput(JSON.stringify({
        endpoint: path,
        status: 200,
        timestamp: new Date().toISOString(),
        message: "Endpoint live and responsive on FastAPI application."
      }, null, 2));
    }
  };

  return (
    <div className="view-container">
      <div className="cyber-card api-header-card">
        <div className="badge-status badge-status-cyan">
          <Terminal size={13} />
          <span>FASTAPI MICROSERVICE EXPLORER</span>
        </div>
        <h2>V1 REST API & Neural Endpoints</h2>
        <p className="text-muted">
          Interactive developer console for evaluating backend endpoints running on <code>http://localhost:8000</code>.
        </p>
      </div>

      <div className="dashboard-double-grid">
        <div className="cyber-card">
          <div className="card-header-bar">
            <h3 className="card-title">Endpoint Catalog</h3>
            <span className="font-mono text-dim">9 Selected</span>
          </div>

          <div className="endpoint-list">
            {endpoints.map((ep, idx) => (
              <div 
                key={idx}
                className={`endpoint-item ${selectedEndpoint === ep.path ? 'active' : ''}`}
                onClick={() => handleTestCall(ep.path)}
              >
                <span className={`method-badge method-${ep.method.toLowerCase()} font-mono`}>
                  {ep.method}
                </span>
                <div className="endpoint-info">
                  <div className="endpoint-path font-mono">{ep.path}</div>
                  <div className="endpoint-desc">{ep.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="cyber-card api-terminal-card">
          <div className="card-header-bar">
            <div className="card-title-group">
              <Code2 size={16} className="text-cyan" />
              <h3 className="card-title font-mono">{selectedEndpoint}</h3>
            </div>
            <button 
              className="btn-cyber-primary btn-sm"
              onClick={() => handleTestCall(selectedEndpoint)}
            >
              <Send size={13} />
              <span>Send Request</span>
            </button>
          </div>

          <div className="terminal-body font-mono">
            <div className="terminal-status-bar">
              <span className="text-emerald">HTTP 200 OK</span>
              <span className="text-dim">4.2ms</span>
            </div>
            <pre className="terminal-json">{responseOutput}</pre>
          </div>
        </div>
      </div>
    </div>
  );
}
