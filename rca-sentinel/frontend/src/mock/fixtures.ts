/**
 * RCA-Sentinel Deterministic Factory Fixtures
 * Rich manufacturing dataset: 4 lines, 20 machines, 3 supplier tiers,
 * maintenance crews, failure catalog, and the Golden Scenario ground truth.
 */

export interface MachineStation {
  id: string;
  name: string;
  lineId: string;
  type: 'stamping' | 'milling' | 'welding' | 'inspection' | 'assembly';
  status: 'nominal' | 'warning' | 'critical' | 'interlocked';
  oee: number;
  scrapRate: number; // percentage
  vibrationMmS: number;
  temperatureC: number;
  lastCalibrationDate: string;
  lastCalibratedBy: string;
  currentLotId: string;
  spindleOffsetMm?: number;
}

export interface ProductionLine {
  id: string;
  name: string;
  targetYield: number;
  currentYield: number;
  scrapRate: number;
  status: 'nominal' | 'degraded' | 'halted';
  currentOutputPpm: number;
  targetOutputPpm: number;
  stations: string[]; // station IDs
}

export interface SupplierLot {
  id: string;
  supplierName: string;
  supplierTier: 1 | 2 | 3;
  vendorCode: string;
  materialType: string;
  siliconContentPct: number;
  specCeilingPct: number;
  quarantineStatus: 'released' | 'quarantined' | 'verified_buffer';
  receivedDate: string;
  quantityKg: number;
  defectPpmHistory: number;
  riskScore: number; // 0-100
}

export interface MaintenanceCrew {
  id: string;
  name: string;
  leadTechnician: string;
  shift: 'A' | 'B' | 'C';
  complianceRate: number;
  avgHandoverMinutes: number;
  handoverQuality: 'nominal' | 'rushed' | 'exemplary';
  mtbfHours: number;
  activeWorkOrders: number;
}

export interface IncidentEvidence {
  id: string;
  title: string;
  category: 'material' | 'maintenance' | 'telemetry' | 'operational';
  confidence: number;
  liftScore: number;
  sourceSystem: string;
  sourceRecordId: string;
  evidenceHash: string; // SHA-256 for audit
  description: string;
  isCulprit: boolean;
  claimsSupported: string[];
}

export interface RcaActionProposal {
  id: string;
  type: 'plc_interlock' | 'erp_quarantine' | 'cmms_work_order';
  title: string;
  targetEntity: string;
  description: string;
  justification: string;
  estimatedLossAvoided: number;
  riskLevel: 'low' | 'moderate' | 'extreme';
  reversibility: 'instant' | 'requires_recalibration' | 'staged';
  status: 'pending' | 'approved' | 'rejected' | 'executed' | 'rolled_back';
  slaSecondsRemaining: number;
  signedBy?: string;
  executedAt?: string;
}

// ── 1. Production Lines ──────────────────────────────────────────────────────────

export const INITIAL_LINES: ProductionLine[] = [
  {
    id: 'line-01',
    name: 'Line 01 (Chassis Stamping)',
    targetYield: 99.4,
    currentYield: 99.2,
    scrapRate: 0.8,
    status: 'nominal',
    currentOutputPpm: 280,
    targetOutputPpm: 285,
    stations: ['st-01a', 'st-01b', 'st-01c', 'st-01d', 'st-01e'],
  },
  {
    id: 'line-02',
    name: 'Line 02 (Powertrain Machining)',
    targetYield: 99.0,
    currentYield: 98.9,
    scrapRate: 1.1,
    status: 'nominal',
    currentOutputPpm: 310,
    targetOutputPpm: 315,
    stations: ['st-02a', 'st-02b', 'st-02c', 'st-02d', 'st-02e'],
  },
  {
    id: 'line-03',
    name: 'Line 03 (Precision Spindle Assembly)',
    targetYield: 99.2,
    currentYield: 87.8, // 12.2% scrap spike!
    scrapRate: 12.2,
    status: 'degraded',
    currentOutputPpm: 215,
    targetOutputPpm: 290,
    stations: ['st-03a', 'st-03b', 'st-03c', 'st-03d', 'st-03e'],
  },
  {
    id: 'line-04',
    name: 'Line 04 (Final Electronics & QA)',
    targetYield: 99.5,
    currentYield: 99.1,
    scrapRate: 0.9,
    status: 'nominal',
    currentOutputPpm: 240,
    targetOutputPpm: 245,
    stations: ['st-04a', 'st-04b', 'st-04c', 'st-04d', 'st-04e'],
  },
];

// ── 2. Machine Stations ─────────────────────────────────────────────────────────

export const INITIAL_STATIONS: MachineStation[] = [
  // Line 01
  { id: 'st-01a', name: 'Raw Infeed Blanker', lineId: 'line-01', type: 'stamping', status: 'nominal', oee: 92.4, scrapRate: 0.4, vibrationMmS: 0.9, temperatureC: 38.2, lastCalibrationDate: '2024-09-08', lastCalibratedBy: 'Crew A', currentLotId: 'lot-40810' },
  { id: 'st-01b', name: 'Hydraulic Press #1', lineId: 'line-01', type: 'stamping', status: 'nominal', oee: 91.0, scrapRate: 0.5, vibrationMmS: 1.2, temperatureC: 42.1, lastCalibrationDate: '2024-09-08', lastCalibratedBy: 'Crew A', currentLotId: 'lot-40810' },
  { id: 'st-01c', name: 'Laser Trimmer', lineId: 'line-01', type: 'milling', status: 'nominal', oee: 94.2, scrapRate: 0.2, vibrationMmS: 0.8, temperatureC: 36.4, lastCalibrationDate: '2024-09-07', lastCalibratedBy: 'Crew A', currentLotId: 'lot-40810' },
  { id: 'st-01d', name: 'Robotic Welder A', lineId: 'line-01', type: 'welding', status: 'nominal', oee: 89.8, scrapRate: 0.6, vibrationMmS: 1.1, temperatureC: 55.0, lastCalibrationDate: '2024-09-05', lastCalibratedBy: 'Crew C', currentLotId: 'lot-40810' },
  { id: 'st-01e', name: 'Vision Gage #1', lineId: 'line-01', type: 'inspection', status: 'nominal', oee: 98.1, scrapRate: 0.1, vibrationMmS: 0.4, temperatureC: 24.1, lastCalibrationDate: '2024-09-10', lastCalibratedBy: 'Crew A', currentLotId: 'lot-40810' },

  // Line 02
  { id: 'st-02a', name: 'Rotary Broach', lineId: 'line-02', type: 'milling', status: 'nominal', oee: 90.5, scrapRate: 0.7, vibrationMmS: 1.4, temperatureC: 44.2, lastCalibrationDate: '2024-09-06', lastCalibratedBy: 'Crew C', currentLotId: 'lot-40850' },
  { id: 'st-02b', name: '5-Axis Center A', lineId: 'line-02', type: 'milling', status: 'nominal', oee: 88.9, scrapRate: 0.9, vibrationMmS: 1.5, temperatureC: 48.0, lastCalibrationDate: '2024-09-04', lastCalibratedBy: 'Crew C', currentLotId: 'lot-40850' },
  { id: 'st-02c', name: 'Honing Station', lineId: 'line-02', type: 'milling', status: 'nominal', oee: 93.1, scrapRate: 0.4, vibrationMmS: 1.0, temperatureC: 39.8, lastCalibrationDate: '2024-09-09', lastCalibratedBy: 'Crew A', currentLotId: 'lot-40850' },
  { id: 'st-02d', name: 'Ultrasonic Wash', lineId: 'line-02', type: 'assembly', status: 'nominal', oee: 96.0, scrapRate: 0.1, vibrationMmS: 0.6, temperatureC: 62.1, lastCalibrationDate: '2024-09-11', lastCalibratedBy: 'Crew A', currentLotId: 'lot-40850' },
  { id: 'st-02e', name: 'Air Gage Bore Station', lineId: 'line-02', type: 'inspection', status: 'nominal', oee: 97.4, scrapRate: 0.2, vibrationMmS: 0.5, temperatureC: 23.5, lastCalibrationDate: '2024-09-10', lastCalibratedBy: 'Crew A', currentLotId: 'lot-40850' },

  // Line 03 (THE CULPRIT LINE)
  { id: 'st-03a', name: 'Face Milling 03A', lineId: 'line-03', type: 'milling', status: 'nominal', oee: 86.4, scrapRate: 1.2, vibrationMmS: 1.9, temperatureC: 46.2, lastCalibrationDate: '2024-09-02', lastCalibratedBy: 'Crew B', currentLotId: 'lot-40921' },
  {
    id: 'st-03b',
    name: 'Precision Spindle 03B',
    lineId: 'line-03',
    type: 'milling',
    status: 'critical', // THE FOCAL POINT
    oee: 54.2,
    scrapRate: 12.2,
    vibrationMmS: 4.82, // Anomaly spike
    temperatureC: 78.4,  // Thermal deformation
    lastCalibrationDate: '2024-08-28', // Skipped scheduled tramming
    lastCalibratedBy: 'Crew B',
    currentLotId: 'lot-40921', // Out-of-spec lot
    spindleOffsetMm: 0.035,   // Spec: +-0.010mm
  },
  { id: 'st-03c', name: 'High-Torque Tapper', lineId: 'line-03', type: 'milling', status: 'warning', oee: 78.1, scrapRate: 4.5, vibrationMmS: 2.6, temperatureC: 56.1, lastCalibrationDate: '2024-09-03', lastCalibratedBy: 'Crew B', currentLotId: 'lot-40921' },
  { id: 'st-03d', name: 'Sub-Assembly Press', lineId: 'line-03', type: 'assembly', status: 'nominal', oee: 89.2, scrapRate: 0.8, vibrationMmS: 1.1, temperatureC: 37.0, lastCalibrationDate: '2024-09-08', lastCalibratedBy: 'Crew A', currentLotId: 'lot-40921' },
  { id: 'st-03e', name: 'Automated CMM Gate', lineId: 'line-03', type: 'inspection', status: 'critical', oee: 62.0, scrapRate: 12.2, vibrationMmS: 0.5, temperatureC: 22.8, lastCalibrationDate: '2024-09-12', lastCalibratedBy: 'Crew A', currentLotId: 'lot-40921' },

  // Line 04
  { id: 'st-04a', name: 'SMT Placement #1', lineId: 'line-04', type: 'assembly', status: 'nominal', oee: 95.1, scrapRate: 0.3, vibrationMmS: 0.4, temperatureC: 31.0, lastCalibrationDate: '2024-09-10', lastCalibratedBy: 'Crew A', currentLotId: 'lot-40788' },
  { id: 'st-04b', name: 'Reflow Soldering Oven', lineId: 'line-04', type: 'assembly', status: 'nominal', oee: 93.8, scrapRate: 0.4, vibrationMmS: 0.7, temperatureC: 245.0, lastCalibrationDate: '2024-09-09', lastCalibratedBy: 'Crew A', currentLotId: 'lot-40788' },
  { id: 'st-04c', name: 'Selective Coating', lineId: 'line-04', type: 'assembly', status: 'nominal', oee: 92.0, scrapRate: 0.2, vibrationMmS: 0.5, temperatureC: 28.4, lastCalibrationDate: '2024-09-07', lastCalibratedBy: 'Crew C', currentLotId: 'lot-40788' },
  { id: 'st-04d', name: 'Burn-in Test Rack', lineId: 'line-04', type: 'inspection', status: 'nominal', oee: 96.5, scrapRate: 0.5, vibrationMmS: 0.3, temperatureC: 58.0, lastCalibrationDate: '2024-09-11', lastCalibratedBy: 'Crew A', currentLotId: 'lot-40788' },
  { id: 'st-04e', name: 'Automated Packing Gate', lineId: 'line-04', type: 'assembly', status: 'nominal', oee: 98.2, scrapRate: 0.1, vibrationMmS: 0.6, temperatureC: 24.0, lastCalibrationDate: '2024-09-12', lastCalibratedBy: 'Crew A', currentLotId: 'lot-40788' },
];

// ── 3. Supplier Lots ────────────────────────────────────────────────────────────

export const SUPPLIER_LOTS: SupplierLot[] = [
  {
    id: 'lot-40921',
    supplierName: 'AlloyTech Global',
    supplierTier: 3,
    vendorCode: 'VEND-8812',
    materialType: 'Structural Alloy A36 Mod',
    siliconContentPct: 1.82, // DEFECT: Spec ceiling is 1.35%
    specCeilingPct: 1.35,
    quarantineStatus: 'quarantined',
    receivedDate: '2024-09-14',
    quantityKg: 1200,
    defectPpmHistory: 1420,
    riskScore: 92,
  },
  {
    id: 'lot-40889',
    supplierName: 'PrecisionAlloy Corp',
    supplierTier: 1,
    vendorCode: 'VEND-1044',
    materialType: 'Structural Alloy A36 Mod',
    siliconContentPct: 1.12, // VERIFIED CLEAN ALTERNATIVE
    specCeilingPct: 1.35,
    quarantineStatus: 'verified_buffer',
    receivedDate: '2024-09-12',
    quantityKg: 2800,
    defectPpmHistory: 110,
    riskScore: 14,
  },
  {
    id: 'lot-40810',
    supplierName: 'Kobe Steel Specialties',
    supplierTier: 1,
    vendorCode: 'VEND-2201',
    materialType: 'Deep-Draw Sheet Steel',
    siliconContentPct: 0.94,
    specCeilingPct: 1.20,
    quarantineStatus: 'released',
    receivedDate: '2024-09-10',
    quantityKg: 5000,
    defectPpmHistory: 75,
    riskScore: 8,
  },
  {
    id: 'lot-40850',
    supplierName: 'Apex Precision Billet',
    supplierTier: 2,
    vendorCode: 'VEND-3490',
    materialType: 'Machining Billet 6061-T6',
    siliconContentPct: 0.65,
    specCeilingPct: 0.80,
    quarantineStatus: 'released',
    receivedDate: '2024-09-08',
    quantityKg: 3200,
    defectPpmHistory: 230,
    riskScore: 22,
  },
];

// ── 4. Maintenance Crews ────────────────────────────────────────────────────────

export const MAINTENANCE_CREWS: MaintenanceCrew[] = [
  {
    id: 'crew-a',
    name: 'Maintenance Crew A',
    leadTechnician: 'M. Vance (Master Tech)',
    shift: 'A',
    complianceRate: 99.4,
    avgHandoverMinutes: 15.2,
    handoverQuality: 'exemplary',
    mtbfHours: 142.0,
    activeWorkOrders: 1,
  },
  {
    id: 'crew-b',
    name: 'Maintenance Crew B',
    leadTechnician: 'J. Kowalski',
    shift: 'B',
    complianceRate: 88.2, // WARNING: Frequent rushed handovers
    avgHandoverMinutes: 4.1,  // RUSHED (Target is >= 15 min)
    handoverQuality: 'rushed',
    mtbfHours: 84.5,
    activeWorkOrders: 4,
  },
  {
    id: 'crew-c',
    name: 'Maintenance Crew C',
    leadTechnician: 'D. Rossi',
    shift: 'C',
    complianceRate: 96.1,
    avgHandoverMinutes: 12.8,
    handoverQuality: 'nominal',
    mtbfHours: 118.0,
    activeWorkOrders: 2,
  },
];

// ── 5. Evidence Package for Golden Scenario ─────────────────────────────────────

export const GOLDEN_EVIDENCE_PACKAGE: IncidentEvidence[] = [
  {
    id: 'ev-lot-silicon',
    title: 'Out-of-Specification Silicon in Lot #40921',
    category: 'material',
    confidence: 0.98,
    liftScore: 4.82,
    sourceSystem: 'SAP-QM (Spectrometry Analysis)',
    sourceRecordId: 'LOT-REC-20240915-0012',
    evidenceHash: '8f9a2b71c4d5e89a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a',
    description: 'Silicon content measured at 1.82%, exceeding ASTM-A36 ceiling of 1.35% by +34.8%. Induces severe workpiece hardness heterogeneity.',
    isCulprit: true,
    claimsSupported: ['Workpiece chatter', 'Accelerated spindle tool edge chipping'],
  },
  {
    id: 'ev-skipped-calibration',
    title: 'Skipped Dynamic Spindle Tramming (Crew B)',
    category: 'maintenance',
    confidence: 0.96,
    liftScore: 5.14,
    sourceSystem: 'Maximo CMMS Work Order #WO-88914',
    sourceRecordId: 'CMMS-WO-88914-SHIFT-B',
    evidenceHash: 'c4d5e6f7a8b9c0d1e2f3a8f9a2b71c4d5e89a0b1c2d3e4f5a6b7c8d9e0f1a2b3',
    description: 'Maintenance Crew B marked scheduled 200-hour dynamic tramming as complete during a 4-minute shift handover without recording dial indicator runout. Station-03b runout measured at 0.035mm (Tolerance: +-0.010mm).',
    isCulprit: true,
    claimsSupported: ['Spindle eccentricity', 'Thermal deformation under hard alloy feed'],
  },
  {
    id: 'ev-compound-interaction',
    title: 'Compound Thermal Warp Failure (FM-WAF-001)',
    category: 'operational',
    confidence: 0.94,
    liftScore: 6.20,
    sourceSystem: 'Neo4j Multi-Hop Graph Traversal',
    sourceRecordId: 'GRAPH-TRAVERSAL-PATH-8921',
    evidenceHash: '1a2b3c4d5e6f7a8b9c0d1e2f3a8f9a2b71c4d5e89a0b1c2d3e4f5a6b7c8d9e0f',
    description: 'Hard alloy workpiece (Lot #40921) encountering eccentric spindle (0.035mm offset) exponentially increased cutting friction, generating 78.4C thermal spindle warp within 12 minutes.',
    isCulprit: true,
    claimsSupported: ['Rapid 12.2% scrap spike', 'Dimensional failure at CMM Gate'],
  },
  {
    id: 'ev-decoy-tool-wear',
    title: 'Decoy: Tool Wear Degradation on Station-03A',
    category: 'telemetry',
    confidence: 0.12,
    liftScore: 1.05,
    sourceSystem: 'Beckhoff PLC High-Speed Telemetry',
    sourceRecordId: 'PLC-LOG-ST03A-20240915',
    evidenceHash: '2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a',
    description: 'Tool cycle count was at 82% of life limit. However, vibration signatures on 03A remained nominal (1.9 mm/s) prior to part transfer to 03B.',
    isCulprit: false,
    claimsSupported: [],
  },
];

// ── 6. Action Proposals for Golden Scenario ────────────────────────────────────

export const INITIAL_ACTION_PROPOSALS: RcaActionProposal[] = [
  {
    id: 'act-001-interlock',
    type: 'plc_interlock',
    title: 'Emergency PLC Feed-Hold Interlock: Station-03B',
    targetEntity: 'Machine Station-03b (Line 03)',
    description: 'Signal PLC controller to execute feed-hold and disengage spindle motor drive to prevent catastrophic tool wreck and thermal bearing destruction.',
    justification: 'Vibration currently at 4.82 mm/s with 78.4C spindle temp. Continued operation guarantees 100% defective parts and $62,000/hr in compounded losses.',
    estimatedLossAvoided: 62000,
    riskLevel: 'extreme',
    reversibility: 'instant',
    status: 'pending',
    slaSecondsRemaining: 680,
  },
  {
    id: 'act-002-quarantine',
    type: 'erp_quarantine',
    title: 'ERP Quarantine of Lot #40921 & Feeder Switch to Lot #40889',
    targetEntity: 'Material Lot #40921 (AlloyTech Global)',
    description: 'Place global quality block on Lot #40921 in SAP-MM across all plants. Reroute Line 03 hopper feed to Verified Buffer Lot #40889 (1.12% Si).',
    justification: 'AlloyTech silicon at 1.82% (+34.8% over limit). Verified lot already staged at Buffer 03 and ready for production within 8 minutes.',
    estimatedLossAvoided: 54400,
    riskLevel: 'moderate',
    reversibility: 'staged',
    status: 'pending',
    slaSecondsRemaining: 900,
  },
  {
    id: 'act-003-work-order',
    type: 'cmms_work_order',
    title: 'Dispatch Priority Emergency Spindle Tramming (Crew A)',
    targetEntity: 'Station-03b Spindle Head',
    description: 'Issue urgent CMMS priority work order WO-9921 for dynamic dial-indicator runout realignment. Assign to Master Tech M. Vance (Crew A).',
    justification: 'Current runout is 0.035mm vs +-0.010mm tolerance. Alignment restoration required before Line 03 restart.',
    estimatedLossAvoided: 12000,
    riskLevel: 'low',
    reversibility: 'requires_recalibration',
    status: 'pending',
    slaSecondsRemaining: 1800,
  },
];
