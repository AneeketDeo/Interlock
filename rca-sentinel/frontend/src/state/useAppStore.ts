import { create } from 'zustand';
import {
  INITIAL_LINES,
  INITIAL_STATIONS,
  INITIAL_ACTION_PROPOSALS,
  GOLDEN_EVIDENCE_PACKAGE,
  SUPPLIER_LOTS,
  MAINTENANCE_CREWS,
  ProductionLine,
  MachineStation,
  RcaActionProposal,
  IncidentEvidence,
  SupplierLot,
  MaintenanceCrew,
} from '../mock/fixtures';
import { fetchMachines, fetchSpannerLots, SpannerMachine } from '../lib/api';

export type UserRole = 'reliability_engineer' | 'quality_engineer' | 'operator' | 'plant_manager';
export type AppTheme = 'night' | 'day';

export interface RcaCase {
  id: string;
  title: string;
  severity: 'critical' | 'caution' | 'nominal';
  status: 'active' | 'contained' | 'resolved';
  lineId: string;
  stationId: string;
  detectedAt: string;
  elapsedSeconds: number;
  stageProgress: {
    detect: 'done' | 'running' | 'pending';
    diagnose: 'done' | 'running' | 'pending';
    classify: 'done' | 'running' | 'pending';
    forecast: 'done' | 'running' | 'pending';
    remediate: 'done' | 'running' | 'pending';
  };
  agentNotes: {
    detect: string;
    diagnose: string;
    classify: string;
    forecast: string;
    remediate: string;
  };
  blastRadiusUnits: number;
  grossFinancialExposure: number;
  avoidedLoss: number;
  failureModeCode: string;
  rpnScore: number;
}

interface AppState {
  theme: AppTheme;
  role: UserRole;
  dataMode: 'mock' | 'live';
  isSpannerConnected: boolean;
  isDryRun: boolean;
  commandPaletteOpen: boolean;
  presenterActive: boolean;
  presenterStep: number;
  
  // Scenario Timeline State (0 = Nominal, 1 = Spike, 2 = Detect, 3 = Diagnose, 4 = Classify, 5 = Forecast, 6 = Remediate, 7 = Executed)
  timelineStage: number;
  isPlaying: boolean;
  playbackSpeed: number; // 0.5, 1, 2

  // Domain State
  lines: ProductionLine[];
  stations: MachineStation[];
  activeCase: RcaCase;
  proposals: RcaActionProposal[];
  evidence: IncidentEvidence[];
  lots: SupplierLot[];
  crews: MaintenanceCrew[];

  // Actions
  setTheme: (theme: AppTheme) => void;
  toggleTheme: () => void;
  setRole: (role: UserRole) => void;
  setDataMode: (mode: 'mock' | 'live') => void;
  toggleDataMode: () => void;
  loadSpannerData: () => Promise<void>;
  setCommandPaletteOpen: (open: boolean) => void;
  setPresenterActive: (active: boolean) => void;
  setPresenterStep: (step: number) => void;
  
  // Scenario Control Actions
  setTimelineStage: (stage: number) => void;
  setIsPlaying: (playing: boolean) => void;
  setPlaybackSpeed: (speed: number) => void;
  stepForward: () => void;
  stepBackward: () => void;
  resetScenario: () => void;

  // Interventions & HITL
  approveProposal: (proposalId: string, signatoryName?: string) => void;
  rejectProposal: (proposalId: string, reason?: string) => void;
  rollbackProposal: (proposalId: string) => void;
}

const INITIAL_CASE: RcaCase = {
  id: 'INC-8921',
  title: 'Line 03 Scrap Rate Spike (12.2%) & Spindle Thermal Warp',
  severity: 'critical',
  status: 'active',
  lineId: 'line-03',
  stationId: 'st-03b',
  detectedAt: '22:01:14 UTC',
  elapsedSeconds: 228,
  stageProgress: {
    detect: 'done',
    diagnose: 'done',
    classify: 'done',
    forecast: 'done',
    remediate: 'running',
  },
  agentNotes: {
    detect: 'Telemetry EWMA/CUSUM on sensor-vib-03b triggered alarm at 22:01 UTC. scrapRate on Line 03 shifted from 0.8% baseline to 12.2%. 42 consecutive anomaly ticks confirmed without transient recovery.',
    diagnose: 'Cloud Spanner Graph (FactoryGraph) ISO GQL traversal linked Machine station-03b with Material Lot #40921 (AlloyTech Global) and Maintenance Crew B shift handover records. Hard alloy silicon measured at 1.82% (+34.8% over 1.35% spec ceiling) in conjunction with 0.035mm spindle runout caused severe tool chatter and 78.4C thermal spindle warp. Alternative causes (Tool Wear, Operator Fatigue) ruled out with p < 0.001.',
    classify: 'Classified under PFMEA catalog as FM-WAF-001: Thermal Spindle Dynamic Warp. Severity S=8 (Line shutdown), Occurrence O=5 (Shift correlation), Detection D=7 (Found at CMM gate). Total RPN = 280.',
    forecast: 'Forward blast radius traces 420 finished assemblies currently contaminated in Batches #40921-A, B, C across orders Tesla PO-9912 and Boeing Tier-1 PO-9940. Unmitigated financial exposure: $184,800. Net avoided loss upon containment: $128,400.',
    remediate: 'Proposed immediate tri-part physical containment: 1) PLC emergency feed-hold interlock on Station-03b, 2) ERP inventory quarantine of Lot #40921 with auto-reroute to verified buffer Lot #40889, 3) CMMS urgent dispatch of dynamic tramming to Crew A. Gated for human engineering signoff.',
  },
  blastRadiusUnits: 420,
  grossFinancialExposure: 184800,
  avoidedLoss: 128400,
  failureModeCode: 'FM-WAF-001',
  rpnScore: 280,
};

export const useAppStore = create<AppState>((set, get) => ({
  theme: 'night',
  role: 'reliability_engineer',
  dataMode: (import.meta.env.VITE_DATA_MODE as 'live' | 'mock') || 'live',
  isSpannerConnected: false,
  isDryRun: true,
  commandPaletteOpen: false,
  presenterActive: false,
  presenterStep: 0,

  timelineStage: 3, // Defaults to showpiece stage (Root Cause Diagnosed)
  isPlaying: false,
  playbackSpeed: 1,

  lines: INITIAL_LINES,
  stations: INITIAL_STATIONS,
  activeCase: INITIAL_CASE,
  proposals: INITIAL_ACTION_PROPOSALS,
  evidence: GOLDEN_EVIDENCE_PACKAGE,
  lots: SUPPLIER_LOTS,
  crews: MAINTENANCE_CREWS,

  setDataMode: (mode) => {
    set({ dataMode: mode });
    if (mode === 'live') {
      get().loadSpannerData();
    } else {
      set({
        lines: INITIAL_LINES,
        stations: INITIAL_STATIONS,
        lots: SUPPLIER_LOTS,
        crews: MAINTENANCE_CREWS,
        isSpannerConnected: false,
      });
    }
  },

  toggleDataMode: () => {
    const next = get().dataMode === 'live' ? 'mock' : 'live';
    get().setDataMode(next);
  },

  loadSpannerData: async () => {
    try {
      const [machines, spannerLots] = await Promise.all([
        fetchMachines(),
        fetchSpannerLots(),
      ]);

      if (!machines || machines.length === 0) {
        return;
      }

      // Group machines by line
      const lineMap: Record<string, SpannerMachine[]> = {};
      for (const m of machines) {
        if (!lineMap[m.line_id]) lineMap[m.line_id] = [];
        lineMap[m.line_id].push(m);
      }

      const lineNames: Record<string, string> = {
        L1: 'Line 01 (Housing Machining)',
        L2: 'Line 02 (Shaft Turning)',
        L3: 'Line 03 (Ring Gear Grinding)',
      };

      const lineRates: Record<string, number> = {
        L1: 150,
        L2: 190,
        L3: 130,
      };

      const affectedMachines = new Set(['M02', 'M03', 'M06', 'M09', 'M11']);

      const lines: ProductionLine[] = Object.keys(lineMap).map((lineId) => {
        const ms = lineMap[lineId];
        const hasAffected = ms.some((m) => affectedMachines.has(m.id));
        return {
          id: lineId,
          name: lineNames[lineId] || `Line ${lineId}`,
          targetYield: 99.2,
          currentYield: hasAffected ? 88.2 : 99.4,
          scrapRate: hasAffected ? 11.8 : 0.6,
          status: hasAffected ? 'degraded' : 'nominal',
          currentOutputPpm: lineRates[lineId] || 150,
          targetOutputPpm: (lineRates[lineId] || 150) + 10,
          stations: ms.map((m) => m.id),
        };
      });

      const stations: MachineStation[] = machines.map((m) => {
        const isCritical = affectedMachines.has(m.id);
        const stationType = m.type.toLowerCase().includes('mill')
          ? 'milling'
          : m.type.toLowerCase().includes('turning') || m.type.toLowerCase().includes('lathe')
          ? 'milling'
          : m.type.toLowerCase().includes('grinder')
          ? 'milling'
          : 'assembly';

        return {
          id: m.id,
          name: `${m.name} (${m.id})`,
          lineId: m.line_id,
          type: stationType,
          status: isCritical ? 'critical' : 'nominal',
          oee: isCritical ? 64.2 : 88.5,
          scrapRate: isCritical ? 11.8 : 0.6,
          vibrationMmS: isCritical ? 4.82 : 1.25,
          temperatureC: isCritical ? 78.4 : 42.0,
          lastCalibrationDate: '2026-10-14',
          lastCalibratedBy: isCritical ? 'Crew A (Rushed)' : 'Crew B',
          currentLotId: isCritical ? 'LOT-409' : 'LOT-377',
          spindleOffsetMm: isCritical ? 0.035 : 0.005,
        };
      });

      let lots: SupplierLot[] = get().lots;
      if (spannerLots && spannerLots.length > 0) {
        lots = spannerLots.map((l) => {
          const isCulprit = l.lot_id === 'LOT-409' || l.edge_flag === 'UPPER_EDGE_ALL';
          const tier = (l.supplier_tier === 1 || l.supplier_tier === 2 || l.supplier_tier === 3)
            ? (l.supplier_tier as 1 | 2 | 3)
            : 1;

          return {
            id: l.lot_id,
            supplierName: l.supplier_name || 'Apex Drivetrain Systems',
            supplierTier: tier,
            vendorCode: l.supplier_id || 'SUP-T1-01',
            materialType: '20MnCr5 Structural Alloy Steel',
            siliconContentPct: isCulprit ? 1.82 : 1.15,
            specCeilingPct: 1.35,
            quarantineStatus: isCulprit ? 'quarantined' : 'released',
            receivedDate: '2026-10-06',
            quantityKg: l.qty_kg || 12000,
            defectPpmHistory: isCulprit ? 1420 : 310,
            riskScore: isCulprit ? 94 : 12,
          };
        });
      }

      const spannerCase: RcaCase = {
        id: 'INC-20261015-01',
        title: 'Multi-Machine Scrap Spike on Milling Centers (M02, M03, M06, M09, M11)',
        severity: 'critical',
        status: 'active',
        lineId: 'L1',
        stationId: 'M02',
        detectedAt: '2026-10-15T07:15:00Z',
        elapsedSeconds: 312,
        stageProgress: {
          detect: 'done',
          diagnose: 'done',
          classify: 'done',
          forecast: 'done',
          remediate: 'running',
        },
        agentNotes: {
          detect: 'Scrap spike detected on 5 CNC milling work centers (M02, M03, M06, M09, M11) across Lines L1, L2, L3. Machine scrap jumped from 0.8% baseline to 11.8%. Persistent shift confirmed at automated inspection.',
          diagnose: 'Cloud Spanner ISO GQL multi-hop traversal confirmed compound interaction: MaterialLot LOT-409 (Apex Drivetrain Systems / Tier-3 Meridian Specialty Steels, 31.7 HRC, 0.219% C, UPPER_EDGE_ALL) processed across machines coinciding with rushed shift handover HO-20261014-S (6.0 mins duration) by Crew A that skipped Step 6: Thermal offset verification (CAL-0021..CAL-0027). Machine intersection: M02, M03, M06, M09, M11.',
          classify: 'Classified under PFMEA catalog as FM-01 / FM-02: Upper-Edge Hardness Alloy Chatter under Unverified Thermal Spindle Offset. Severity S=8, Occurrence O=5, Detection D=7. Total RPN = 280.',
          forecast: 'Forward blast radius traces 8 machines total that processed LOT-409 across Lines L1, L2, L3. Unmitigated exposure: $184,800. Net avoided loss upon containment: $128,400.',
          remediate: 'Proposed immediate tri-part physical containment: 1) PLC emergency feed-hold interlock on affected stations (M02, M03, M06, M09, M11), 2) ERP quarantine of LOT-409 with auto-reroute to verified buffer LOT-377, 3) CMMS urgent dispatch of Step 6 Thermal offset recalibration to Crew B. Gated for human engineering signoff.',
        },
        blastRadiusUnits: 420,
        grossFinancialExposure: 184800,
        avoidedLoss: 128400,
        failureModeCode: 'FM-01 / FM-02',
        rpnScore: 280,
      };

      const spannerCrews: MaintenanceCrew[] = [
        {
          id: 'crew-a',
          name: 'Crew A (Morning Shift)',
          shift: 'A',
          leadTechnician: 'J. Martinez (Lead Specialist)',
          complianceRate: 87.5,
          avgHandoverMinutes: 6.0,
          handoverQuality: 'rushed',
          mtbfHours: 412,
          activeWorkOrders: 4,
        },
        {
          id: 'crew-b',
          name: 'Crew B (Swing Shift)',
          shift: 'B',
          leadTechnician: 'D. Kowalski (Master Millwright)',
          complianceRate: 100.0,
          avgHandoverMinutes: 32.4,
          handoverQuality: 'exemplary',
          mtbfHours: 648,
          activeWorkOrders: 1,
        },
        {
          id: 'crew-c',
          name: 'Crew C (Graveyard Shift)',
          shift: 'C',
          leadTechnician: 'S. Patel (Reliability Tech III)',
          complianceRate: 98.2,
          avgHandoverMinutes: 31.0,
          handoverQuality: 'nominal',
          mtbfHours: 590,
          activeWorkOrders: 2,
        },
      ];

      const spannerProposals: RcaActionProposal[] = [
        {
          id: 'act-01',
          type: 'plc_interlock',
          title: 'Emergency PLC Feed-Hold Interlock',
          description: 'Halt feed axes immediately on affected CNC milling centers (M02, M03, M06, M09, M11) to eliminate further out-of-spec scrap generation.',
          justification: 'Work centers M02, M03, M06, M09, M11 running unverified thermal offset with Upper-Edge Lot LOT-409.',
          targetEntity: 'Work Centers M02, M03, M06, M09, M11 (Lines L1, L2, L3)',
          slaSecondsRemaining: 684,
          status: 'pending',
          riskLevel: 'extreme',
          estimatedLossAvoided: 68000,
          reversibility: 'instant',
        },
        {
          id: 'act-02',
          type: 'erp_quarantine',
          title: 'ERP Automated Inventory Quarantine & Buffer Reroute',
          description: 'Lock MaterialLot LOT-409 in SAP/ERP and auto-reroute feed conveyors to verified clean buffer lot LOT-377 (Helix Powertrain, 29.6 HRC).',
          justification: 'Lot LOT-409 upper-edge hardness is generating resonant cutting chatter.',
          targetEntity: 'Raw Material Lot LOT-409 (Apex Drivetrain Systems / Meridian Specialty Steels T3)',
          slaSecondsRemaining: 684,
          status: 'pending',
          riskLevel: 'moderate',
          estimatedLossAvoided: 60400,
          reversibility: 'staged',
        },
        {
          id: 'act-03',
          type: 'cmms_work_order',
          title: 'CMMS Urgent Recalibration Dispatch',
          description: 'Dispatch high-priority work order to Crew B to execute Step 6: Thermal offset verification and dynamic spindle tramming across M02, M03, M06, M09, M11.',
          justification: 'Crew A omitted Step 6 during rushed handover HO-20261014-S.',
          targetEntity: 'CMMS Work Order MO-0028 -> Crew B',
          slaSecondsRemaining: 1800,
          status: 'pending',
          riskLevel: 'low',
          estimatedLossAvoided: 56400,
          reversibility: 'requires_recalibration',
        },
      ];

      set({
        lines,
        stations,
        lots,
        activeCase: spannerCase,
        crews: spannerCrews,
        proposals: spannerProposals,
        dataMode: 'live',
        isSpannerConnected: true,
      });
    } catch (err) {
      console.warn('Could not load live Spanner data:', err);
    }
  },

  setTheme: (theme) => {
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', theme);
    }
    set({ theme });
  },
  toggleTheme: () => {
    const nextTheme = get().theme === 'night' ? 'day' : 'night';
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', nextTheme);
    }
    set({ theme: nextTheme });
  },
  setRole: (role) => set({ role }),
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
  setPresenterActive: (active) => set({ presenterActive: active }),
  setPresenterStep: (step) => set({ presenterStep: step }),

  setTimelineStage: (stage) => {
    const s = Math.max(0, Math.min(7, stage));
    const lines = [...get().lines];
    const stations = [...get().stations];
    const affectedMachineIds = new Set(['st-03b', 'M02', 'M03', 'M06', 'M09', 'M11']);

    for (const line of lines) {
      const hasAffected = line.stations.some((stId) => affectedMachineIds.has(stId));
      if (hasAffected || line.id === 'line-03') {
        if (s === 0) {
          line.currentYield = 99.4;
          line.scrapRate = 0.6;
          line.status = 'nominal';
        } else if (s >= 1 && s < 7) {
          line.currentYield = 88.2;
          line.scrapRate = 11.8;
          line.status = 'degraded';
        } else if (s >= 7) {
          line.currentYield = 98.4;
          line.scrapRate = 1.6;
          line.status = 'halted';
        }
      }
    }

    for (const station of stations) {
      if (affectedMachineIds.has(station.id)) {
        if (s === 0) {
          station.status = 'nominal';
          station.vibrationMmS = 1.25;
          station.temperatureC = 42.0;
          station.scrapRate = 0.6;
          station.oee = 88.5;
        } else if (s >= 1 && s < 7) {
          station.status = 'critical';
          station.vibrationMmS = 4.82;
          station.temperatureC = 78.4;
          station.scrapRate = 11.8;
          station.oee = 64.2;
        } else if (s >= 7) {
          station.status = 'interlocked';
          station.vibrationMmS = 0.0;
          station.temperatureC = 28.5;
          station.scrapRate = 0.0;
          station.oee = 0.0;
        }
      }
    }

    set({ timelineStage: s, lines, stations });
  },

  setIsPlaying: (playing) => set({ isPlaying: playing }),
  setPlaybackSpeed: (playbackSpeed) => set({ playbackSpeed }),

  stepForward: () => {
    const next = get().timelineStage + 1;
    if (next <= 7) get().setTimelineStage(next);
  },
  stepBackward: () => {
    const prev = get().timelineStage - 1;
    if (prev >= 0) get().setTimelineStage(prev);
  },
  resetScenario: () => {
    get().setTimelineStage(0);
    set({
      proposals: INITIAL_ACTION_PROPOSALS.map((p) => ({ ...p, status: 'pending' })),
    });
  },

  approveProposal: (proposalId, signatoryName = 'M. Vance (PE, Reliability)') => {
    const proposals = get().proposals.map((p) =>
      p.id === proposalId
        ? {
            ...p,
            status: 'approved' as const,
            signedBy: signatoryName,
            executedAt: new Date().toISOString(),
          }
        : p
    );
    // If interlock or reroute approved, jump to contained state
    const allApproved = proposals.filter((p) => p.status === 'approved').length >= 2;
    if (allApproved) {
      get().setTimelineStage(7);
    }
    set({ proposals });
  },

  rejectProposal: (proposalId) => {
    const proposals = get().proposals.map((p) =>
      p.id === proposalId ? { ...p, status: 'rejected' as const } : p
    );
    set({ proposals });
  },

  rollbackProposal: (proposalId) => {
    const proposals = get().proposals.map((p) =>
      p.id === proposalId ? { ...p, status: 'rolled_back' as const } : p
    );
    set({ proposals });
  },
}));

// Automatically trigger live Spanner data fetch on app start
if (typeof window !== 'undefined') {
  useAppStore.getState().loadSpannerData();
}
