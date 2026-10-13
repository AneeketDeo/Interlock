import { useNavigate } from 'react-router-dom';
import { AlertTriangle, ShieldCheck, Wrench, Package, ArrowRight } from 'lucide-react';
import { useAppStore } from '../../../state/useAppStore';

export function NeedsAttentionPanel() {
  const navigate = useNavigate();
  const { proposals } = useAppStore();

  const pendingProposals = proposals.filter((p) => p.status === 'pending');

  return (
    <div className="bg-panel border border-subtle rounded-md p-5 flex flex-col justify-between">
      <div className="border-b border-subtle pb-3 flex items-center justify-between">
        <div>
          <h3 className="font-heading font-bold text-sm text-white tracking-wide flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-critical" />
            CRITICAL NEEDS ATTENTION ({pendingProposals.length + 2} ITEMS)
          </h3>
          <p className="text-xs text-secondary mt-0.5">
            Operational bottlenecks, gated engineering decisions, and active supply chain flags.
          </p>
        </div>
      </div>

      <div className="my-4 space-y-3">
        {/* Pending Gated Actions */}
        {pendingProposals.map((proposal) => (
          <div
            key={proposal.id}
            className="p-3 bg-critical-bg/50 border border-critical-border rounded flex flex-wrap items-center justify-between gap-3 text-xs"
          >
            <div className="flex items-center gap-3">
              <ShieldCheck className="h-5 w-5 text-critical shrink-0" />
              <div>
                <span className="font-mono text-[10px] text-critical uppercase font-bold">
                  GATED ACTION • SLA: {Math.floor(proposal.slaSecondsRemaining / 60)}m remaining
                </span>
                <h4 className="font-heading font-bold text-sm text-white mt-0.5">{proposal.title}</h4>
                <p className="text-secondary text-[11px] mt-0.5">{proposal.targetEntity}</p>
              </div>
            </div>
            <button
              onClick={() => navigate('/approvals')}
              className="px-3 py-1.5 rounded bg-critical text-white font-mono text-xs font-bold hover:bg-red-600 transition-colors flex items-center gap-1 shrink-0"
            >
              <span>Review &amp; Sign</span>
              <ArrowRight className="h-3 w-3" />
            </button>
          </div>
        ))}

        {/* Overdue Calibration Item */}
        <div className="p-3 bg-caution-bg/40 border border-caution-border rounded flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <Wrench className="h-5 w-5 text-caution shrink-0" />
            <div>
              <span className="font-mono text-[10px] text-caution uppercase font-bold">
                OVERDUE CALIBRATION
              </span>
              <h4 className="font-heading font-bold text-sm text-white mt-0.5">
                Station-03b Dynamic Runout Tramming
              </h4>
              <p className="text-secondary text-[11px] mt-0.5">
                Skipped by Crew B during rushed 4-min shift handover. Current offset: 0.035mm.
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/maintenance')}
            className="px-3 py-1.5 rounded bg-raised border border-subtle text-secondary hover:text-white font-mono text-xs font-medium transition-colors flex items-center gap-1 shrink-0"
          >
            <span>View Heatmap</span>
            <ArrowRight className="h-3 w-3" />
          </button>
        </div>

        {/* High Risk Supplier Lot */}
        <div className="p-3 bg-raised border border-subtle rounded flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <Package className="h-5 w-5 text-dim shrink-0" />
            <div>
              <span className="font-mono text-[10px] text-dim uppercase font-bold">
                SUPPLIER QUARANTINE HOLD
              </span>
              <h4 className="font-heading font-bold text-sm text-white mt-0.5">
                AlloyTech Global &bull; Lot #40921 (1,200 kg)
              </h4>
              <p className="text-secondary text-[11px] mt-0.5">
                Defect rate: 1.82% Si. Global quality block recommended across Austin plant.
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/supply-chain')}
            className="px-3 py-1.5 rounded bg-raised border border-subtle text-secondary hover:text-white font-mono text-xs font-medium transition-colors flex items-center gap-1 shrink-0"
          >
            <span>Lot Lineage</span>
            <ArrowRight className="h-3 w-3" />
          </button>
        </div>
      </div>
    </div>
  );
}
