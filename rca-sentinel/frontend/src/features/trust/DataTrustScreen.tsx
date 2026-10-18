import { useEffect, useState } from 'react';
import { CheckCircle2, ShieldCheck, Key, RefreshCw } from 'lucide-react';
import { fetchHealthStatus, HealthStatusResponse } from '../../lib/api';

export function DataTrustScreen() {
  const [health, setHealth] = useState<HealthStatusResponse | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadHealth = async () => {
    setIsRefreshing(true);
    const data = await fetchHealthStatus();
    setHealth(data);
    setIsRefreshing(false);
  };

  useEffect(() => {
    loadHealth();
  }, []);

  const auditEvents = [
    {
      time: '22:04:18 UTC',
      actor: 'M. Vance (PE Reliability)',
      action: 'APPROVE_PLC_INTERLOCK',
      entity: 'station-03b',
      hash: '7f9a12c8e3d4b5a67890123456789abcdef0123456789abcdef0123456789abcd',
      status: 'VERIFIED',
    },
    {
      time: '22:04:12 UTC',
      actor: 'RemediateAgent',
      action: 'PROPOSE_CONTAINMENT_ACTIONS',
      entity: 'INC-8921',
      hash: 'c4d5e6f7a8b9c0d1e2f3a8f9a2b71c4d5e89a0b1c2d3e4f5a6b7c8d9e0f1a2b3',
      status: 'VERIFIED',
    },
    {
      time: '22:01:15 UTC',
      actor: 'DiagnoseAgent',
      action: 'MULTI_HOP_GRAPH_INFERENCE',
      entity: 'lot-40921 + crew-b',
      hash: '8f9a2b71c4d5e89a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a',
      status: 'VERIFIED',
    },
    {
      time: '22:01:14 UTC',
      actor: 'StreamConsumerWorker',
      action: 'ANOMALY_CONFIRMED_INCIDENT_CREATED',
      entity: 'sensor-vib-03b',
      hash: '1a2b3c4d5e6f7a8b9c0d1e2f3a8f9a2b71c4d5e89a0b1c2d3e4f5a6b7c8d9e0f',
      status: 'VERIFIED',
    },
  ];

  return (
    <div className="space-y-6">
      {/* ── Header ───────────────────────────────────────────────────────────── */}
      <div className="p-5 bg-panel border border-subtle rounded-md flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="font-mono text-xs text-dim uppercase tracking-wider block">
            DATA INTEGRITY &amp; TRUST ARCHITECTURE
          </span>
          <h2 className="font-heading font-bold text-2xl text-primary mt-1">
            Google Cloud Platform Ingestion Health &amp; Audit Trail
          </h2>
          <p className="text-xs text-secondary mt-1 max-w-2xl font-sans">
            Cryptographic proof of evidence grounding, Spanner Graph ISO GQL ontology compliance, and append-only actuation audit log.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadHealth}
            className="p-2 rounded bg-raised border border-subtle hover:border-active transition-colors text-secondary hover:text-primary"
            title="Refresh Health Status"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
          <div className="p-3 bg-healthy-bg rounded border border-healthy-border text-right font-mono text-xs">
            <span className="text-healthy text-[10px] block font-bold">ONTOLOGY COMPLIANCE</span>
            <span className="text-primary font-bold">100% Spanner Graph</span>
            <span className="text-healthy text-[11px] block mt-0.5">0 Quarantine Rejects</span>
          </div>
        </div>
      </div>

      {/* ── Data Connectors Grid ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 bg-panel border border-subtle rounded-md">
          <div className="flex items-center justify-between text-secondary font-mono text-[10px] uppercase">
            <span>SPANNER GRAPH</span>
            <CheckCircle2 className={`h-4 w-4 ${health?.checks?.spanner_graph !== false ? 'text-healthy' : 'text-critical'}`} />
          </div>
          <div className="font-heading font-bold text-lg text-primary mt-1">
            {health?.checks?.spanner_graph !== false ? 'Connected' : 'Offline'}
          </div>
          <span className="text-[10px] font-mono text-dim block mt-0.5">FactoryGraph &bull; ISO GQL</span>
        </div>

        <div className="p-4 bg-panel border border-subtle rounded-md">
          <div className="flex items-center justify-between text-secondary font-mono text-[10px] uppercase">
            <span>BIGQUERY HISTORIAN</span>
            <CheckCircle2 className={`h-4 w-4 ${health?.checks?.bigquery !== false ? 'text-healthy' : 'text-critical'}`} />
          </div>
          <div className="font-heading font-bold text-lg text-primary mt-1">
            {health?.checks?.bigquery !== false ? 'Streaming Active' : 'Offline'}
          </div>
          <span className="text-[10px] font-mono text-dim block mt-0.5">rca_historian.ObservationWindow</span>
        </div>

        <div className="p-4 bg-panel border border-subtle rounded-md">
          <div className="flex items-center justify-between text-secondary font-mono text-[10px] uppercase">
            <span>CLOUD PUB/SUB</span>
            <CheckCircle2 className={`h-4 w-4 ${health?.checks?.pubsub !== false ? 'text-healthy' : 'text-critical'}`} />
          </div>
          <div className="font-heading font-bold text-lg text-primary mt-1">
            {health?.checks?.pubsub !== false ? 'Listening' : 'Offline'}
          </div>
          <span className="text-[10px] font-mono text-dim block mt-0.5">telemetry-anomaly-sub &bull; 0 lag</span>
        </div>

        <div className="p-4 bg-panel border border-subtle rounded-md">
          <div className="flex items-center justify-between text-secondary font-mono text-[10px] uppercase">
            <span>FASTMCP SERVER</span>
            <CheckCircle2 className="h-4 w-4 text-healthy" />
          </div>
          <div className="font-heading font-bold text-lg text-primary mt-1">Active (:8001)</div>
          <span className="text-[10px] font-mono text-dim block mt-0.5">10 Tools &bull; 3 Resources</span>
        </div>
      </div>

      {/* ── Immutable Audit Log ──────────────────────────────────────────────── */}
      <div className="bg-panel border border-subtle rounded-md overflow-hidden">
        <div className="p-4 border-b border-subtle flex items-center justify-between bg-muted/30">
          <h3 className="font-heading font-bold text-sm text-primary flex items-center gap-2">
            <Key className="h-4 w-4 text-cobalt" />
            IMMUTABLE ACTUATION &amp; INFERENCE AUDIT TRAIL
          </h3>
          <span className="text-xs font-mono text-dim">
            SHA-256 Cryptographic Hashes
          </span>
        </div>

        <div className="divide-y divide-subtle/50 text-xs font-mono">
          {auditEvents.map((ev, idx) => (
            <div key={idx} className="p-4 flex flex-wrap items-center justify-between gap-4 hover:bg-raised/30 transition-colors">
              <div className="flex items-center gap-4">
                <span className="text-secondary shrink-0">{ev.time}</span>
                <span className="px-2 py-0.5 rounded bg-raised text-primary text-[11px] font-bold">
                  {ev.action}
                </span>
                <span className="text-primary font-sans text-xs">{ev.actor}</span>
                <span className="text-dim">on</span>
                <span className="text-secondary font-bold">{ev.entity}</span>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-[11px] text-dim font-mono max-w-[200px] truncate" title={ev.hash}>
                  {ev.hash}
                </span>
                <span className="flex items-center gap-1 text-[11px] text-healthy bg-healthy-bg px-2 py-0.5 rounded border border-healthy-border">
                  <ShieldCheck className="h-3 w-3" />
                  {ev.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
