import { useState } from 'react';
import {
  ShieldCheck,
  Lock,
  CheckCircle2,
  XCircle,
  RotateCcw,
  FileCheck,
  UserCheck,
} from 'lucide-react';
import { useAppStore } from '../../state/useAppStore';
import { RcaActionProposal } from '../../mock/fixtures';
import { formatCurrency } from '../../lib/formatters';

export function ApprovalGate() {
  const { proposals, approveProposal, rejectProposal, rollbackProposal, role, isDryRun } = useAppStore();

  const [signingProposal, setSigningProposal] = useState<RcaActionProposal | null>(null);
  const [engineerNotes, setEngineerNotes] = useState('');

  const canApprove = role === 'reliability_engineer' || role === 'quality_engineer';

  const handleConfirmSignature = () => {
    if (!signingProposal) return;
    approveProposal(signingProposal.id, `M. Vance (PE Reliability, Shift B) — Notes: ${engineerNotes || 'Standard Containment Protocol'}`);
    setSigningProposal(null);
    setEngineerNotes('');
  };

  return (
    <div className="space-y-6">
      {/* ── Banner: Human in the Loop & Dry-Run Guarantee ────────────────────── */}
      <div className="p-4 bg-panel border border-subtle rounded-md flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded bg-caution-bg border border-caution-border text-caution">
            <Lock className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-heading font-bold text-base text-white tracking-wide">
                MANDATORY HUMAN-IN-THE-LOOP APPROVAL GATE (HITL)
              </span>
              {isDryRun && (
                <span className="px-2 py-0.2 rounded font-mono text-[10px] bg-caution-bg text-caution border border-caution-border font-bold">
                  DRY_RUN: SIMULATED EXECUTION
                </span>
              )}
            </div>
            <p className="text-xs text-secondary mt-0.5 max-w-2xl font-sans">
              AI agents are restricted to proposing interventions. Physical PLC interlocks, ERP inventory quarantines, and CMMS dispatches strictly require signed human engineer authorization.
            </p>
          </div>
        </div>

        {/* User Role Status */}
        <div className="flex items-center gap-3 text-xs font-mono">
          <div className="text-right">
            <span className="text-dim text-[10px] block">ACTIVE CREDENTIAL</span>
            <span className={canApprove ? 'text-healthy font-bold' : 'text-caution font-bold'}>
              {role.toUpperCase().replace('_', ' ')}
            </span>
          </div>
          {!canApprove && (
            <div className="p-2 bg-caution-bg border border-caution-border text-caution text-[11px] rounded">
              Operator view only. Approvals disabled.
            </div>
          )}
        </div>
      </div>

      {/* ── Action Proposal Cards ────────────────────────────────────────────── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between px-1">
          <h3 className="font-heading font-bold text-base text-white tracking-wide">
            PROPOSED CONTAINMENT &amp; CORRECTIVE ACTIONS ({proposals.length})
          </h3>
          <span className="text-xs font-mono text-secondary">
            Decision Window: <strong className="text-critical">11 mins SLA remaining</strong>
          </span>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {proposals.map((proposal) => {
            const isPending = proposal.status === 'pending';
            const isApproved = proposal.status === 'approved';
            const isRejected = proposal.status === 'rejected';
            const isRolledBack = proposal.status === 'rolled_back';

            return (
              <div
                key={proposal.id}
                className={`p-5 rounded-md border transition-all ${
                  isApproved
                    ? 'bg-healthy-bg/20 border-healthy'
                    : isRejected
                    ? 'bg-raised/30 border-subtle opacity-50'
                    : isRolledBack
                    ? 'bg-caution-bg/20 border-caution'
                    : 'bg-panel border-subtle hover:border-strong'
                }`}
              >
                {/* Proposal Header */}
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-subtle pb-3">
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                        proposal.type === 'plc_interlock'
                          ? 'bg-critical text-white'
                          : proposal.type === 'erp_quarantine'
                          ? 'bg-cobalt text-white'
                          : 'bg-caution text-black'
                      }`}
                    >
                      {proposal.type.replace('_', ' ')}
                    </span>
                    <h4 className="font-heading font-bold text-base text-white">{proposal.title}</h4>
                  </div>

                  <div className="flex items-center gap-3 text-xs font-mono">
                    <span className="text-dim">Risk Level:</span>
                    <span
                      className={`font-bold uppercase ${
                        proposal.riskLevel === 'extreme'
                          ? 'text-critical'
                          : proposal.riskLevel === 'moderate'
                          ? 'text-caution'
                          : 'text-healthy'
                      }`}
                    >
                      {proposal.riskLevel}
                    </span>
                    <span className="text-dim">|</span>
                    <span className="text-secondary">
                      Loss Avoided: <strong className="text-healthy">{formatCurrency(proposal.estimatedLossAvoided)}</strong>
                    </span>
                  </div>
                </div>

                {/* Scope & Impact Body */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4 text-xs font-sans">
                  <div>
                    <span className="font-mono text-[10px] text-secondary uppercase font-bold block mb-1">
                      TARGET &amp; PROPOSED ACTION
                    </span>
                    <p className="text-primary leading-relaxed">{proposal.description}</p>
                    <div className="mt-2 font-mono text-[11px] text-dim">
                      Target Entity: <strong className="text-primary">{proposal.targetEntity}</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-raised/50 rounded border border-subtle/60">
                    <span className="font-mono text-[10px] text-secondary uppercase font-bold block mb-1">
                      DIAGNOSTIC EVIDENCE JUSTIFICATION
                    </span>
                    <p className="text-secondary leading-relaxed">{proposal.justification}</p>
                    <div className="mt-2 font-mono text-[10px] text-dim flex items-center justify-between">
                      <span>Reversibility: {proposal.reversibility.replace('_', ' ')}</span>
                      <span>SLA: {Math.floor(proposal.slaSecondsRemaining / 60)}m</span>
                    </div>
                  </div>
                </div>

                {/* Actions & Status Bar */}
                <div className="border-t border-subtle pt-3 flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div>
                    {isApproved && (
                      <div className="flex items-center gap-2 text-healthy font-mono">
                        <CheckCircle2 className="h-4 w-4" />
                        <span>Signed &amp; Approved by {proposal.signedBy}</span>
                      </div>
                    )}
                    {isRejected && (
                      <div className="flex items-center gap-2 text-dim font-mono">
                        <XCircle className="h-4 w-4" />
                        <span>Intervention Rejected by Engineering</span>
                      </div>
                    )}
                    {isRolledBack && (
                      <div className="flex items-center gap-2 text-caution font-mono">
                        <RotateCcw className="h-4 w-4" />
                        <span>Action Safely Rolled Back via Audit Trail</span>
                      </div>
                    )}
                    {isPending && (
                      <span className="text-secondary font-mono text-[11px]">
                        Requires explicit signature before actuator trigger.
                      </span>
                    )}
                  </div>

                  {/* Buttons */}
                  <div className="flex items-center gap-2">
                    {isPending && (
                      <>
                        <button
                          onClick={() => rejectProposal(proposal.id)}
                          className="px-3 py-1.5 rounded bg-raised border border-subtle text-secondary hover:text-white font-mono transition-colors"
                        >
                          Reject
                        </button>
                        <button
                          onClick={() => setSigningProposal(proposal)}
                          disabled={!canApprove}
                          className="px-4 py-1.5 rounded bg-critical text-white font-mono font-bold hover:bg-red-600 disabled:opacity-40 transition-colors flex items-center gap-1.5 shadow-sm"
                        >
                          <UserCheck className="h-4 w-4" />
                          <span>Approve &amp; Sign Action &rarr;</span>
                        </button>
                      </>
                    )}

                    {isApproved && (
                      <button
                        onClick={() => rollbackProposal(proposal.id)}
                        className="px-3 py-1 rounded bg-raised border border-subtle text-secondary hover:text-white font-mono text-xs flex items-center gap-1.5 transition-colors"
                        title="Emergency Rollback"
                      >
                        <RotateCcw className="h-3 w-3" />
                        <span>Rollback Action</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Signature Confirmation Modal ────────────────────────────────────── */}
      {signingProposal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-overlay border border-strong rounded-lg max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-subtle pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-critical" />
                <h3 className="font-heading font-bold text-lg text-white">
                  Confirm Engineering Signature
                </h3>
              </div>
              <button
                onClick={() => setSigningProposal(null)}
                className="text-dim hover:text-white font-mono text-xs"
              >
                Cancel [Esc]
              </button>
            </div>

            <div className="space-y-3 text-xs font-sans">
              <div className="p-3 bg-critical-bg/40 border border-critical-border rounded text-primary">
                <span className="font-mono text-[10px] text-critical uppercase font-bold block mb-1">
                  ACTION TO EXECUTE ({signingProposal.type.toUpperCase()})
                </span>
                <p className="font-semibold text-white">{signingProposal.title}</p>
                <p className="text-secondary text-[11px] mt-1">{signingProposal.description}</p>
              </div>

              <div>
                <label className="font-mono text-[10px] text-secondary uppercase font-bold block mb-1">
                  ENGINEERING JUSTIFICATION NOTES:
                </label>
                <textarea
                  value={engineerNotes}
                  onChange={(e) => setEngineerNotes(e.target.value)}
                  placeholder="e.g., Confirmed Lot #40921 silicon out of spec. Approving immediate feed-hold and buffer lot switchover."
                  className="w-full bg-raised border border-subtle rounded p-2 text-white font-mono text-xs outline-none focus:border-active h-20"
                />
              </div>

              <div className="p-2.5 rounded bg-raised border border-subtle text-[11px] font-mono text-dim">
                Signed by: <strong>M. Vance (Lead Reliability PE, ID #ENG-881)</strong>
                <br />
                Audit Hash: <strong>7f9a12c8...3e4f (SHA-256 Verifiable)</strong>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-subtle">
              <button
                onClick={() => setSigningProposal(null)}
                className="px-4 py-2 rounded bg-raised border border-subtle text-secondary hover:text-white font-mono text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmSignature}
                className="px-5 py-2 rounded bg-critical text-white font-mono text-xs font-bold hover:bg-red-600 transition-colors flex items-center gap-1.5"
              >
                <FileCheck className="h-4 w-4" />
                <span>Sign &amp; Execute Containment</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
