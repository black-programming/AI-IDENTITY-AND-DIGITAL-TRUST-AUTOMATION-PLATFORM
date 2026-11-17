import React, { useState } from 'react';
import { 
  FileCheck2, 
  UploadCloud, 
  Scan, 
  CheckCircle, 
  AlertCircle, 
  Sparkles, 
  ShieldCheck, 
  Cpu, 
  Layers, 
  Copy, 
  ExternalLink,
  RefreshCw,
  Eye,
  Sliders
} from 'lucide-react';
import { MOCK_DOCUMENTS } from '../data/mockData';

export default function VerificationHubView() {
  const [selectedDocKey, setSelectedDocKey] = useState('aadhaar');
  const [isScanning, setIsScanning] = useState(false);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true);
  const [copiedHash, setCopiedHash] = useState(false);

  const doc = MOCK_DOCUMENTS[selectedDocKey];

  const handleTriggerScan = () => {
    setIsScanning(true);
    setTimeout(() => {
      setIsScanning(false);
    }, 1800);
  };

  const handleCopyHash = () => {
    navigator.clipboard?.writeText(doc.hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  return (
    <div className="view-container">
      {/* Top Controls Bar */}
      <div className="hub-top-bar cyber-card">
        <div className="hub-title-group">
          <div className="badge-status badge-status-cyan">
            <Scan size={13} />
            <span>REAL-TIME INFERENCE ARENA</span>
          </div>
          <h2>Autonomous Document Verification Hub</h2>
          <p className="text-muted">
            Inspect YOLO entity detection coordinates, OCR field extraction, and zero-knowledge compliance audits.
          </p>
        </div>

        <div className="hub-doc-selector">
          <button
            id="tab-select-aadhaar"
            className={`doc-selector-btn ${selectedDocKey === 'aadhaar' ? 'active' : ''}`}
            onClick={() => setSelectedDocKey('aadhaar')}
          >
            <ShieldCheck size={16} />
            <span>Aadhaar Card (UIDAI)</span>
          </button>
          <button
            id="tab-select-pan"
            className={`doc-selector-btn ${selectedDocKey === 'pan' ? 'active' : ''}`}
            onClick={() => setSelectedDocKey('pan')}
          >
            <Cpu size={16} />
            <span>PAN Card (ITD)</span>
          </button>
          <button
            id="tab-select-dl"
            className={`doc-selector-btn ${selectedDocKey === 'dl' ? 'active' : ''}`}
            onClick={() => setSelectedDocKey('dl')}
          >
            <FileCheck2 size={16} />
            <span>Driving Licence</span>
          </button>
        </div>
      </div>

      {/* Main Split Arena */}
      <div className="hub-split-grid">
        {/* Left: Interactive Document Inspection Canvas */}
        <div className="cyber-card doc-canvas-card">
          <div className="canvas-header">
            <div className="canvas-title">
              <Eye size={16} className="text-cyan" />
              <span>Document Optical Surface & YOLO Bounding Boxes</span>
            </div>

            <div className="canvas-controls">
              <label className="toggle-label">
                <input 
                  type="checkbox" 
                  checked={showBoundingBoxes}
                  onChange={(e) => setShowBoundingBoxes(e.target.checked)}
                />
                <span>Show Bounding Boxes</span>
              </label>

              <button 
                className="btn-cyber-primary btn-sm"
                onClick={handleTriggerScan}
                disabled={isScanning}
                id="btn-re-scan-doc"
              >
                <Scan size={14} className={isScanning ? 'spin-icon' : ''} />
                <span>{isScanning ? 'Neural Scanning...' : 'Run Neural Scan'}</span>
              </button>
            </div>
          </div>

          {/* Visual ID Document Preview */}
          <div className={`id-document-frame ${isScanning ? 'scanner-active' : ''}`}>
            {/* Watermark Notice */}
            <div className="doc-watermark-ribbon">
              SYNTHETIC BENCHMARK SPECIMEN — SECURE TESTING ONLY
            </div>

            {/* Document Header & Emblems */}
            <div className="doc-preview-header">
              <div className="doc-emblem">🏛️</div>
              <div className="doc-national-heading">
                <div className="nat-title">
                  {selectedDocKey === 'aadhaar' && 'GOVERNMENT OF INDIA • UIDAI'}
                  {selectedDocKey === 'pan' && 'INCOME TAX DEPARTMENT • GOVT OF INDIA'}
                  {selectedDocKey === 'dl' && 'UNION OF INDIA • DRIVING LICENCE'}
                </div>
                <div className="nat-sub">{doc.type}</div>
              </div>
              <div className="doc-hologram-shield">
                <div className="hologram-shine"></div>
                <span>ORIGINAL</span>
              </div>
            </div>

            {/* Document Body */}
            <div className="doc-preview-body">
              <div className="doc-photo-box">
                <div className="photo-placeholder">
                  <div className="avatar-silhouette">👤</div>
                  <div className="photo-scan-grid"></div>
                </div>
                <div className="photo-sub-label">OFFICIAL PHOTO</div>
              </div>

              <div className="doc-meta-fields">
                <div className="field-row">
                  <span className="field-lbl">NAME / FULL NAME:</span>
                  <span className="field-val highlight-val">{doc.holderName}</span>
                </div>

                {doc.fatherName && (
                  <div className="field-row">
                    <span className="field-lbl">FATHER'S NAME:</span>
                    <span className="field-val">{doc.fatherName}</span>
                  </div>
                )}

                <div className="field-row-split">
                  <div>
                    <span className="field-lbl">DATE OF BIRTH:</span>
                    <span className="field-val">{doc.dob}</span>
                  </div>
                  {doc.gender && (
                    <div>
                      <span className="field-lbl">GENDER:</span>
                      <span className="field-val">{doc.gender}</span>
                    </div>
                  )}
                  {doc.vehicleClasses && (
                    <div>
                      <span className="field-lbl">CLASSES:</span>
                      <span className="field-val">{doc.vehicleClasses}</span>
                    </div>
                  )}
                </div>

                <div className="field-row doc-highlight-box">
                  <span className="field-lbl">REGISTRATION / IDENTIFIER:</span>
                  <span className="field-val font-mono doc-number-lg">{doc.docNumber}</span>
                </div>
              </div>
            </div>

            {/* Footer with QR / Barcode & Microchip */}
            <div className="doc-preview-footer">
              <div className="doc-barcode-strip">
                <div className="barcode-lines"></div>
                <span className="font-mono">{doc.id}</span>
              </div>
              <div className="doc-seal-emblem">
                <span>VERIFIED AUTH</span>
              </div>
            </div>

            {/* YOLO Bounding Box Overlay Over Document */}
            {showBoundingBoxes && (
              <div className="yolo-bounding-layer">
                {doc.yoloBoundingBoxes.map((box, idx) => (
                  <div 
                    key={idx}
                    className="yolo-box"
                    style={{
                      left: `${box.x}%`,
                      top: `${box.y}%`,
                      width: `${box.w}%`,
                      height: `${box.h}%`
                    }}
                  >
                    <span className="yolo-tag">
                      {box.label} {(box.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Tamper Proof / Cryptographic Signature Bar */}
          <div className="canvas-footer-hash">
            <div className="hash-header">
              <span className="font-mono text-dim">SHA-256 DOCUMENT DIGEST:</span>
              <button 
                className="btn-copy-hash"
                onClick={handleCopyHash}
                title="Copy SHA-256 Digest"
              >
                <Copy size={13} />
                <span>{copiedHash ? 'COPIED!' : 'COPY'}</span>
              </button>
            </div>
            <div className="font-mono doc-hash-text">{doc.hash}</div>
          </div>
        </div>

        {/* Right: Real-Time Extraction Results & Risk Evaluation */}
        <div className="cyber-card doc-details-card">
          <div className="card-header-bar">
            <div className="card-title-group">
              <Sparkles size={18} className="text-cyan" />
              <h3>PaddleOCR Extracted Attributes</h3>
            </div>
            <span className="badge-status badge-status-success">
              <CheckCircle size={13} />
              <span>PASSED VERHOEFF</span>
            </span>
          </div>

          {/* Field Table */}
          <div className="extracted-fields-list">
            {doc.ocrFields.map((field, idx) => (
              <div key={idx} className="ocr-field-item">
                <div className="ocr-field-meta">
                  <span className="ocr-field-key">{field.key}</span>
                  <span className="ocr-confidence-pill font-mono">
                    {(field.confidence * 100).toFixed(1)}% CONF
                  </span>
                </div>
                <div className="ocr-field-val font-mono">{field.value}</div>
                <div className="confidence-meter-track">
                  <div 
                    className="confidence-meter-fill" 
                    style={{ width: `${field.confidence * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>

          {/* Risk Scoring & Policy Decision */}
          <div className="risk-verdict-box">
            <div className="verdict-header">
              <div className="verdict-label">AUTONOMOUS POLICY VERDICT</div>
              <span className="badge-status badge-status-success font-mono">
                {doc.verdict} (ZERO HUMAN OVERRIDE)
              </span>
            </div>

            <div className="risk-score-display">
              <div className="risk-score-num">
                <div className="score-val text-gradient-emerald font-mono">
                  {((1 - doc.riskScore) * 100).toFixed(1)}%
                </div>
                <div className="score-label">CALIBRATED TRUST CONFIDENCE</div>
              </div>

              <div className="risk-gauge-bar-wrap">
                <div className="risk-gauge-label font-mono">
                  <span>Platt Risk: {(doc.riskScore * 100).toFixed(1)}%</span>
                  <span className="text-emerald">LOW RISK TIER</span>
                </div>
                <div className="risk-track">
                  <div 
                    className="risk-bar-fill" 
                    style={{ width: `${(1 - doc.riskScore) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <p className="policy-rationale font-mono">
              <strong>Audit Rationale:</strong> {doc.policyCheck}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
