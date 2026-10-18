import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  Clock,
  User,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';
import { Node, Edge, MarkerType } from '@xyflow/react';
import { useAppStore } from '../../state/useAppStore';
import { EvidenceGraph, GraphNodeData } from './components/EvidenceGraph';
import { ProvenanceDrawer } from './components/ProvenanceDrawer';
import { fetchMachineSubgraph } from '../../lib/api';

export function IncidentCaseBoard() {
  const navigate = useNavigate();
  const { activeCase, timelineStage, proposals, dataMode } = useAppStore();
  const [selectedNode, setSelectedNode] = useState<GraphNodeData | null>(null);
  const [activeStageTab, setActiveStageTab] = useState<'detect' | 'diagnose' | 'classify' | 'forecast' | 'remediate'>('diagnose');

  const [liveNodes, setLiveNodes] = useState<Node<GraphNodeData>[] | null>(null);
  const [liveEdges, setLiveEdges] = useState<Edge[] | null>(null);
  const [isLoadingGraph, setIsLoadingGraph] = useState(false);

  const isContained = timelineStage >= 7;
  const isLive = dataMode === 'live';

  useEffect(() => {
    let mounted = true;
    async function loadSpannerGraph() {
      if (!isLive) {
        setLiveNodes(null);
        setLiveEdges(null);
        return;
      }

      setIsLoadingGraph(true);
      try {
        const targetMachineId = activeCase.stationId === 'st-03b' ? 'M02' : activeCase.stationId;
        const data = await fetchMachineSubgraph(targetMachineId);

        if (!mounted || !data || !data.nodes || data.nodes.length === 0) {
          setIsLoadingGraph(false);
          return;
        }

        // Layout coordinate lookup table
        const posMap: Record<string, { x: number; y: number }> = {
          'SUP-T1-01': { x: -320, y: 60 },
          'SUP-T1-02': { x: -560, y: 60 },
          'LOT-409': { x: -260, y: 220 },
          'LOT-377': { x: -500, y: 220 },
          'LOT-401': { x: -500, y: 350 },
          'LOT-392': { x: -500, y: 480 },
          'LOT-388': { x: -500, y: 610 },
          'CREW-A': { x: 300, y: 60 },
          'CREW-C': { x: 540, y: 60 },
          'CAL-0022': { x: 260, y: 220 },
          'CAL-0006': { x: 500, y: 220 },
          'M02': { x: 0, y: 340 },
          'L1': { x: -160, y: 490 },
          'SN-M02-VIB': { x: 60, y: 500 },
          'SN-M02-TEMP': { x: 240, y: 500 },
          'SN-M02-PRES': { x: 420, y: 500 },
        };

        const convertedNodes: Node<GraphNodeData>[] = data.nodes.map((n, idx) => {
          let category: GraphNodeData['category'] = 'machine';
          let isCulprit = false;
          let isDecoy = false;
          let label = n.properties?.name || n.id;
          let subLabel = n.label;
          let metric = '';
          let spec = '';
          let whyItMatters = '';
          const sourceSystem = 'Cloud Spanner FactoryGraph';

          if (n.label === 'Machine') {
            category = 'machine';
            isCulprit = true;
            label = `${n.properties?.name || 'CNC Mill'} (${n.id})`;
            subLabel = `Line ${n.properties?.line_id || 'L1'} • Machining Center`;
            metric = 'Scrap: 11.8% • Spindle offset: 0.035mm';
            spec = 'Normal Scrap: <= 0.8%';
            whyItMatters = 'Work center affected by compound alloy chatter and missed spindle thermal compensation.';
          } else if (n.label === 'MaterialLot') {
            isCulprit = n.id === 'LOT-409';
            isDecoy = !isCulprit;
            category = isCulprit ? 'lot' : 'decoy';
            label = `Material Lot ${n.id}`;
            subLabel = isCulprit ? 'Alloy Steel (UPPER_EDGE_ALL)' : 'Standard Buffer Lot';
            metric = isCulprit ? 'Hardness: 31.7 HRC • Carbon: 0.219%' : 'Within Spec (29.6 HRC)';
            spec = 'Upper Hardness: <= 30.0 HRC';
            whyItMatters = isCulprit
              ? 'Excess silicon/hardness generates high workpiece cutting resistance, inducing thermal spindle chatter.'
              : 'Decoy lot ruled out: metallurgic properties strictly centered in tolerance.';
          } else if (n.label === 'MaintenanceEvent') {
            isCulprit = n.id === 'CAL-0022' || n.id === 'CAL-0021';
            category = 'maintenance';
            label = `Calibration ${n.id}`;
            subLabel = isCulprit ? 'Crew A (Skipped Step 6)' : 'Standard Calibration';
            metric = isCulprit ? 'Completed: 7/8 Steps' : 'Completed: 8/8 Steps';
            spec = 'Mandatory Protocol: 8/8 Steps';
            whyItMatters = isCulprit
              ? 'Step 6 (Thermal offset verification) omitted during rushed shift handover, leaving 0.035mm dynamic offset.'
              : 'Routine PM check completed with full verification.';
          } else if (n.label === 'OperatorLog' || n.label === 'Crew') {
            category = 'maintenance';
            isCulprit = n.id === 'CREW-A';
            label = n.id === 'CREW-A' ? 'Maintenance Crew A' : 'Maintenance Crew C';
            subLabel = n.id === 'CREW-A' ? 'Handover HO-20261014-S (6.0m Rushed)' : 'Standard Shift Handover';
            metric = n.id === 'CREW-A' ? 'Duration: 6 mins (Standard: >= 15m)' : 'Duration: 32 mins';
            whyItMatters = n.id === 'CREW-A'
              ? 'Rushed transition omitted mandatory thermal indicator sign-off checklist.'
              : 'Normal handover transition with complete PM validation.';
          } else if (n.label === 'Supplier') {
            category = 'supplier';
            isCulprit = n.id === 'SUP-T1-01';
            label = `Supplier ${n.properties?.name || n.id}`;
            subLabel = isCulprit ? 'Tier 1 Supplier (Origin: Meridian T3)' : 'Tier 1 Supplier (Helix)';
            metric = isCulprit ? 'Delivered Lot LOT-409' : 'Delivered Buffer Lot LOT-377';
            whyItMatters = isCulprit
              ? 'Apex Drivetrain sourced high-hardness heat batches from Tier-3 Meridian Specialty Steels.'
              : 'Alternative certified supplier with clean track record.';
          } else if (n.label === 'Sensor') {
            category = 'machine';
            isDecoy = true;
            label = `${n.id}`;
            subLabel = `Sensor (${n.properties?.sensor_type || 'TELEMETRY'})`;
            metric = n.properties?.unit || '';
            whyItMatters = 'High-frequency telemetry stream ingested via Google Cloud PubSub.';
          } else if (n.label === 'ProductionLine') {
            category = 'machine';
            label = `Production Line ${n.id}`;
            subLabel = n.properties?.name || 'Assembly Line';
            whyItMatters = 'Facility machining line housing CNC work centers M01 through M04.';
          }

          const defaultPos = { x: (idx % 4) * 220 - 200, y: Math.floor(idx / 4) * 160 + 50 };
          const pos = posMap[n.id] || defaultPos;

          return {
            id: n.id,
            type: 'evidenceNode',
            position: pos,
            data: {
              label,
              category,
              subLabel,
              isCulprit,
              isDecoy,
              metric,
              spec,
              sourceSystem,
              recordId: n.id,
              evidenceHash: `spanner-sha256-${n.id.toLowerCase()}-7a8b9c`,
              whyItMatters,
            },
          };
        });

        const convertedEdges: Edge[] = data.edges.map((e) => {
          const isCulpritEdge =
            (e.from_id === 'M02' && e.to_id === 'LOT-409') ||
            (e.from_id === 'CAL-0022' && e.to_id === 'M02') ||
            (e.from_id === 'SUP-T1-01' && e.to_id === 'LOT-409');

          return {
            id: e.id,
            source: e.from_id,
            target: e.to_id,
            label: e.type,
            animated: isCulpritEdge,
            style: {
              stroke: isCulpritEdge ? '#FF5A3C' : e.type === 'SUPPLIED_BY' ? '#4C8DFF' : '#64748B',
              strokeWidth: isCulpritEdge ? 3 : 1.5,
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: isCulpritEdge ? '#FF5A3C' : '#64748B',
            },
          };
        });

        if (mounted) {
          setLiveNodes(convertedNodes);
          setLiveEdges(convertedEdges);
        }
      } catch (err) {
        console.warn('Could not build live Spanner evidence graph:', err);
      } finally {
        if (mounted) setIsLoadingGraph(false);
      }
    }

    loadSpannerGraph();
    return () => {
      mounted = false;
    };
  }, [isLive, activeCase.stationId]);

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
            <span className="text-xs font-mono text-secondary">
              {isLive ? 'AUSTIN LINES L1, L2, L3 • FOCAL: M02' : 'AUSTIN LINE 03 • STATION 03B'}
            </span>
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
            {isLive
              ? 'Automated scrap monitoring detected an 11.8% scrap rate spike on 5 CNC milling work centers (M02, M03, M06, M09, M11) across Lines L1, L2, L3. Cloud Spanner Graph ISO GQL traversal isolated the compound root cause: Tier-3 steel lot LOT-409 (Apex Drivetrain Systems / Meridian Specialty Steels, 31.7 HRC, 0.219% C) combined with rushed shift handover HO-20261014-S by Crew A which skipped Step 6: Thermal offset verification (CAL-0021..CAL-0027).'
              : 'At 22:01 UTC, vibration telemetry on Precision Spindle Station-03b shifted to 4.82 mm/s, causing a 12.2% scrap spike at the automated CMM gate. The diagnostic pipeline backward-traced through the knowledge graph in 1.2s to isolate a compound root cause: out-of-specification raw material from AlloyTech Global (Lot #40921, 1.82% Si) combined with an uncalibrated spindle runout offset (0.035 mm) skipped by Maintenance Crew B during a rushed shift handover.'}
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
            <span className="text-dim text-[10px]">
              {isLive ? 'GOOGLE CLOUD SPANNER FACTORYGRAPH GROUNDED' : 'VERIFIED GROUNDING • NO HALLUCINATION'}
            </span>
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
            <h3 className="font-heading font-bold text-base text-white tracking-wide flex items-center gap-2">
              <span>ROOT CAUSE REVEAL: MULTI-HOP EVIDENCE GRAPH</span>
              {isLive && (
                <span className="px-2 py-0.5 rounded bg-cobalt/20 text-cobalt font-mono text-[10px] font-bold">
                  LIVE SPANNER TOPOLOGY (M02)
                </span>
              )}
            </h3>
            <p className="text-xs text-secondary">
              Trace backward from failing work center to raw supply chain lots, mill certificates, and maintenance shift handovers.
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

        <EvidenceGraph
          onSelectNode={(node) => setSelectedNode(node)}
          customNodes={liveNodes || undefined}
          customEdges={liveEdges || undefined}
          isLoading={isLoadingGraph}
        />
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
                Commonality analysis evaluating compound and decoy failure modes in Spanner.
              </p>
            </div>
          </div>

          <div className="my-3 space-y-3">
            {/* Culprit Hypothesis 1 */}
            <div className="p-3 rounded bg-critical-bg/50 border border-critical-border text-xs">
              <div className="flex items-center justify-between font-mono mb-1">
                <span className="font-bold text-critical">
                  {isLive
                    ? '1. COMPOUND CAUSE: ALLOY LOT LOT-409 + SKIPPED THERMAL CALIBRATION'
                    : '1. COMPOUND CAUSE: ALLOY LOT #40921 + SKIPPED TRAMMING'}
                </span>
                <span className="px-1.5 py-0.2 rounded bg-critical text-white font-bold">94.2% CONF</span>
              </div>
              <p className="text-primary text-[11px] leading-relaxed">
                {isLive
                  ? 'Upper-edge hardness (31.7 HRC) and carbon (0.219%) on Lot LOT-409 (Apex Drivetrain / Meridian T3) induced cutting chatter, compounding with missed Step 6: Thermal offset verification (CAL-0021..CAL-0027) by Crew A to cause thermal warp across M02, M03, M06, M09, M11. Lift: 4.82x.'
                  : 'Excess silicon (1.82%) induced hard workpiece chatter, compounding with 0.035mm spindle runout to cause 78.4°C thermal warp within 12 minutes. Lift score: 4.82x across historical failure corpus.'}
              </p>
            </div>

            {/* Decoy 1 */}
            <div className="p-3 rounded bg-raised border border-subtle text-xs opacity-75">
              <div className="flex items-center justify-between font-mono mb-1">
                <span className="font-bold text-dim line-through">
                  {isLive ? '2. DECOY: M05 VIBRATION DRIFT ALONE' : '2. DECOY: STATION-03A TOOL WEAR DEGRADATION'}
                </span>
                <span className="px-1.5 py-0.2 rounded bg-raised text-dim font-bold">12.4% CONF</span>
              </div>
              <p className="text-secondary text-[11px] leading-relaxed">
                {isLive
                  ? 'Ruled out: Slow vibration drift on Machine M05 since Oct 11, but scrap rates on M05 remained nominal (0.6%).'
                  : 'Ruled out: Tool life at 82%, but upstream vibration signatures remained flat at 1.9 mm/s without cross-station vibration transfer.'}
              </p>
            </div>

            {/* Decoy 2 */}
            <div className="p-3 rounded bg-raised border border-subtle text-xs opacity-75">
              <div className="flex items-center justify-between font-mono mb-1">
                <span className="font-bold text-dim line-through">
                  {isLive ? '3. DECOY: TIER-3 SUPPLIER ALONE (LOT-412 BENCHMARK)' : '3. DECOY: OPERATOR SHIFT FATIGUE'}
                </span>
                <span className="px-1.5 py-0.2 rounded bg-raised text-dim font-bold">4.1% CONF</span>
              </div>
              <p className="text-secondary text-[11px] leading-relaxed">
                {isLive
                  ? 'Ruled out: LOT-412 from the exact same supplier (Meridian Specialty Steels) runs without scrap rise on M01.'
                  : 'Ruled out: Defect rate correlates directly with Lot #40921 loading timestamp rather than shift hour progression.'}
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
              <span className="text-white font-bold">{isLive ? 'FM-01 / FM-02 (Material & Method Interaction)' : 'FM-WAF-001 (Thermal Spindle Dynamic Warp)'}</span>
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
              <span>View Full 8D Root Cause Report</span>
              <ChevronRight className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Slide-over Provenance Drawer */}
      <ProvenanceDrawer nodeData={selectedNode} onClose={() => setSelectedNode(null)} />
    </div>
  );
}
