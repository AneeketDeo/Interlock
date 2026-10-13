import { DollarSign, TrendingDown, Clock, ShieldCheck } from 'lucide-react';
import { useAppStore } from '../../../state/useAppStore';
import { formatCurrency } from '../../../lib/formatters';

export function FinancialWaterfallPanel() {
  const { activeCase, timelineStage } = useAppStore();

  const isContained = timelineStage >= 7;
  const unmitigatedExposure = activeCase.grossFinancialExposure; // $184,800
  const avoidedLoss = activeCase.avoidedLoss; // $128,400

  return (
    <div className="bg-panel border border-subtle rounded-md p-5 flex flex-col justify-between">
      {/* Panel Header */}
      <div className="border-b border-subtle pb-3 flex items-center justify-between">
        <div>
          <h3 className="font-heading font-bold text-sm text-white tracking-wide flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-caution" />
            FINANCIAL EXPOSURE &amp; MITIGATION WATERFALL
          </h3>
          <p className="text-xs text-secondary mt-0.5">
            Dollar impact on scrap, rework, line downtime, and customer SLA penalties.
          </p>
        </div>

        {/* SLA Countdown Clock */}
        <div className="flex items-center gap-2 bg-critical-bg border border-critical-border px-2.5 py-1 rounded text-xs font-mono">
          <Clock className="h-3.5 w-3.5 text-critical animate-pulse" />
          <span className="text-secondary">Containment SLA:</span>
          <span className="text-critical font-bold">11m 24s</span>
        </div>
      </div>

      {/* Main Figures: With vs Without Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
        {/* Unmitigated Loss */}
        <div className="p-4 bg-raised rounded border border-subtle relative overflow-hidden">
          <span className="text-xs font-mono text-secondary uppercase block">
            UNMITIGATED EXPOSURE (NO ACTION)
          </span>
          <div className="font-heading font-bold text-3xl text-critical mt-1 tabular-nums">
            {formatCurrency(unmitigatedExposure)}
          </div>
          <span className="text-[11px] text-dim block mt-1">
            420 units scrap + 2.5h line stoppage + PO-9912 SLA penalty
          </span>
          <div className="absolute top-2 right-2 opacity-10">
            <TrendingDown className="h-16 w-16 text-critical" />
          </div>
        </div>

        {/* Avoided Loss / Recovered */}
        <div className={`p-4 rounded border relative overflow-hidden transition-all ${
          isContained
            ? 'bg-healthy-bg border-healthy text-healthy'
            : 'bg-cobalt-bg border-cobalt-border text-cobalt'
        }`}>
          <span className="text-xs font-mono uppercase block font-semibold">
            {isContained ? 'CONTAINED & RECOVERED VALUE' : 'NET AVOIDABLE LOSS (WITH ACTIONS)'}
          </span>
          <div className="font-heading font-bold text-3xl mt-1 tabular-nums">
            {formatCurrency(avoidedLoss)}
          </div>
          <span className="text-[11px] opacity-80 block mt-1">
            Station interlock halts defectives; feeder reroutes to verified lot in 8 mins
          </span>
          <div className="absolute top-2 right-2 opacity-15">
            <ShieldCheck className="h-16 w-16" />
          </div>
        </div>
      </div>

      {/* Waterfall Breakdown Rows */}
      <div className="space-y-2 text-xs font-mono border-t border-subtle pt-3">
        <div className="flex justify-between py-1 border-b border-subtle/40">
          <span className="text-secondary">1. Direct Scrap (420 assemblies @ $200/unit):</span>
          <span className="text-white font-bold">{formatCurrency(84000)}</span>
        </div>
        <div className="flex justify-between py-1 border-b border-subtle/40">
          <span className="text-secondary">2. Downstream Tear-Down &amp; Rework:</span>
          <span className="text-white font-bold">{formatCurrency(42000)}</span>
        </div>
        <div className="flex justify-between py-1 border-b border-subtle/40">
          <span className="text-secondary">3. Unplanned Line Downtime (2.5 hrs @ $15.5k/hr):</span>
          <span className="text-white font-bold">{formatCurrency(38800)}</span>
        </div>
        <div className="flex justify-between py-1 border-b border-subtle/40">
          <span className="text-secondary">4. Customer SLA Delivery Penalties (Order #PO-9912):</span>
          <span className="text-white font-bold">{formatCurrency(20000)}</span>
        </div>
        <div className="flex justify-between pt-1 font-bold text-sm">
          <span className="text-healthy">Avoided Exposure Upon Gated Interlock:</span>
          <span className="text-healthy tabular-nums">-{formatCurrency(avoidedLoss)} (69.5%)</span>
        </div>
      </div>
    </div>
  );
}
