import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  Clock,
  User,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';
import { useAppStore } from '../../state/useAppStore';
import { EvidenceGraph, GraphNodeData } from './components/EvidenceGraph';
import { ProvenanceDrawer } from './components/ProvenanceDrawer';

export function IncidentCaseBoard() {
  const navigate = useNavigate();
  const { activeCase, timelineStage, proposals } = useAppStore();
  const [selectedNode, setSelectedNode] = useState<GraphNodeData | null>(null);
  const [activeStageTab, setActiveStageTab] = useState<'detect' | 'diagnose' | 'classify' | 'forecast' | 'remediate'>('diagnose');

  const isContained = timelineStage >= 7;

  const stages = [
    { key: 'detect' as const, label: '1. DETECT (D2)', duration: '0.4s', conf: '99.4%', status: timelineStage >= 2 ? 'done' : 'running' },
    { key: 'diagnose' as const, label: '2. DIAGNOSE (D4)', duration: '1.2s', conf: '94.2%', status: timelineStage >= 3 ? 'done' : 'running' },
    { key: 'classify' as const, label: '3. CLASSIFY (PFMEA)', duration: '0.6s', conf: 'RPN 280', status: timelineStage >= 4 ? 'done' : 'running' },
    { key: 'forecast' as const, label: '4. FORECAST (RISK)', duration: '0.8s', conf: '$184.8k', status: timelineStage >= 5 ? 'done' : 'running' },
    { key: 'remediate' as const, label: '5. REMEDIATE (D3/5)', duration: '0.9s', conf: 'GATED', status: timelineStage >= 7 ? 'done' : 'pending' },
  ];

  return (
    <div className="space-y-6">
      {/* ── Case Header & Problem Statement ──────────────────────────────────── */}
      <div className="p-5 bg-panel border border-subtle rounded-md">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-subtle pb-3">
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold uppercase bg-critical text-white flex items-center gap-1.5">
              <AlertTriangle className="h-3.5 w-3.5" />
              CRITICAL • SEVERITY 8
            </span>
            <span className="font-mono text-xs text-dim">CASE #{activeCase.id}</span>
            <span className="text-dim">/</span>
            <span className="text-xs font-mono text-secondary">AUSTIN LINE 03 &bull; STATION 03B</span>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-1.5 text-secondary">
              <Clock className="h-3.5 w-3.5 text-dim" />
              <span>Detected: {activeCase.detectedAt}</span>
            </div>
            <div className="flex items-center gap-1.5 text-secondary">
              <User className="h-3.5 w-3.5 text-dim" />
              <span>Owner: M. Vance (Lead Reliability PE)</span>
            </div>
            <span
              className={`px-2 py-0.5 rounded font-bold uppercase text-[11px] ${
                isContained
                  ? 'bg-healthy-bg text-healthy border border-healthy-border'
                  : 'bg-critical-bg text-critical border border-critical-border animate-pulse'
              }`}
            >
              {isContained ? 'CONTAINMENT ACTIVE' : 'OPEN ANOMALY'}
            </span>
          </div>
        </div>

        {/* Auto-Written Problem Statement */}
        <div className="mt-3">
          <h2 className="font-heading font-bold text-xl text-white">
            {activeCase.title}
          </h2>
          <p className="text-xs text-secondary mt-1 leading-relaxed max-w-4xl font-sans">
            At 22:01 UTC, vibration telemetry on Precision Spindle Station-03b shifted to 4.82 mm/s, causing a 12.2% scrap spike at the automated CMM gate. The diagnostic pipeline backward-traced through the knowledge graph in 1.2s to isolate a compound root cause: out-of-specification raw material from AlloyTech Global (Lot #40921, 1.82% Si) combined with an uncalibrated spindle runout offset (0.035 mm) skipped by Maintenance Crew B during a rushed shift handover.
          </p>
        </div>
      </div>

      {/* ── Five-Stage Diagnostic Pipeline Tracker ───────────────────────────── */}
      <div className="bg-panel border border-subtle rounded-md p-4">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {stages.map((st) => {
            const isSelected = activeStageTab === st.key;
            return (
              <button
                key={st.key}
                onClick={() => setActiveStageTab(st.key)}
                className={`p-3 rounded border text-left transition-all relative ${
                  isSelected
                    ? 'bg-raised border-active ring-1 ring-active'
                    : 'bg-panel border-subtle hover:border-strong'
                }`}
              >
                <div className="flex items-center justify-between text-[10px] font-mono mb-1">
                  <span className="font-bold text-dim uppercase">{st.duration}</span>
                  <span
                    className={`px-1 rounded text-[9px] font-bold uppercase ${
                      st.status === 'done'
                        ? 'bg-healthy/20 text-healthy'
                        : st.status === 'running'
                        ? 'bg-cobalt/20 text-cobalt animate-pulse'
                        : 'bg-raised text-dim'
                    }`}
                  >
                    {st.status}
                  </span>
                </div>
                <div className="font-heading font-bold text-xs text-white truncate">
                  {st.label}
                </div>
                <div className="text-[11px] font-mono text-secondary mt-0.5">
                  Conf: <strong className="text-primary">{st.conf}</strong>
                </div>
              </button>
            );
          })}
        </div>

        {/* Streamed Analyst Reasoning Notes for Selected Stage */}
        <div className="mt-4 p-3 bg-canvas border border-subtle rounded text-xs font-mono">
          <div className="flex items-center justify-between border-b border-subtle/50 pb-1.5 mb-2">
            <span className="text-cobalt font-bold uppercase flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-cobalt animate-ping" />
              ANALYST REASONING LOG: {activeStageTab.toUpperCase()}
            </span>
            <span className="text-dim text-[10px]">VERIFIED GROUNDING • NO HALLUCINATION</span>
          </div>
          <p className="text-secondary leading-relaxed font-sans text-xs">
            {activeCase.agentNotes[activeStageTab]}
          </p>
        </div>
      </div>

      {/* ── Root Cause Reveal: Interactive Evidence Graph (Showpiece) ─────────── */}
      <div className="space-y-2">
        <div className="flex items-center justify-between px-1">
          <div>
            <h3 className="font-heading font-bold text-base text-white tracking-wide">
              ROOT CAUSE REVEAL: MULTI-HOP EVIDENCE GRAPH
            </h3>
            <p className="text-xs text-secondary">
              Trace backward from failing Station-03b to raw supply chain lot and maintenance work orders.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/approvals')}
              className="px-3 py-1.5 rounded bg-critical text-white font-mono text-xs font-bold hover:bg-red-600 transition-colors flex items-center gap-1.5"
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Review Containment Actions ({proposals.filter((p) => p.status === 'pending').length}) &rarr;</span>
            </button>
          </div>
        </div>

        <EvidenceGraph onSelectNode={(node) => setSelectedNode(node)} />
      </div>

      {/* ── Hypotheses Leaderboard & PFMEA Classification ────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hypotheses Leaderboard */}
        <div className="bg-panel border border-subtle rounded-md p-5 flex flex-col justify-between">
          <div className="border-b border-subtle pb-3 flex items-center justify-between">
            <div>
              <h4 className="font-heading font-bold text-sm text-white">
                HYPOTHESES LEADERBOARD (RANKED BY LIFT &amp; CONFIDENCE)
              </h4>
              <p className="text-xs text-secondary mt-0.5">
                Commonality analysis evaluating compound and decoy failure modes.
              </p>
            </div>
          </div>

          <div className="my-3 space-y-3">
            {/* Culprit Hypothesis 1 */}
            <div className="p-3 rounded bg-critical-bg/50 border border-critical-border text-xs">
              <div className="flex items-center justify-between font-mono mb-1">
                <span className="font-bold text-critical">1. COMPOUND CAUSE: ALLOY LOT #40921 + SKIPPED TRAMMING</span>
                <span className="px-1.5 py-0.2 rounded bg-critical text-white font-bold">94.2% CONF</span>
              </div>
              <p className="text-primary text-[11px] leading-relaxed">
                Excess silicon (1.82%) induced hard workpiece chatter, compounding with 0.035mm spindle runout to cause 78.4°C thermal warp within 12 minutes. Lift score: 4.82x across historical failure corpus.
              </p>
            </div>

            {/* Decoy 1 */}
            <div className="p-3 rounded bg-raised border border-subtle text-xs opacity-75">
              <div className="flex items-center justify-between font-mono mb-1">
                <span className="font-bold text-dim line-through">2. DECOY: STATION-03A TOOL WEAR DEGRADATION</span>
                <span className="px-1.5 py-0.2 rounded bg-raised text-dim font-bold">12.4% CONF</span>
              </div>
              <p className="text-secondary text-[11px] leading-relaxed">
                Ruled out: Tool life at 82%, but upstream vibration signatures remained flat at 1.9 mm/s without cross-station vibration transfer.
              </p>
            </div>

            {/* Decoy 2 */}
            <div className="p-3 rounded bg-raised border border-subtle text-xs opacity-75">
              <div className="flex items-center justify-between font-mono mb-1">
                <span className="font-bold text-dim line-through">3. DECOY: OPERATOR SHIFT FATIGUE</span>
                <span className="px-1.5 py-0.2 rounded bg-raised text-dim font-bold">4.1% CONF</span>
              </div>
              <p className="text-secondary text-[11px] leading-relaxed">
                Ruled out: Defect rate correlates directly with Lot #40921 loading timestamp rather than shift hour progression.
              </p>
            </div>
          </div>
        </div>

        {/* PFMEA Classification Card */}
        <div className="bg-panel border border-subtle rounded-md p-5 flex flex-col justify-between">
          <div className="border-b border-subtle pb-3 flex items-center justify-between">
            <div>
              <h4 className="font-heading font-bold text-sm text-white">
                FAILURE CLASSIFICATION &amp; PFMEA TAXONOMY
              </h4>
              <p className="text-xs text-secondary mt-0.5">
                Automated 8D classification linked to standard quality catalog.
              </p>
            </div>
            <span className="font-mono text-xs text-caution font-bold px-2 py-0.5 rounded bg-caution-bg border border-caution-border">
              RPN: 280 / 1000
            </span>
          </div>

          <div className="my-3 space-y-2 text-xs font-mono">
            <div className="flex justify-between py-1.5 border-b border-subtle/40">
              <span className="text-secondary">Failure Mode Code:</span>
              <span className="text-white font-bold">FM-WAF-001 (Thermal Spindle Dynamic Warp)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-subtle/40">
              <span className="text-secondary">Severity (S):</span>
              <span className="text-critical font-bold">8 / 10 (Line stoppage, customer order delay)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-subtle/40">
              <span className="text-secondary">Occurrence (O):</span>
              <span className="text-caution font-bold">5 / 10 (Isolated to rushed shift handover &amp; Tier-3 lot)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-subtle/40">
              <span className="text-secondary">Detection (D):</span>
              <span className="text-white font-bold">7 / 10 (Detected at CMM Gate before shipping)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-subtle/40">
              <span className="text-secondary">Recurrence Risk:</span>
              <span className="text-critical font-bold">EXTREME (Without dynamic recalibration)</span>
            </div>
          </div>

          <div className="pt-2 border-t border-subtle flex justify-end">
            <button
              onClick={() => navigate('/report')}
              className="text-xs text-cobalt font-mono font-bold hover:underline flex items-center gap-1"
            >
              <span>View Full 8D Report (D1-D8)</span>
              <ChevronRight className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>

      {/* ── Provenance Drawer ────────────────────────────────────────────────── */}
      <ProvenanceDrawer nodeData={selectedNode} onClose={() => setSelectedNode(null)} />
    </div>
  );
}
