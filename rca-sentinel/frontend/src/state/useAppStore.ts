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
    diagnose: 'Multi-hop graph traversal linked Machine Station-03B with Material Lot #40921 (AlloyTech Global) and Maintenance Crew B shift handover records. Hard alloy silicon measured at 1.82% (+34.8% over 1.35% spec ceiling) in conjunction with 0.035mm spindle runout caused severe tool chatter and 78.4C thermal spindle warp. Alternative causes (Tool Wear, Operator Fatigue) ruled out with p < 0.001.',
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
  dataMode: 'mock',
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

  setTheme: (theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    set({ theme });
  },
  toggleTheme: () => {
    const nextTheme = get().theme === 'night' ? 'day' : 'night';
    document.documentElement.setAttribute('data-theme', nextTheme);
    set({ theme: nextTheme });
  },
  setRole: (role) => set({ role }),
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
  setPresenterActive: (active) => set({ presenterActive: active }),
  setPresenterStep: (step) => set({ presenterStep: step }),

  setTimelineStage: (stage) => {
    const s = Math.max(0, Math.min(7, stage));
    // Dynamically adjust machine and line states based on stage
    const lines = [...get().lines];
    const stations = [...get().stations];
    const targetLine = lines.find((l) => l.id === 'line-03');
    const targetStation = stations.find((st) => st.id === 'st-03b');

    if (s === 0) {
      // Nominal
      if (targetLine) {
        targetLine.currentYield = 99.2;
        targetLine.scrapRate = 0.8;
        targetLine.status = 'nominal';
      }
      if (targetStation) {
        targetStation.status = 'nominal';
        targetStation.vibrationMmS = 1.2;
        targetStation.temperatureC = 42.0;
        targetStation.scrapRate = 0.8;
      }
    } else if (s >= 1 && s < 7) {
      // Anomaly Spike active
      if (targetLine) {
        targetLine.currentYield = 87.8;
        targetLine.scrapRate = 12.2;
        targetLine.status = 'degraded';
      }
      if (targetStation) {
        targetStation.status = 'critical';
        targetStation.vibrationMmS = 4.82;
        targetStation.temperatureC = 78.4;
        targetStation.scrapRate = 12.2;
      }
    } else if (s >= 7) {
      // Actions Executed & Line Halted/Contained
      if (targetLine) {
        targetLine.currentYield = 98.4;
        targetLine.scrapRate = 1.6;
        targetLine.status = 'halted';
      }
      if (targetStation) {
        targetStation.status = 'interlocked';
        targetStation.vibrationMmS = 0.0;
        targetStation.temperatureC = 28.5;
        targetStation.scrapRate = 0.0;
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
