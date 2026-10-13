import { CheckCircle2, ShieldCheck, Key } from 'lucide-react';

export function DataTrustScreen() {
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
          <h2 className="font-heading font-bold text-2xl text-white mt-1">
            Ingestion Health, SHACL Validation &amp; Audit Trail
          </h2>
          <p className="text-xs text-secondary mt-1 max-w-2xl font-sans">
            Cryptographic proof of evidence grounding, declarative RDF/OWL ontology compliance, and append-only actuation audit log.
          </p>
        </div>

        <div className="p-3 bg-healthy-bg rounded border border-healthy-border text-right font-mono text-xs">
          <span className="text-healthy text-[10px] block font-bold">SHACL VALIDATION STATUS</span>
          <span className="text-white font-bold">100% Schema Compliant</span>
          <span className="text-healthy text-[11px] block mt-0.5">0 Quarantine Rejects</span>
        </div>
      </div>

      {/* ── Data Connectors Grid ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 bg-panel border border-subtle rounded-md">
          <div className="flex items-center justify-between text-secondary font-mono text-[10px] uppercase">
            <span>NEO4J AURA KG</span>
            <CheckCircle2 className="h-4 w-4 text-healthy" />
          </div>
          <div className="font-heading font-bold text-lg text-white mt-1">Connected</div>
          <span className="text-[10px] font-mono text-dim block mt-0.5">42,800 nodes &bull; 114,200 rels</span>
        </div>

        <div className="p-4 bg-panel border border-subtle rounded-md">
          <div className="flex items-center justify-between text-secondary font-mono text-[10px] uppercase">
            <span>TIMESCALEDB</span>
            <CheckCircle2 className="h-4 w-4 text-healthy" />
          </div>
          <div className="font-heading font-bold text-lg text-white mt-1">Connected</div>
          <span className="text-[10px] font-mono text-dim block mt-0.5">380k rows/sec ingestion</span>
        </div>

        <div className="p-4 bg-panel border border-subtle rounded-md">
          <div className="flex items-center justify-between text-secondary font-mono text-[10px] uppercase">
            <span>REDIS 7 STREAMS</span>
            <CheckCircle2 className="h-4 w-4 text-healthy" />
          </div>
          <div className="font-heading font-bold text-lg text-white mt-1">Listening</div>
          <span className="text-[10px] font-mono text-dim block mt-0.5">rca:stream:telemetry &bull; 0 lag</span>
        </div>

        <div className="p-4 bg-panel border border-subtle rounded-md">
          <div className="flex items-center justify-between text-secondary font-mono text-[10px] uppercase">
            <span>FASTMCP SERVER</span>
            <CheckCircle2 className="h-4 w-4 text-healthy" />
          </div>
          <div className="font-heading font-bold text-lg text-white mt-1">Active (:8001)</div>
          <span className="text-[10px] font-mono text-dim block mt-0.5">10 Tools &bull; 3 Resources</span>
        </div>
      </div>

      {/* ── Immutable Audit Log ──────────────────────────────────────────────── */}
      <div className="bg-panel border border-subtle rounded-md overflow-hidden">
        <div className="p-4 border-b border-subtle flex items-center justify-between bg-muted/30">
          <h3 className="font-heading font-bold text-sm text-white flex items-center gap-2">
            <Key className="h-4 w-4 text-cobalt" />
            IMMUTABLE ACTUATION &amp; INFERENCE AUDIT TRAIL
          </h3>
          <span className="text-xs font-mono text-dim">
            SHA-256 Cryptographic Hashes
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-subtle bg-muted/20 text-secondary">
                <th className="p-3 font-semibold">TIMESTAMP</th>
                <th className="p-3 font-semibold">ACTOR</th>
                <th className="p-3 font-semibold">ACTION</th>
                <th className="p-3 font-semibold">ENTITY</th>
                <th className="p-3 font-semibold">EVIDENCE SNAPSHOT HASH</th>
                <th className="p-3 font-semibold text-right">AUDIT PROOF</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-subtle/50">
              {auditEvents.map((evt, idx) => (
                <tr key={idx} className="hover:bg-raised/40 transition-colors">
                  <td className="p-3 text-secondary">{evt.time}</td>
                  <td className="p-3 font-bold text-white">{evt.actor}</td>
                  <td className="p-3">
                    <span className="px-1.5 py-0.5 rounded bg-raised text-cobalt font-bold">
                      {evt.action}
                    </span>
                  </td>
                  <td className="p-3 text-secondary">{evt.entity}</td>
                  <td className="p-3 text-dim truncate max-w-xs">{evt.hash}</td>
                  <td className="p-3 text-right">
                    <span className="text-healthy font-bold flex items-center justify-end gap-1">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      {evt.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
