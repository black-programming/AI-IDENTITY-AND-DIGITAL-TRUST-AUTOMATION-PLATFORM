import React, { useState } from 'react';
import { 
  FileText, 
  CheckCircle2, 
  Lock, 
  ExternalLink, 
  Copy, 
  Clock, 
  Key, 
  Search,
  Download
} from 'lucide-react';
import { MOCK_AUDIT_LOGS } from '../data/mockData';

export default function AuditLedgerView() {
  const [copiedIndex, setCopiedIndex] = useState(null);

  const handleCopy = (hash, idx) => {
    navigator.clipboard?.writeText(hash);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="view-container">
      <div className="cyber-card audit-header-banner">
        <div className="badge-status badge-status-cyan">
          <Lock size={13} />
          <span>CRYPTOGRAPHIC EVIDENCE AUDIT SINK</span>
        </div>
        <h2>Immutable Merkle Verification Ledger</h2>
        <p className="text-muted">
          All document evaluations, OCR extracted tokens, and policy verdicts produce tamper-evident cryptographic receipts with SHA-256 Merkle root verification.
        </p>

        <div className="ledger-summary-strip font-mono">
          <div>TOTAL PROOFS: <span className="text-cyan">849,201</span></div>
          <div>ROOT HASH: <span className="text-emerald">0x71a2e89f...b01c9842</span></div>
          <div>CONSENSUS: <span className="text-emerald">THRESHOLD ECDSA SECP256K1</span></div>
        </div>
      </div>

      <div className="cyber-card ledger-table-card">
        <div className="card-header-bar">
          <div className="card-title-group">
            <Clock size={16} className="text-cyan" />
            <h3 className="card-title">Recent Cryptographic Sealed Receipts</h3>
          </div>
          <button 
            className="btn-cyber-secondary btn-sm"
            onClick={() => alert('Exporting signed audit proof certificate (JSON-LD zero-knowledge receipt)...')}
          >
            <Download size={14} />
            <span>Export ZK Receipt (JSON-LD)</span>
          </button>
        </div>

        <table className="cyber-table">
          <thead>
            <tr>
              <th>BLOCK HEIGHT</th>
              <th>EVENT TYPE</th>
              <th>CASE / IDENTIFIER</th>
              <th>MERKLE HASH DIGEST</th>
              <th>VALIDATOR SIGNER</th>
              <th>PROOF STATUS</th>
              <th>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {MOCK_AUDIT_LOGS.map((log, idx) => (
              <tr key={idx} className="table-row-hover">
                <td className="font-mono text-cyan font-bold">{log.block}</td>
                <td>
                  <span className="doc-pill font-mono">{log.event}</span>
                </td>
                <td className="font-mono font-semibold">{log.entity}</td>
                <td>
                  <div className="hash-with-copy">
                    <span className="font-mono text-dim">{log.hash}</span>
                  </div>
                </td>
                <td className="font-mono text-muted">{log.signer}</td>
                <td>
                  <span className="badge-status badge-status-success font-mono">
                    <CheckCircle2 size={12} />
                    <span>{log.status}</span>
                  </span>
                </td>
                <td>
                  <button 
                    className="btn-inspect-mini"
                    onClick={() => handleCopy(log.hash, idx)}
                  >
                    {copiedIndex === idx ? 'COPIED' : 'COPY HASH'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
