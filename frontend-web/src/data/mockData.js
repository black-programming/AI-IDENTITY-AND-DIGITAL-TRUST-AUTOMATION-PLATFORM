// Mock Data for AegisTrust AI Platform
export const MOCK_SYSTEM_METRICS = {
  trustIndex: 99.4,
  trustIndexDelta: '+1.8% vs last week',
  docsProcessedToday: 14892,
  autonomousPassRate: 94.2,
  fraudInterceptionRate: 99.87,
  avgLatencyMs: 482,
  neuralNodesActive: 32,
  clusterHealth: 'OPTIMAL',
  uptime: '99.99%',
  modelCalibrationVersion: 'v1.2.0-calibrated (YOLOv8 + PaddleOCR + Platt Scorer)'
};

export const MOCK_DOCUMENTS = {
  aadhaar: {
    id: 'DOC-AADHAAR-8901',
    type: 'Aadhaar Card (UIDAI)',
    docNumber: 'XXXX-XXXX-4921',
    holderName: 'KAVITHA RANGANATHAN',
    dob: '1990-08-14',
    gender: 'FEMALE',
    issueDate: '2019-11-04',
    address: '42, Cyber Security Ave, Chennai, TN 600096',
    qrPayloadValid: true,
    hologramDetected: true,
    yoloBoundingBoxes: [
      { label: 'EMBLEM', x: 8, y: 10, w: 22, h: 26, confidence: 0.99 },
      { label: 'PHOTO', x: 12, y: 42, w: 25, h: 48, confidence: 0.98 },
      { label: 'NAME_BLOCK', x: 42, y: 22, w: 52, h: 18, confidence: 0.97 },
      { label: 'DOB_GENDER', x: 42, y: 44, w: 46, h: 14, confidence: 0.95 },
      { label: 'AADHAAR_NUM', x: 40, y: 76, w: 54, h: 16, confidence: 0.99 }
    ],
    ocrFields: [
      { key: 'Document Type', value: 'Government of India - Unique Identification', confidence: 0.99 },
      { key: 'Full Name', value: 'Kavitha Ranganathan', confidence: 0.98 },
      { key: 'Date of Birth', value: '14/08/1990', confidence: 0.97 },
      { key: 'Gender', value: 'Female', confidence: 0.99 },
      { key: 'Masked UID', value: '•••• •••• 4921', confidence: 0.99 },
      { key: 'Verhoeff Checksum', value: 'VALID (Algorithm Passed)', confidence: 1.0 }
    ],
    riskScore: 0.04, // 4% risk = 96% trust
    verdict: 'ALLOW',
    hash: '8f4c2b9a1e05d43e2a9b6c8109d43f2187b419c820efbc1d8a9e0123fabc4567',
    policyCheck: 'All 7 deterministic compliance rules passed without exception.'
  },
  pan: {
    id: 'DOC-PAN-3312',
    type: 'Permanent Account Number (PAN Card)',
    docNumber: 'ABCDE1234F',
    holderName: 'ROHIT S. VERMA',
    fatherName: 'SURESH VERMA',
    dob: '1988-05-22',
    issueDate: '2016-03-18',
    qrPayloadValid: true,
    hologramDetected: true,
    yoloBoundingBoxes: [
      { label: 'GOV_HEADER', x: 10, y: 8, w: 80, h: 18, confidence: 0.99 },
      { label: 'PHOTO', x: 10, y: 32, w: 26, h: 46, confidence: 0.97 },
      { label: 'PAN_NUM', x: 42, y: 32, w: 48, h: 18, confidence: 0.98 },
      { label: 'NAME', x: 42, y: 54, w: 50, h: 14, confidence: 0.96 },
      { label: 'SIGNATURE', x: 42, y: 74, w: 45, h: 20, confidence: 0.94 }
    ],
    ocrFields: [
      { key: 'PAN Format', value: '5 Letters + 4 Digits + 1 Letter', confidence: 1.0 },
      { key: 'Cardholder Name', value: 'Rohit S. Verma', confidence: 0.98 },
      { key: 'Father\'s Name', value: 'Suresh Verma', confidence: 0.95 },
      { key: 'Date of Birth', value: '22/05/1988', confidence: 0.99 },
      { key: 'Permanent Acc Number', value: 'ABCDE1234F', confidence: 0.99 },
      { key: 'Income Tax Seal', value: 'GENUINE (Optical Matched)', confidence: 0.96 }
    ],
    riskScore: 0.08,
    verdict: 'ALLOW',
    hash: '3e120fbb728a0d9e4a5c689b1428c92b8d41e739fa08bc63e157291a8cd90214',
    policyCheck: 'ITD structure validated. Category fourth-character represents Individual (P).'
  },
  dl: {
    id: 'DOC-DL-7721',
    type: 'Indian Driving Licence (Parivahan)',
    docNumber: 'DL-TN-2021-998811',
    holderName: 'JOHN SYNTH DRIVER',
    dob: '1992-09-21',
    vehicleClasses: 'LMV, MCWG',
    issueDate: '2021-02-10',
    expiryDate: '2031-02-10',
    issuingRTO: 'TN-09 (South Chennai)',
    qrPayloadValid: true,
    hologramDetected: true,
    yoloBoundingBoxes: [
      { label: 'STATE_HEADER', x: 12, y: 8, w: 76, h: 20, confidence: 0.99 },
      { label: 'PHOTO', x: 12, y: 34, w: 24, h: 44, confidence: 0.98 },
      { label: 'DL_NUMBER', x: 40, y: 32, w: 52, h: 16, confidence: 0.97 },
      { label: 'VALIDITY', x: 40, y: 52, w: 50, h: 16, confidence: 0.96 },
      { label: 'CHIP_EMV', x: 74, y: 72, w: 18, h: 22, confidence: 0.99 }
    ],
    ocrFields: [
      { key: 'State & RTO', value: 'Tamil Nadu - TN-09', confidence: 0.99 },
      { key: 'Licence Holder', value: 'John Synth Driver', confidence: 0.98 },
      { key: 'Authorised Classes', value: 'LMV (Light Motor) & MCWG (Motorcycle)', confidence: 0.97 },
      { key: 'Issue Date', value: '10/02/2021', confidence: 0.99 },
      { key: 'Validity Expiry', value: '10/02/2031 (Active)', confidence: 0.99 },
      { key: 'SmartCard Microchip', value: 'INTEGRITY VERIFIED', confidence: 0.99 }
    ],
    riskScore: 0.05,
    verdict: 'ALLOW',
    hash: '7c89a012de934bca81923e01fc82d71629487c53e02914ba192389dc129034aa',
    policyCheck: 'Active non-expired credential. Match rate 99.1% across national registry.'
  }
};

export const MOCK_RECENT_VERIFICATIONS = [
  {
    caseId: 'CASE-2026-9481',
    applicant: 'Dr. Aris Thorne',
    docType: 'Aadhaar Card',
    status: 'VERIFIED',
    riskLevel: 'LOW (0.02)',
    latency: '394ms',
    time: '2 mins ago',
    hash: '0x9fa1...8b21'
  },
  {
    caseId: 'CASE-2026-9480',
    applicant: 'Elena Rostova',
    docType: 'Permanent Account No.',
    status: 'VERIFIED',
    riskLevel: 'LOW (0.07)',
    latency: '412ms',
    time: '6 mins ago',
    hash: '0x3dc4...19f0'
  },
  {
    caseId: 'CASE-2026-9479',
    applicant: 'Marcus Vance',
    docType: 'Driving Licence',
    status: 'REVIEW_NEEDED',
    riskLevel: 'ELEVATED (0.48)',
    latency: '580ms',
    time: '14 mins ago',
    hash: '0x7e29...aa01'
  },
  {
    caseId: 'CASE-2026-9478',
    applicant: 'Sarah Jenkins',
    docType: 'Aadhaar Card',
    status: 'VERIFIED',
    riskLevel: 'LOW (0.03)',
    latency: '378ms',
    time: '21 mins ago',
    hash: '0x11ab...6042'
  },
  {
    caseId: 'CASE-2026-9477',
    applicant: 'Kenji Takahashi',
    docType: 'Driving Licence',
    status: 'REJECTED_SUSPICIOUS',
    riskLevel: 'CRITICAL (0.94)',
    latency: '490ms',
    time: '34 mins ago',
    hash: '0xee92...9901'
  }
];

export const MOCK_AUDIT_LOGS = [
  {
    block: '#849,201',
    event: 'CRYPTOGRAPHIC_PROOF_SEALED',
    entity: 'CASE-2026-9481',
    hash: 'e4b3c2a19...d098e',
    signer: 'AegisNode-Mumbai-01',
    status: 'SEALED_ON_CHAIN'
  },
  {
    block: '#849,200',
    event: 'YOLO_ENTITY_EXTRACTION_SUCCESS',
    entity: 'CASE-2026-9481',
    hash: '7b9e01fa2...8832a',
    signer: 'NeuralCore-v1.2',
    status: 'COMPLETED'
  },
  {
    block: '#849,199',
    event: 'PLATT_RISK_CALIBRATION_EVAL',
    entity: 'CASE-2026-9480',
    hash: '921af093c...4120f',
    signer: 'RiskEngine-Alpha',
    status: 'LOW_RISK_ALLOW'
  },
  {
    block: '#849,198',
    event: 'HUMAN_REVIEW_DISPATCH_POLICY',
    entity: 'CASE-2026-9479',
    hash: '490ba3291...3892c',
    signer: 'PolicyOrchestrator',
    status: 'ROUTED_TO_OFFICER'
  }
];

export const MOCK_SECURITY_THREATS = [
  {
    id: 'SEC-ALRT-01',
    type: 'Synthetic Document Injection Attempt',
    severity: 'HIGH',
    sourceIp: '194.26.29.112 (Proxy / TOR Exit)',
    targetEndpoint: '/api/v1/evidence/upload',
    mitigation: 'Automated Quarantine + Rate Limiting Triggered (429)',
    time: '12m ago'
  },
  {
    id: 'SEC-ALRT-02',
    type: 'High-Frequency Token Rotation',
    severity: 'MEDIUM',
    sourceIp: '103.21.244.0 (Subnet Scan)',
    targetEndpoint: '/api/v1/auth/refresh',
    mitigation: 'Adaptive Challenge Enforced',
    time: '1h 24m ago'
  }
];
