import { useState } from 'react';
import { Gauge, Zap, ShieldAlert } from 'lucide-react';

export function RcaPerformancePanel() {

  // Editable baseline assumption (e.g. 4.5 hours manual vs 4 minutes ThreadTrace)
  const [manualInvestigationMinutes, setManualInvestigationMinutes] = useState(270); // 4.5 hours
  const threadTraceTotalSeconds = 248; // ~4.1 minutes

  const speedupRatio = (manualInvestigationMinutes * 60) / threadTraceTotalSeconds;

  return (
    <div className="bg-panel border border-subtle rounded-md p-5 flex flex-col justify-between">
      {/* Panel Header */}
      <div className="border-b border-subtle pb-3 flex items-center justify-between">
        <div>
          <h3 className="font-heading font-bold text-sm text-primary tracking-wide flex items-center gap-2">
            <Gauge className="h-4 w-4 text-cobalt" />
            THREADTRACE PERFORMANCE &amp; MTTR BENCHMARK
          </h3>
          <p className="text-xs text-secondary mt-0.5">
            Agentic multi-hop diagnosis vs. standard manual engineering investigation.
          </p>
        </div>
        <span className="text-[11px] font-mono text-cobalt font-bold px-2 py-0.5 rounded bg-cobalt/20">
          {speedupRatio.toFixed(0)}x FASTER CONTAINMENT
        </span>
      </div>

      {/* Speed Comparison Block */}
      <div className="my-4 grid grid-cols-2 gap-3 text-xs">
        {/* ThreadTrace Agents */}
        <div className="p-3 bg-cobalt-bg/60 border border-cobalt-border rounded">
          <div className="flex items-center justify-between text-cobalt font-mono font-bold text-[10px] uppercase">
            <span>THREADTRACE AGENTS</span>
            <Zap className="h-3.5 w-3.5" />
          </div>
          <div className="font-heading font-bold text-2xl text-primary mt-1 tabular-nums">
            4m 08s
          </div>
          <span className="text-[10px] text-secondary block mt-0.5">
            Detection (0.4s) &bull; Diagnosis (1.2s) &bull; Signoff
          </span>
        </div>

        {/* Manual Investigation Baseline */}
        <div className="p-3 bg-raised border border-subtle rounded">
          <div className="flex items-center justify-between text-secondary font-mono text-[10px] uppercase">
            <span>MANUAL BASELINE (HISTORICAL BENCHMARK)</span>
            <ShieldAlert className="h-3.5 w-3.5 text-dim" />
          </div>
          <div className="font-heading font-bold text-2xl text-primary mt-1 tabular-nums flex items-baseline gap-1">
            <span>{Math.floor(manualInvestigationMinutes / 60)}h {manualInvestigationMinutes % 60}m</span>
          </div>
          <div className="mt-1 flex items-center gap-1">
            <input
              type="range"
              min="120"
              max="480"
              step="30"
              value={manualInvestigationMinutes}
              onChange={(e) => setManualInvestigationMinutes(Number(e.target.value))}
              className="w-full accent-blue-500 h-1 bg-subtle rounded cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* Diagnostic Metrics Matrix */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono border-t border-subtle pt-3">
        <div className="p-2 bg-raised/50 rounded border border-subtle/50">
          <span className="text-secondary text-[10px] block">AGENT CONFIDENCE</span>
          <span className="font-heading font-bold text-sm text-healthy">94.2%</span>
        </div>
        <div className="p-2 bg-raised/50 rounded border border-subtle/50">
          <span className="text-secondary text-[10px] block">EVIDENCE CITED</span>
          <span className="font-heading font-bold text-sm text-primary">4 Entities</span>
        </div>
        <div className="p-2 bg-raised/50 rounded border border-subtle/50">
          <span className="text-secondary text-[10px] block">FALSE POSITIVE</span>
          <span className="font-heading font-bold text-sm text-primary">1.4%</span>
        </div>
        <div className="p-2 bg-raised/50 rounded border border-subtle/50">
          <span className="text-secondary text-[10px] block">HUMAN OVERRIDE</span>
          <span className="font-heading font-bold text-sm text-primary">2.1%</span>
        </div>
      </div>
    </div>
  );
}
