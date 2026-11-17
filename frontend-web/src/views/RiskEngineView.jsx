import React from 'react';
import { 
  Cpu, 
  BarChart3, 
  Sliders, 
  CheckCircle2, 
  AlertTriangle, 
  Target, 
  Info,
  ShieldCheck,
  TrendingDown
} from 'lucide-react';

export default function RiskEngineView() {
  const modelMetrics = {
    version: 'ExplainableIdentityRiskScorer v1.2.0-calibrated',
    calibrationMethod: 'Platt Scaling (Sigmoidal Log-Odds Mapping)',
    brierScore: '0.0412 (Excellent Calibration)',
    rocAuc: '0.9841',
    eceScore: '0.018 (Expected Calibration Error < 2%)',
    autonomousRejections: '0 (Strict Policy: Only routes to human review)'
  };

  const riskFactors = [
    { factor: 'Document Boundary & Aspect Ratio Warp', weight: '+0.28', impact: 'Moderate', color: 'amber' },
    { factor: 'OCR Character Font Discrepancy / Inpainting', weight: '+0.42', impact: 'High', color: 'ruby' },
    { factor: 'UIDAI / ITD Verhoeff & Checksum Check', weight: '-0.38', impact: 'Strong Mitigator', color: 'emerald' },
    { factor: 'Device Geolocation & Subnet Velocity', weight: '-0.14', impact: 'Standard Legitimate', color: 'cyan' },
    { factor: 'Hologram Spectral Reflection Gradient', weight: '-0.24', impact: 'Physical Specimen Match', color: 'emerald' }
  ];

  const subgroupSlices = [
    { slice: 'Aadhaar (QR-Embedded)', sampleCount: 1200, brierScore: 0.038, passRate: '95.4%' },
    { slice: 'PAN Card (Alphanumeric)', sampleCount: 950, brierScore: 0.042, passRate: '94.1%' },
    { slice: 'Driving Licence (SmartCard/Paper)', sampleCount: 780, brierScore: 0.045, passRate: '92.8%' },
    { slice: 'Low-Light Degradation (Simulated)', sampleCount: 310, brierScore: 0.051, passRate: '88.6%' },
    { slice: 'Elderly Demographic (>65yr)', sampleCount: 220, brierScore: 0.039, passRate: '94.8%' }
  ];

  return (
    <div className="view-container">
      {/* Risk Engine Header */}
      <div className="cyber-card risk-header-banner">
        <div className="badge-status badge-status-violet">
          <Cpu size={14} />
          <span>NEURAL RISK & EXPLAINABILITY ENGINE</span>
        </div>
        <h2>Explainable Identity Risk Scorer (v1.2.0)</h2>
        <p className="text-muted">
          Platt-calibrated machine learning risk model paired with deterministic rule constraints.
          Guaranteed zero autonomous rejections — all ambiguous cases are surfaced to verified review officers.
        </p>

        <div className="model-badges-strip">
          <div className="model-stat-pill">
            <span className="pill-lbl">Brier Score:</span>
            <span className="pill-val font-mono text-emerald">{modelMetrics.brierScore.split(' ')[0]}</span>
          </div>
          <div className="model-stat-pill">
            <span className="pill-lbl">ROC-AUC:</span>
            <span className="pill-val font-mono text-cyan">{modelMetrics.rocAuc}</span>
          </div>
          <div className="model-stat-pill">
            <span className="pill-lbl">ECE Error:</span>
            <span className="pill-val font-mono text-emerald">{modelMetrics.eceScore.split(' ')[0]}</span>
          </div>
          <div className="model-stat-pill">
            <span className="pill-lbl">Autonomous Rejections:</span>
            <span className="pill-val font-mono text-ruby">0 (Safeguarded)</span>
          </div>
        </div>
      </div>

      <div className="dashboard-double-grid">
        {/* Directional Feature Contributions */}
        <div className="cyber-card">
          <div className="card-header-bar">
            <div className="card-title-group">
              <Sliders size={18} className="text-violet" />
              <h3 className="card-title">Directional Risk Feature Contributions</h3>
            </div>
            <span className="badge-status badge-status-cyan">SHAP / ATTRIBUTION</span>
          </div>

          <div className="risk-factors-list">
            {riskFactors.map((item, idx) => (
              <div key={idx} className="risk-factor-item">
                <div className="factor-top">
                  <span className="factor-name">{item.factor}</span>
                  <span className={`font-mono badge-status badge-status-${item.color}`}>
                    {item.weight}
                  </span>
                </div>
                <div className="factor-sub font-mono text-dim">
                  Effect: {item.impact}
                </div>
                <div className="factor-bar-track">
                  <div 
                    className={`factor-bar-fill fill-${item.color}`}
                    style={{ width: `${Math.abs(parseFloat(item.weight)) * 180}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Subgroup Demographic & Document Slices */}
        <div className="cyber-card">
          <div className="card-header-bar">
            <div className="card-title-group">
              <Target size={18} className="text-emerald" />
              <h3 className="card-title">Subgroup Fairness & Calibration Slices</h3>
            </div>
            <span className="badge-status badge-status-success">NO BIAS DETECTED</span>
          </div>

          <table className="cyber-table">
            <thead>
              <tr>
                <th>SUBGROUP SLICE</th>
                <th>SAMPLES</th>
                <th>BRIER</th>
                <th>PASS RATE</th>
              </tr>
            </thead>
            <tbody>
              {subgroupSlices.map((slice, idx) => (
                <tr key={idx} className="table-row-hover">
                  <td className="font-semibold">{slice.slice}</td>
                  <td className="font-mono text-dim">{slice.sampleCount}</td>
                  <td className="font-mono text-emerald">{slice.brierScore}</td>
                  <td className="font-mono text-cyan">{slice.passRate}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="calibration-notes-box">
            <Info size={16} className="text-cyan" />
            <p className="font-mono text-dim">
              Model Card: Platt coefficients derived from N=2,000 synthetic benchmark cases. Evaluated under ISO/IEC 30107-3 presentation attack metrics.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
