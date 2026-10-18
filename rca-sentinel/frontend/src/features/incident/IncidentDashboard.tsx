import { useState } from 'react';
import {
  AlertTriangle,
  Search,
  FileText,
  Clock,
  Printer,
  X,
  ChevronRight,
} from 'lucide-react';
import { useAppStore } from '../../state/useAppStore';
import { IncidentCaseBoard } from './IncidentCaseBoard';
import { ReportScreen } from '../report/ReportScreen';

export interface IncidentRecord {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  status: 'active' | 'contained' | 'decoy_ruled_out' | 'resolved' | 'verified_buffer';
  category: 'scrap_spike' | 'telemetry_drift' | 'sensor_fault' | 'material_gate';
  targetAssets: string;
  lines: string;
  detectedTime: string;
  detectionSource: string;
  metric: string;
  spec: string;
  rootCauseSummary: string;
  remediationSummary: string;
  financialImpact: string;
  aiConfidence: string;
}

const INCIDENTS_REGISTRY: IncidentRecord[] = [
  {
    id: 'INC-20261015-01',
    title: 'Scrap Rate Spike (11.8%) across CNC Milling Centers',
    severity: 'critical',
    status: 'active',
    category: 'scrap_spike',
    targetAssets: 'M02, M03, M06, M09, M11',
    lines: 'Lines L1, L2, L3 • Spindle Centers',
    detectedTime: '14 mins ago',
    detectionSource: 'Automated CMM Quality Gate',
    metric: 'Scrap: 11.8% • Spindle offset: 0.035mm',
    spec: 'Scrap Tolerance <= 0.8% • Spindle runout <= 0.010mm',
    rootCauseSummary:
      'Compound Failure: Upper-edge hardness on Lot LOT-409 (31.7 HRC) + Maintenance Crew A rushed handover omitting Step 6 spindle thermal offset verification (CAL-0021..CAL-0027).',
    remediationSummary:
      'Three-Fold Actuation: Emergency PLC feed-hold on 5 centers, ERP quarantine of LOT-409 with reroute to LOT-377, CMMS work order MO-0028 dispatched to Crew B.',
    financialImpact: '$128,400 scrap avoided',
    aiConfidence: '94.2%',
  },
  {
    id: 'INC-20261011-04',
    title: 'Machine M05 Spindle Vibration Baseline Drift',
    severity: 'low',
    status: 'decoy_ruled_out',
    category: 'telemetry_drift',
    targetAssets: 'M05',
    lines: 'Line L2 • Finish Mill Center',
    detectedTime: '4 days ago',
    detectionSource: 'High-Frequency Accelerometer (SN-M05-VIB)',
    metric: 'Vibration: 2.1 mm/s • Scrap: 0.6%',
    spec: 'Vibration Threshold <= 2.5 mm/s • Scrap <= 0.8%',
    rootCauseSummary:
      'Monitored Failure Decoy: Vibration slowly trended upward over 72 hours, but scrap rates remained nominal (0.6%) and zero cross-station transfer occurred. Ruled out as root cause via Spanner commonality traversal.',
    remediationSummary:
      'Scheduled preventive lubrication inspection during standard weekend shift. No emergency actuation required.',
    financialImpact: '$0 (Nominal baseline)',
    aiConfidence: '88.6%',
  },
  {
    id: 'INC-20261008-02',
    title: 'Pneumatic Pressure Sensor Telemetry Glitch on M12',
    severity: 'medium',
    status: 'resolved',
    category: 'sensor_fault',
    targetAssets: 'M12',
    lines: 'Line L3 • High-Speed Milling Center',
    detectedTime: '7 days ago',
    detectionSource: 'Pneumatic Transducer (SN-M12-PRES)',
    metric: 'Pressure drop: -0.2 bar intermittent',
    spec: 'Pneumatic Feed: 6.0 ± 0.3 bar',
    rootCauseSummary:
      'Hardware Sensor Glitch: Unseated optical transceiver cable produced intermittent telemetry drops. Physical tool clamping pressure remained mechanically verified at 6.1 bar.',
    remediationSummary:
      'Re-seated optical connector and replaced transceiver. Telemetry verified normal with zero workpieces scrapped.',
    financialImpact: '$4,200 sensor replacement',
    aiConfidence: '96.1%',
  },
  {
    id: 'INC-20260928-01',
    title: 'Raw Infeed Alloy Steel Lot LOT-377 Hardness Certification',
    severity: 'info',
    status: 'verified_buffer',
    category: 'material_gate',
    targetAssets: 'LOT-377 (Helix Powertrain)',
    lines: 'Inbound Receiving Dock 4 • Buffer Stock',
    detectedTime: '17 days ago',
    detectionSource: 'Inbound Receiving Metallurgy Lab',
    metric: 'Hardness: 29.6 HRC • Carbon: 0.185%',
    spec: 'Hardness Range: 28.0 - 30.0 HRC',
    rootCauseSummary:
      'Quality Gate Validation: Inbound metallurgic batch test verified optimal centered hardness and carbon density. Certified as active primary clean buffer lot for production line emergency cutover.',
    remediationSummary:
      'Designated active buffer inventory in ERP. Immediate standby infeed ready for routing upon LOT-409 quarantine.',
    financialImpact: '$84,000 buffer equity protected',
    aiConfidence: '99.4%',
  },
];

export function IncidentDashboard() {
  const { timelineStage, dataMode, isSpannerConnected } = useAppStore();
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [reportModalIncidentId, setReportModalIncidentId] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<'all' | 'critical' | 'decoy' | 'resolved'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const isContained = timelineStage >= 7;

  // Filtered list
  const filteredIncidents = INCIDENTS_REGISTRY.map((inc) => {
    // Dynamic status for active incident when approved
    if (inc.id === 'INC-20261015-01' && isContained) {
      return { ...inc, status: 'contained' as const };
    }
    return inc;
  }).filter((inc) => {
    // Status filter
    if (filterStatus === 'critical' && inc.severity !== 'critical') return false;
    if (filterStatus === 'decoy' && inc.status !== 'decoy_ruled_out') return false;
    if (filterStatus === 'resolved' && inc.status !== 'resolved' && inc.status !== 'verified_buffer') return false;

    // Search query filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        inc.id.toLowerCase().includes(q) ||
        inc.title.toLowerCase().includes(q) ||
        inc.targetAssets.toLowerCase().includes(q) ||
        inc.lines.toLowerCase().includes(q) ||
        inc.rootCauseSummary.toLowerCase().includes(q)
      );
    }
    return true;
  });

  // If an incident is drilled down, render the detailed IncidentCaseBoard
  if (selectedIncidentId) {
    return (
      <div className="space-y-4">
        {/* Back navigation header */}
        <div className="bg-panel border border-subtle rounded-md px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSelectedIncidentId(null)}
              className="px-3 py-1.5 rounded bg-raised border border-subtle text-primary font-mono text-xs hover:border-strong hover:bg-raised/80 transition-colors flex items-center gap-2"
            >
              <span>&larr; Back to Incidents Fleet</span>
            </button>
            <span className="text-dim">|</span>
            <span className="font-mono text-xs text-secondary">
              Viewing Deep-Dive Case: <strong className="text-primary">{selectedIncidentId}</strong>
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setReportModalIncidentId(selectedIncidentId)}
              className="px-3 py-1.5 rounded bg-cobalt-bg text-cobalt border border-cobalt-border font-mono text-xs font-bold hover:bg-cobalt/20 transition-colors flex items-center gap-1.5"
            >
              <Printer className="h-3.5 w-3.5" />
              <span>Print / View 8D Report</span>
            </button>
          </div>
        </div>

        {/* Detailed Case Board */}
        <IncidentCaseBoard onBack={() => setSelectedIncidentId(null)} onOpenReport={() => setReportModalIncidentId(selectedIncidentId)} />

        {/* 8D Report Modal */}
        {reportModalIncidentId && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
            <div className="bg-panel border border-strong rounded-lg max-w-5xl w-full max-h-[90vh] overflow-y-auto p-6 relative shadow-2xl">
              <button
                onClick={() => setReportModalIncidentId(null)}
                className="absolute top-4 right-4 p-2 rounded text-secondary hover:text-primary hover:bg-raised transition-colors z-20"
                title="Close Report"
              >
                <X className="h-5 w-5" />
              </button>
              <ReportScreen onBack={() => setReportModalIncidentId(null)} />
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Dashboard Header ─────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 bg-panel border border-subtle rounded-md">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-cobalt uppercase font-bold tracking-wider">
              FLEET ANOMALY &amp; INCIDENT MANAGEMENT
            </span>
            <span className="text-dim">&bull;</span>
            <span className="font-mono text-xs text-dim uppercase">
              {dataMode === 'live' ? (isSpannerConnected ? 'GOOGLE CLOUD SPANNER GRAPH CONNECTED' : 'SPANNER GRAPH SYNCING') : 'OPERATIONAL STANDBY'}
            </span>
          </div>
          <h2 className="font-heading font-bold text-2xl text-primary mt-1 flex items-center gap-2">
            <AlertTriangle className="h-6 w-6 text-critical" />
            Manufacturing Incidents Dashboard
          </h2>
          <p className="text-xs text-secondary mt-1 max-w-2xl font-sans">
            Centralized monitoring of anomalies raised across shop-floor milling centers, shift handovers, and supplier material lots. Select an incident card below to drill down into the knowledge graph traversal, root cause isolation, and three-fold remediation flow.
          </p>
        </div>

        {/* Aggregate KPI Badges */}
        <div className="flex flex-wrap items-center gap-3 font-mono text-xs">
          <div className="p-3 rounded bg-raised border border-subtle text-left">
            <span className="text-dim text-[10px] uppercase block">ACTIVE INCIDENTS</span>
            <span className="font-bold text-base text-critical">1 High Impact</span>
          </div>
          <div className="p-3 rounded bg-raised border border-subtle text-left">
            <span className="text-dim text-[10px] uppercase block">TOTAL INVESTIGATED</span>
            <span className="font-bold text-base text-primary">4 Cases</span>
          </div>
          <div className="p-3 rounded bg-raised border border-subtle text-left">
            <span className="text-dim text-[10px] uppercase block">NET SCRAP PROTECTED</span>
            <span className="font-bold text-base text-healthy">$128,400</span>
          </div>
        </div>
      </div>

      {/* ── Search and Filter Controls Bar ──────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Filter Pills */}
        <div className="flex items-center gap-2 bg-panel border border-subtle p-1 rounded-md">
          <button
            onClick={() => setFilterStatus('all')}
            className={`px-3 py-1.5 rounded text-xs font-mono transition-colors ${
              filterStatus === 'all' ? 'bg-raised text-primary font-bold' : 'text-secondary hover:text-primary'
            }`}
          >
            All Incidents (4)
          </button>
          <button
            onClick={() => setFilterStatus('critical')}
            className={`px-3 py-1.5 rounded text-xs font-mono transition-colors ${
              filterStatus === 'critical' ? 'bg-critical text-white font-bold' : 'text-secondary hover:text-primary'
            }`}
          >
            Active Critical (1)
          </button>
          <button
            onClick={() => setFilterStatus('decoy')}
            className={`px-3 py-1.5 rounded text-xs font-mono transition-colors ${
              filterStatus === 'decoy' ? 'bg-raised text-primary font-bold' : 'text-secondary hover:text-primary'
            }`}
          >
            Monitored Decoys (1)
          </button>
          <button
            onClick={() => setFilterStatus('resolved')}
            className={`px-3 py-1.5 rounded text-xs font-mono transition-colors ${
              filterStatus === 'resolved' ? 'bg-healthy-bg text-healthy font-bold' : 'text-secondary hover:text-primary'
            }`}
          >
            Resolved &amp; Buffer (2)
          </button>
        </div>

        {/* Search Bar */}
        <div className="flex items-center gap-2 bg-panel border border-subtle px-3 py-1.5 rounded-md min-w-[280px]">
          <Search className="h-4 w-4 text-dim shrink-0" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by Machine (M02), Lot (LOT-409), Line (L1)..."
            className="w-full bg-transparent text-xs text-primary placeholder-dim outline-none font-mono"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery('')} className="text-dim hover:text-primary text-xs">
              &times;
            </button>
          )}
        </div>
      </div>

      {/* ── Incident Cards Grid ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {filteredIncidents.map((incident) => {
          const isCritical = incident.severity === 'critical';
          const isDecoy = incident.status === 'decoy_ruled_out';
          const isBuffer = incident.status === 'verified_buffer';

          return (
            <div
              key={incident.id}
              className={`p-6 rounded-md border flex flex-col justify-between transition-all duration-150 ${
                isCritical
                  ? isContained
                    ? 'bg-healthy-bg/15 border-healthy hover:border-healthy'
                    : 'bg-critical-bg/20 border-critical hover:border-red-400 shadow-lg'
                  : isDecoy
                  ? 'bg-panel border-subtle hover:border-strong opacity-85'
                  : 'bg-panel border-subtle hover:border-strong'
              }`}
            >
              <div>
                {/* Card Top Strip */}
                <div className="flex items-start justify-between gap-3 border-b border-subtle/70 pb-3 mb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-primary tracking-wider">
                        {incident.id}
                      </span>
                      <span className="text-dim">&bull;</span>
                      <span className="font-mono text-[11px] text-secondary flex items-center gap-1">
                        <Clock className="h-3 w-3 text-dim" />
                        {incident.detectedTime}
                      </span>
                    </div>
                    <h3 className="font-heading font-bold text-lg text-primary mt-1 leading-snug">
                      {incident.title}
                    </h3>
                  </div>

                  {/* Status Badge */}
                  <div>
                    {isCritical && !isContained && (
                      <span className="px-2.5 py-1 rounded text-[10px] font-mono font-bold bg-critical text-white uppercase animate-pulse">
                        ACTIVE CRITICAL
                      </span>
                    )}
                    {isContained && isCritical && (
                      <span className="px-2.5 py-1 rounded text-[10px] font-mono font-bold bg-healthy text-black uppercase">
                        CONTAINED
                      </span>
                    )}
                    {isDecoy && (
                      <span className="px-2.5 py-1 rounded text-[10px] font-mono font-bold bg-raised text-secondary border border-subtle uppercase">
                        RULED OUT DECOY
                      </span>
                    )}
                    {incident.status === 'resolved' && (
                      <span className="px-2.5 py-1 rounded text-[10px] font-mono font-bold bg-healthy-bg text-healthy border border-healthy-border uppercase">
                        RESOLVED
                      </span>
                    )}
                    {isBuffer && (
                      <span className="px-2.5 py-1 rounded text-[10px] font-mono font-bold bg-cobalt-bg text-cobalt border border-cobalt-border uppercase">
                        VERIFIED BUFFER
                      </span>
                    )}
                  </div>
                </div>

                {/* Scope & Asset Tags */}
                <div className="grid grid-cols-2 gap-3 py-2 text-xs font-mono bg-canvas/40 p-2.5 rounded border border-subtle/50 mb-3">
                  <div>
                    <span className="text-dim text-[10px] uppercase block">TARGET MACHINES / LOTS:</span>
                    <span className="text-primary font-bold">{incident.targetAssets}</span>
                  </div>
                  <div>
                    <span className="text-dim text-[10px] uppercase block">FACILITY LOCATION:</span>
                    <span className="text-secondary">{incident.lines}</span>
                  </div>
                  <div>
                    <span className="text-dim text-[10px] uppercase block">CURRENT METRIC:</span>
                    <span className={isCritical ? 'text-critical font-bold' : 'text-primary'}>
                      {incident.metric}
                    </span>
                  </div>
                  <div>
                    <span className="text-dim text-[10px] uppercase block">INSPECTION GATE:</span>
                    <span className="text-secondary truncate block">{incident.detectionSource}</span>
                  </div>
                </div>

                {/* Root Cause & Remediation Summary */}
                <div className="space-y-2 text-xs font-sans">
                  <div>
                    <span className="font-mono text-[10px] text-dim uppercase block">
                      KNOWLEDGE GRAPH ROOT CAUSE ISOLATION:
                    </span>
                    <p className="text-secondary text-[12px] leading-relaxed mt-0.5">
                      {incident.rootCauseSummary}
                    </p>
                  </div>

                  <div>
                    <span className="font-mono text-[10px] text-dim uppercase block">
                      REMEDIATION &amp; CONTAINMENT:
                    </span>
                    <p className="text-secondary text-[12px] leading-relaxed mt-0.5">
                      {incident.remediationSummary}
                    </p>
                  </div>
                </div>
              </div>

              {/* Bottom Card Footer Actions */}
              <div className="mt-5 pt-3 border-t border-subtle/60 flex flex-wrap items-center justify-between gap-3">
                <div className="font-mono text-xs">
                  <span className="text-dim text-[10px] block uppercase">FINANCIAL EXPOSURE:</span>
                  <span className="text-healthy font-bold">{incident.financialImpact}</span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setReportModalIncidentId(incident.id)}
                    className="px-3 py-1.5 rounded bg-raised border border-subtle text-secondary hover:text-primary font-mono text-xs transition-colors flex items-center gap-1.5"
                    title="View & Print 8D Report"
                  >
                    <FileText className="h-3.5 w-3.5" />
                    <span>8D Report</span>
                  </button>

                  <button
                    onClick={() => setSelectedIncidentId(incident.id)}
                    className={`px-4 py-1.5 rounded font-mono text-xs font-bold transition-colors flex items-center gap-1.5 ${
                      isCritical
                        ? 'bg-active text-white hover:bg-blue-600 shadow-md'
                        : 'bg-raised text-primary hover:bg-raised/80 border border-subtle'
                    }`}
                  >
                    <span>Drill Down &amp; Case Board</span>
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── 8D Report Modal (Accessible from any Card) ───────────────────────── */}
      {reportModalIncidentId && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-panel border border-strong rounded-lg max-w-5xl w-full max-h-[90vh] overflow-y-auto p-6 relative shadow-2xl">
            <button
              onClick={() => setReportModalIncidentId(null)}
              className="absolute top-4 right-4 p-2 rounded text-secondary hover:text-primary hover:bg-raised transition-colors z-20"
              title="Close Report"
            >
              <X className="h-5 w-5" />
            </button>
            <ReportScreen onBack={() => setReportModalIncidentId(null)} />
          </div>
        </div>
      )}
    </div>
  );
}
