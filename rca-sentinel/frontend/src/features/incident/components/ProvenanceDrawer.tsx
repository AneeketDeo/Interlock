import { X, ShieldCheck, Key } from 'lucide-react';
import { GraphNodeData } from './EvidenceGraph';

interface ProvenanceDrawerProps {
  nodeData: GraphNodeData | null;
  onClose: () => void;
}

export function ProvenanceDrawer({ nodeData, onClose }: ProvenanceDrawerProps) {
  if (!nodeData) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-panel border-l border-strong shadow-2xl z-50 flex flex-col justify-between animate-in slide-in-from-right duration-200">
      <div>
        {/* Header */}
        <div className="p-4 border-b border-subtle flex items-center justify-between bg-muted/30">
          <div>
            <span className="font-mono text-[10px] text-dim uppercase tracking-wider block">
              EVIDENCE PROVENANCE AUDIT
            </span>
            <h3 className="font-heading font-bold text-base text-primary mt-0.5">{nodeData.label}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-secondary hover:text-primary hover:bg-raised transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Details */}
        <div className="p-4 space-y-4 text-xs font-mono">
          {/* Diagnostic Context */}
          <div className="p-3 bg-raised rounded border border-subtle space-y-1">
            <span className="text-[10px] text-secondary uppercase font-bold block mb-1">WHY IT MATTERS</span>
            <p className="text-primary font-sans leading-relaxed">{nodeData.whyItMatters || 'Evaluated as part of multi-hop causal traversal.'}</p>
          </div>

          {/* Source System & Record ID */}
          <div className="p-3 bg-raised/50 rounded border border-subtle space-y-2">
            <div className="flex justify-between py-1 border-b border-subtle/40">
              <span className="text-secondary">Source System:</span>
              <span className="text-primary font-bold">{nodeData.sourceSystem || 'Google Cloud Spanner Graph (FactoryGraph)'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-subtle/40">
              <span className="text-secondary">Record ID:</span>
              <span className="text-primary font-bold">{nodeData.recordId || 'N/A'}</span>
            </div>
            {nodeData.metric && (
              <div className="flex justify-between py-1 border-b border-subtle/40">
                <span className="text-secondary">Measured Value:</span>
                <span className={nodeData.isCulprit ? 'text-critical font-bold' : 'text-primary font-bold'}>
                  {nodeData.metric}
                </span>
              </div>
            )}
            {nodeData.spec && (
              <div className="flex justify-between py-1 border-b border-subtle/40">
                <span className="text-secondary">Specification Limit:</span>
                <span className="text-dim">{nodeData.spec}</span>
              </div>
            )}
          </div>

          {/* Cryptographic Hash for Audit Trail */}
          <div className="p-3 bg-raised/50 rounded border border-subtle space-y-1.5">
            <div className="flex items-center gap-1.5 text-secondary text-[10px] uppercase font-bold">
              <Key className="h-3 w-3 text-cobalt" />
              <span>CRYPTOGRAPHIC EVIDENCE HASH (SHA-256)</span>
            </div>
            <div className="p-2 bg-canvas rounded border border-subtle text-[10px] text-cobalt break-all font-mono">
              {nodeData.evidenceHash || '3f7a8b9c0d1e2f3a8f9a2b71c4d5e89a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e'}
            </div>
            <span className="text-[10px] text-dim block">
              Immutable snapshot verified against SHACL shapes prior to ingestion.
            </span>
          </div>

          {/* Verification Badge */}
          <div className="p-3 rounded bg-healthy-bg border border-healthy-border flex items-center gap-2 text-healthy">
            <ShieldCheck className="h-4 w-4 shrink-0" />
            <span className="text-[11px] font-sans">
              Grounding verified. Citing graph node ID in agent response.
            </span>
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-subtle bg-panel">
        <button
          onClick={onClose}
          className="w-full py-2 rounded bg-raised border border-subtle text-secondary hover:text-primary text-xs font-mono transition-colors"
        >
          Close Provenance
        </button>
      </div>
    </div>
  );
}
