import { useState } from 'react';
import {
  ShieldCheck,
  Lock,
  CheckCircle2,
  Truck,
  Wrench,
  Cpu,
  FileCheck,
} from 'lucide-react';
import { useAppStore } from '../../../state/useAppStore';

interface RemediationProcessFlowProps {
  onOpenApprovalGate?: () => void;
}

export function RemediationProcessFlow({ onOpenApprovalGate }: RemediationProcessFlowProps) {
  const { proposals, approveProposal, isDryRun, role, timelineStage, setTimelineStage } = useAppStore();
  const [signatoryName] = useState('M. Vance (Lead Reliability PE)');
  const [isAuthorizingAll, setIsAuthorizingAll] = useState(false);

  const canApprove = role === 'reliability_engineer' || role === 'plant_manager';
  const isContained = timelineStage >= 7;

  // Proposal shortcuts
  const interlockProp = proposals.find((p) => p.type === 'plc_interlock') || proposals[0];
  const erpProp = proposals.find((p) => p.type === 'erp_quarantine') || proposals[1];
  const cmmsProp = proposals.find((p) => p.type === 'cmms_work_order') || proposals[2];

  const handleApproveAll = () => {
    setIsAuthorizingAll(true);
    proposals.forEach((p) => {
      approveProposal(p.id, signatoryName);
    });
    setTimelineStage(7);
    setTimeout(() => {
      setIsAuthorizingAll(false);
    }, 600);
  };

  return (
    <div className="bg-panel border border-subtle rounded-md p-6 space-y-6">
      {/* ── Section Header ─────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-subtle pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-cobalt uppercase font-bold tracking-wider">
              ACTUATION ARCHITECTURE
            </span>
            <span className="text-dim">•</span>
            <span className="font-mono text-xs text-dim uppercase">POST-RCA DISPATCH PIPELINE</span>
          </div>
          <h3 className="font-heading font-bold text-xl text-primary mt-1 flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-healthy" />
            Three-Fold Corrective Remediation Flow
          </h3>
          <p className="text-xs text-secondary mt-1 max-w-2xl font-sans">
            Once root cause is isolated through knowledge graph traversal, corrective interventions branch into three decoupled actuator planes: OT Equipment Interlock, IT/ERP Supply Chain Routing, and Maintenance CMMS Work Orders.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isContained ? (
            <div className="p-2.5 rounded bg-healthy-bg border border-healthy-border flex items-center gap-2 text-healthy font-mono text-xs font-bold">
              <CheckCircle2 className="h-4 w-4" />
              <span>CONTAINMENT ACTIVE &bull; ALL 3 BRANCHES DISPATCHED</span>
            </div>
          ) : (
            canApprove && (
              <button
                onClick={handleApproveAll}
                disabled={isAuthorizingAll}
                className="px-4 py-2 rounded bg-critical text-white font-mono text-xs font-bold hover:bg-red-600 transition-colors shadow-md flex items-center gap-2"
              >
                <Lock className="h-4 w-4" />
                <span>{isAuthorizingAll ? 'Dispatching Actuators...' : 'Authorize & Dispatch All 3 Branches'}</span>
              </button>
            )
          )}
        </div>
      </div>

      {/* ── Visual Process Flow Diagram ─────────────────────────────────────── */}
      <div className="space-y-4">
        {/* Top Tier: Input from Semantic Knowledge Graph & 5-Stage RCA */}
        <div className="p-3 bg-canvas/80 border border-subtle rounded-md flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-2 text-primary">
            <span className="h-2 w-2 rounded-full bg-critical animate-ping" />
            <strong className="text-critical uppercase font-bold">CONFIRMED ROOT CAUSE:</strong>
            <span className="text-secondary">
              Lot LOT-409 (Upper-Edge Hardness Alloy) + Crew A Skipped Thermal Offset Verification
            </span>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-dim">
            <span>Graph Ontology: FactoryGraph</span>
            <span>&bull;</span>
            <span className="text-healthy">Inference Confidence: 94.2%</span>
          </div>
        </div>

        {/* Middle Tier: Mandatory Human-in-the-Loop Approval Gate */}
        <div className="p-4 rounded-md border border-caution-border bg-caution-bg/25 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded bg-caution-bg border border-caution-border text-caution">
              <Lock className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="font-heading font-bold text-sm text-primary">
                  HUMAN APPROVAL GATE (HITL)
                </h4>
                {isDryRun && (
                  <span className="px-1.5 py-0.2 rounded font-mono text-[9px] bg-caution-bg text-caution border border-caution-border font-bold">
                    PRE-ACTUATION VERIFICATION GATE
                  </span>
                )}
              </div>
              <p className="text-xs text-secondary mt-0.5 font-sans">
                Mandatory engineering signoff before physical line signals, ERP inventory blocks, or CMMS work orders are committed.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 font-mono text-xs">
            <div className="text-right">
              <span className="text-[10px] text-dim block">SIGNATORY CREDENTIAL</span>
              <span className="text-primary font-bold">{signatoryName}</span>
            </div>
            <span
              className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${
                isContained
                  ? 'bg-healthy text-black'
                  : 'bg-caution text-black animate-pulse'
              }`}
            >
              {isContained ? 'AUTHORIZED & SIGNED' : 'AWAITING AUTHORIZATION'}
            </span>
          </div>
        </div>

        {/* Downward Directional Flow Connector */}
        <div className="flex justify-center items-center py-1 text-dim">
          <div className="h-4 w-0.5 bg-subtle" />
        </div>

        {/* Bottom Tier: Three-Fold Remediation Branches */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Branch 1: Equipment Interlock */}
          <div
            className={`p-4 rounded-md border flex flex-col justify-between transition-all ${
              interlockProp?.status === 'approved' || isContained
                ? 'bg-healthy-bg/20 border-healthy'
                : 'bg-panel border-subtle hover:border-strong'
            }`}
          >
            <div>
              <div className="flex items-center justify-between border-b border-subtle/60 pb-2 mb-3">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded bg-critical-bg text-critical border border-critical-border">
                    <Cpu className="h-4 w-4" />
                  </div>
                  <div>
                    <span className="font-mono text-[9px] text-dim uppercase block leading-none">
                      BRANCH 1 &bull; OT CONTROL
                    </span>
                    <h5 className="font-heading font-bold text-sm text-primary mt-0.5">
                      Equipment Interlock
                    </h5>
                  </div>
                </div>
                <span
                  className={`px-1.5 py-0.5 rounded font-mono text-[10px] font-bold uppercase ${
                    interlockProp?.status === 'approved' || isContained
                      ? 'bg-healthy text-black'
                      : 'bg-critical text-white animate-pulse'
                  }`}
                >
                  {interlockProp?.status === 'approved' || isContained ? 'INTERLOCKED' : 'PENDING'}
                </span>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div>
                  <span className="text-dim text-[10px] block">TARGET WORK CENTERS:</span>
                  <span className="text-primary font-bold">M02, M03, M06, M09, M11 (L1, L2, L3)</span>
                </div>
                <div>
                  <span className="text-dim text-[10px] block">ACTION:</span>
                  <p className="text-secondary text-[11px] font-sans leading-tight mt-0.5">
                    Signal Beckhoff EtherCAT safety controller to execute feed hold on CNC machining centers, disengaging spindle drives.
                  </p>
                </div>
                <div>
                  <span className="text-dim text-[10px] block">PROTOCOL:</span>
                  <span className="text-cobalt">PLC EtherCAT Safety Feed-Hold</span>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-subtle/50 flex items-center justify-between text-xs font-mono">
              <span className="text-secondary">Tool Loss Avoidance:</span>
              <span className="font-bold text-healthy">$68,000 / hr</span>
            </div>
          </div>

          {/* Branch 2: ERP Material Routing */}
          <div
            className={`p-4 rounded-md border flex flex-col justify-between transition-all ${
              erpProp?.status === 'approved' || isContained
                ? 'bg-healthy-bg/20 border-healthy'
                : 'bg-panel border-subtle hover:border-strong'
            }`}
          >
            <div>
              <div className="flex items-center justify-between border-b border-subtle/60 pb-2 mb-3">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded bg-cobalt-bg text-cobalt border border-cobalt-border">
                    <Truck className="h-4 w-4" />
                  </div>
                  <div>
                    <span className="font-mono text-[9px] text-dim uppercase block leading-none">
                      BRANCH 2 &bull; IT / ERP LAYER
                    </span>
                    <h5 className="font-heading font-bold text-sm text-primary mt-0.5">
                      ERP Batch Routing
                    </h5>
                  </div>
                </div>
                <span
                  className={`px-1.5 py-0.5 rounded font-mono text-[10px] font-bold uppercase ${
                    erpProp?.status === 'approved' || isContained
                      ? 'bg-healthy text-black'
                      : 'bg-cobalt text-white animate-pulse'
                  }`}
                >
                  {erpProp?.status === 'approved' || isContained ? 'REROUTED' : 'PENDING'}
                </span>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div>
                  <span className="text-dim text-[10px] block">CONTAMINATED LOT:</span>
                  <span className="text-critical font-bold">LOT-409 (Upper-Edge Hardness)</span>
                </div>
                <div>
                  <span className="text-dim text-[10px] block">REROUTE TO CLEAN BATCH:</span>
                  <span className="text-healthy font-bold">LOT-377 (Helix Powertrain, 29.6 HRC)</span>
                </div>
                <div>
                  <span className="text-dim text-[10px] block">ACTION:</span>
                  <p className="text-secondary text-[11px] font-sans leading-tight mt-0.5">
                    Quarantine LOT-409 in SAP/ERP inventory to prevent further material draws; switch pneumatic infeed hoppers to LOT-377.
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-subtle/50 flex items-center justify-between text-xs font-mono">
              <span className="text-secondary">Net Avoided Loss:</span>
              <span className="font-bold text-healthy">$128,400</span>
            </div>
          </div>

          {/* Branch 3: CMMS Work Order */}
          <div
            className={`p-4 rounded-md border flex flex-col justify-between transition-all ${
              cmmsProp?.status === 'approved' || isContained
                ? 'bg-healthy-bg/20 border-healthy'
                : 'bg-panel border-subtle hover:border-strong'
            }`}
          >
            <div>
              <div className="flex items-center justify-between border-b border-subtle/60 pb-2 mb-3">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded bg-caution-bg text-caution border border-caution-border">
                    <Wrench className="h-4 w-4" />
                  </div>
                  <div>
                    <span className="font-mono text-[9px] text-dim uppercase block leading-none">
                      BRANCH 3 &bull; MAINTENANCE CMMS
                    </span>
                    <h5 className="font-heading font-bold text-sm text-primary mt-0.5">
                      CMMS Work Order
                    </h5>
                  </div>
                </div>
                <span
                  className={`px-1.5 py-0.5 rounded font-mono text-[10px] font-bold uppercase ${
                    cmmsProp?.status === 'approved' || isContained
                      ? 'bg-healthy text-black'
                      : 'bg-caution text-black animate-pulse'
                  }`}
                >
                  {cmmsProp?.status === 'approved' || isContained ? 'DISPATCHED' : 'PENDING'}
                </span>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div>
                  <span className="text-dim text-[10px] block">DISPATCH TARGET:</span>
                  <span className="text-primary font-bold">Crew B (Swing Shift &bull; Master Millwright)</span>
                </div>
                <div>
                  <span className="text-dim text-[10px] block">WORK ORDER:</span>
                  <span className="text-cobalt font-bold">MO-0028 &bull; Priority 1 Urgent</span>
                </div>
                <div>
                  <span className="text-dim text-[10px] block">ACTION:</span>
                  <p className="text-secondary text-[11px] font-sans leading-tight mt-0.5">
                    Execute Step 6 dynamic thermal offset verification and laser spindle runout calibration (tolerance &le; &plusmn;0.010 mm) before clearing lines for restart.
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-subtle/50 flex items-center justify-between text-xs font-mono">
              <span className="text-secondary">Expected MTBF Restoration:</span>
              <span className="font-bold text-healthy">648 Hours</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Cryptographic Lineage Footnote ──────────────────────────────────── */}
      <div className="pt-3 border-t border-subtle flex flex-wrap items-center justify-between gap-3 text-xs font-mono text-dim">
        <div className="flex items-center gap-2">
          <FileCheck className="h-4 w-4 text-cobalt" />
          <span>Actuator audit trail logged with append-only SHA-256 evidence citations.</span>
        </div>
        {onOpenApprovalGate && (
          <button
            onClick={onOpenApprovalGate}
            className="text-cobalt font-bold hover:underline flex items-center gap-1"
          >
            <span>Detailed Multi-Signatory Policy Gate &rarr;</span>
          </button>
        )}
      </div>
    </div>
  );
}
