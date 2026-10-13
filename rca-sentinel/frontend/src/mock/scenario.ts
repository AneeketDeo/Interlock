/**
 * Scenario Timeline Engine
 * Orchestrates the golden scenario playback, telemetry ticks, and stage transitions.
 */

import { useAppStore } from '../state/useAppStore';

export interface ScenarioStepMeta {
  index: number;
  name: string;
  badge: string;
  description: string;
  talkingPoint: string;
}

export const SCENARIO_STEPS: ScenarioStepMeta[] = [
  {
    index: 0,
    name: '1. Baseline Operations',
    badge: 'NOMINAL',
    description: 'All 4 production lines operating within Six Sigma limits at 99.2% plant yield.',
    talkingPoint: 'We begin with nominal factory floor operations across all 4 production lines, with green workpieces moving smoothly at target takt time.',
  },
  {
    index: 1,
    name: '2. Telemetry Anomaly',
    badge: 'SCRAP SPIKE 12.2%',
    description: 'Line 03 scrap counter leaps from 0.8% to 12.2%. Station-03b vibration hits 4.82 mm/s.',
    talkingPoint: 'At 22:01 UTC, streaming CUSUM/EWMA detectors catch a severe scrap spike on Line 03. Machine Station-03B begins thermal vibration runaway.',
  },
  {
    index: 2,
    name: '3. DetectAgent (D2)',
    badge: 'ANOMALY CONFIRMED',
    description: 'Statistical validation confirms persistent shift (p < 0.001) over 42 consecutive cycles.',
    talkingPoint: 'The first ADK agent validates the anomaly, confirming this is not random sensor noise, and automatically generates the D2 problem description.',
  },
  {
    index: 3,
    name: '4. DiagnoseAgent (D4)',
    badge: 'ROOT CAUSE REVEAL',
    description: 'Multi-hop graph traversal pinpoints compound cause: AlloyTech Lot #40921 + Crew B skipped calibration.',
    talkingPoint: 'The DiagnoseAgent traverses the knowledge graph in 1.2 seconds, isolating the compound root cause: out-of-spec alloy from AlloyTech plus skipped calibration by Crew B.',
  },
  {
    index: 4,
    name: '5. ClassifyAgent (PFMEA)',
    badge: 'FM-WAF-001 (RPN 280)',
    description: 'Classified as Thermal Spindle Dynamic Warp with Severity S=8, Occurrence O=5, Detection D=7.',
    talkingPoint: 'The failure mechanism is linked to standard PFMEA catalog FM-WAF-001, calculating an RPN of 280 and establishing formal 8D traceability.',
  },
  {
    index: 5,
    name: '6. ForecastAgent (Risk)',
    badge: '$184.8k EXPOSURE',
    description: 'Forward blast radius identifies 420 downstream assemblies and calculates $184,800 gross financial exposure.',
    talkingPoint: 'The ForecastAgent traces forward to calculate the exact blast radius: 420 units at risk and $184,800 in gross exposure across Tesla and Boeing orders.',
  },
  {
    index: 6,
    name: '7. RemediateAgent (D3/5)',
    badge: 'ACTIONS GATED',
    description: 'Proposes PLC interlock, ERP inventory quarantine, and emergency CMMS work order. Requires human signoff.',
    talkingPoint: 'RemediateAgent crafts 3 specific containment and corrective actions, but halts at the Human-in-the-Loop policy gate for engineering approval.',
  },
  {
    index: 7,
    name: '8. Containment Executed',
    badge: 'CONTAINED • $128.4k SAVED',
    description: 'Human engineer signs approval. Station-03b is interlocked, flow is rerouted to verified batch, lines recover.',
    talkingPoint: 'Upon human approval, physical actuators halt the defective station and reroute feed hoppers to verified stock, recovering $128,400 in avoided loss.',
  },
];

class ScenarioEngine {
  private timer: number | null = null;

  public play() {
    const store = useAppStore.getState();
    store.setIsPlaying(true);
    this.scheduleNextTick();
  }

  public pause() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    useAppStore.getState().setIsPlaying(false);
  }

  public stepForward() {
    const store = useAppStore.getState();
    store.stepForward();
  }

  public stepBackward() {
    const store = useAppStore.getState();
    store.stepBackward();
  }

  public reset() {
    this.pause();
    useAppStore.getState().resetScenario();
  }

  private scheduleNextTick() {
    if (this.timer) clearTimeout(this.timer);
    const store = useAppStore.getState();
    if (!store.isPlaying) return;

    const baseDelayMs = 6000; // 6 seconds per stage in normal speed
    const delay = baseDelayMs / store.playbackSpeed;

    this.timer = window.setTimeout(() => {
      const current = useAppStore.getState().timelineStage;
      if (current < 7) {
        useAppStore.getState().stepForward();
        this.scheduleNextTick();
      } else {
        this.pause();
      }
    }, delay);
  }
}

export const scenarioEngine = new ScenarioEngine();
