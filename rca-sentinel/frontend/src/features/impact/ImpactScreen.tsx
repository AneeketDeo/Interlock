import { useNavigate } from 'react-router-dom';
import {
  GitBranch,
  DollarSign,
  ArrowRight,
  Building2,
} from 'lucide-react';
import { useAppStore } from '../../state/useAppStore';
import { formatCurrency } from '../../lib/formatters';

export function ImpactScreen() {
  const navigate = useNavigate();
  const { activeCase } = useAppStore();

  const unmitigated = activeCase.grossFinancialExposure; // $184,800
  const avoided = activeCase.avoidedLoss; // $128,400

  // Sankey Node definitions
  const sankeyStages = [
    {
      title: '1. SOURCE CONTAMINANT',
      items: [
        { id: 'lot', name: 'Lot #40921 (AlloyTech)', detail: '1,200kg (1.82% Si)', color: '#FF5A3C' },
      ],
    },
    {
      title: '2. MACHINING STATION',
      items: [
        { id: 'st03b', name: 'Station-03b Spindle', detail: '4.82 mm/s vibration', color: '#FF5A3C' },
      ],
    },
    {
      title: '3. AFFECTED WIP BATCHES',
      items: [
        { id: 'b1', name: 'Batch #40921-A', detail: '140 units (Scrap)', color: '#FF5A3C' },
        { id: 'b2', name: 'Batch #40921-B', detail: '160 units (Scrap)', color: '#FF5A3C' },
        { id: 'b3', name: 'Batch #40921-C', detail: '120 units (Quarantined)', color: '#FFB000' },
      ],
    },
    {
      title: '4. DOWNSTREAM CUSTOMERS',
      items: [
        { id: 'c1', name: 'Tesla Powertrain (PO-9912)', detail: '$68,000 exposure', color: '#FF5A3C' },
        { id: 'c2', name: 'Boeing Tier-1 (PO-9940)', detail: '$76,000 exposure', color: '#FF5A3C' },
        { id: 'c3', name: 'Warehouse Safety Buffer', detail: '$40,800 quarantined', color: '#3DD6A5' },
      ],
    },
  ];

  return (
    <div className="space-y-6">
      {/* ── Header Strip ─────────────────────────────────────────────────────── */}
      <div className="p-5 bg-panel border border-subtle rounded-md flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="font-mono text-xs text-dim uppercase tracking-wider block">
            FORWARD IMPACT &amp; BLAST RADIUS MODEL
          </span>
          <h2 className="font-heading font-bold text-2xl text-white mt-1">
            420 Units at Risk across 3 Customer Delivery Batches
          </h2>
          <p className="text-xs text-secondary mt-1 max-w-3xl font-sans">
            Forward lineage trace from contaminated Material Lot #40921 through production station 03b to finished assemblies and customer purchase orders.
          </p>
        </div>

        <div className="flex items-center gap-4 font-mono text-xs">
          <div className="p-3 bg-raised rounded border border-subtle text-right">
            <span className="text-secondary text-[10px] block">TOTAL EXPOSURE</span>
            <span className="font-heading font-bold text-xl text-critical tabular-nums">
              {formatCurrency(unmitigated)}
            </span>
          </div>
          <div className="p-3 bg-healthy-bg rounded border border-healthy-border text-right">
            <span className="text-healthy text-[10px] block font-bold">AVOIDED LOSS</span>
            <span className="font-heading font-bold text-xl text-healthy tabular-nums">
              {formatCurrency(avoided)}
            </span>
          </div>
        </div>
      </div>

      {/* ── Forward Blast Radius Flow (Custom Industrial Sankey Representation) ─ */}
      <div className="bg-panel border border-subtle rounded-md p-5 space-y-4">
        <div className="border-b border-subtle pb-3 flex items-center justify-between">
          <div>
            <h3 className="font-heading font-bold text-base text-white tracking-wide flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-cobalt" />
              FORWARD BLAST RADIUS FLOW (SANKEY MULTI-TIER TRACE)
            </h3>
            <p className="text-xs text-secondary mt-0.5">
              Material dispersion flow from defective raw lot to customer contracts.
            </p>
          </div>
          <span className="text-xs font-mono text-secondary">
            4 Hops &bull; 420 Downstream Assemblies
          </span>
        </div>

        {/* Sankey Columns Container */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 py-4 items-center">
          {sankeyStages.map((col, idx) => (
            <div key={col.title} className="space-y-3 relative">
              <div className="font-mono text-[10px] font-bold text-dim uppercase border-b border-subtle/50 pb-1">
                {col.title}
              </div>

              <div className="space-y-2">
                {col.items.map((item) => (
                  <div
                    key={item.id}
                    className="p-3 rounded bg-raised border border-subtle text-xs relative group hover:border-strong transition-all shadow-sm"
                  >
                    <div className="flex items-center justify-between font-heading font-bold text-xs text-white">
                      <span>{item.name}</span>
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                    </div>
                    <div className="font-mono text-[11px] text-secondary mt-1">
                      {item.detail}
                    </div>

                    {/* Horizontal Connector Arrow */}
                    {idx < 3 && (
                      <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 z-10 text-subtle pointer-events-none">
                        <ArrowRight className="h-3 w-3 text-secondary" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Financial Exposure Waterfall & Graph Criticality ─────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Waterfall Cost Allocation */}
        <div className="bg-panel border border-subtle rounded-md p-5 flex flex-col justify-between">
          <div className="border-b border-subtle pb-3">
            <h4 className="font-heading font-bold text-sm text-white flex items-center gap-1.5">
              <DollarSign className="h-4 w-4 text-caution" />
              FINANCIAL RISK ALLOCATION BREAKDOWN
            </h4>
            <p className="text-xs text-secondary mt-0.5">
              Specific cost drivers accounting for gross exposure.
            </p>
          </div>

          <div className="my-4 space-y-3 text-xs font-mono">
            <div>
              <div className="flex justify-between text-secondary mb-1">
                <span>1. Direct Material Scrap (420 units @ $200):</span>
                <span className="text-white font-bold">{formatCurrency(84000)} (45.5%)</span>
              </div>
              <div className="h-2 w-full bg-raised rounded overflow-hidden">
                <div className="h-full bg-critical" style={{ width: '45.5%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-secondary mb-1">
                <span>2. Downstream Tear-Down &amp; Rework Labor:</span>
                <span className="text-white font-bold">{formatCurrency(42000)} (22.7%)</span>
              </div>
              <div className="h-2 w-full bg-raised rounded overflow-hidden">
                <div className="h-full bg-caution" style={{ width: '22.7%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-secondary mb-1">
                <span>3. Unplanned Line Downtime (2.5h @ $15.5k/hr):</span>
                <span className="text-white font-bold">{formatCurrency(38800)} (21.0%)</span>
              </div>
              <div className="h-2 w-full bg-raised rounded overflow-hidden">
                <div className="h-full bg-caution" style={{ width: '21.0%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-secondary mb-1">
                <span>4. Customer Contract Delivery Penalties:</span>
                <span className="text-white font-bold">{formatCurrency(20000)} (10.8%)</span>
              </div>
              <div className="h-2 w-full bg-raised rounded overflow-hidden">
                <div className="h-full bg-critical" style={{ width: '10.8%' }} />
              </div>
            </div>
          </div>

          <div className="p-3 rounded bg-healthy-bg border border-healthy-border flex items-center justify-between font-mono text-xs text-healthy">
            <span>Avoided Loss with Approved Containment:</span>
            <span className="font-bold text-sm">+{formatCurrency(avoided)}</span>
          </div>
        </div>

        {/* Graph Criticality Leaderboard */}
        <div className="bg-panel border border-subtle rounded-md p-5 flex flex-col justify-between">
          <div className="border-b border-subtle pb-3">
            <h4 className="font-heading font-bold text-sm text-white flex items-center gap-1.5">
              <Building2 className="h-4 w-4 text-cobalt" />
              GRAPH CRITICALITY &amp; CLUSTER EXPOSURE
            </h4>
            <p className="text-xs text-secondary mt-0.5">
              Network centrality identifying high-vulnerability shared nodes.
            </p>
          </div>

          <div className="my-4 space-y-3 text-xs">
            {/* Crew B Criticality */}
            <div className="p-3 rounded bg-raised border border-subtle">
              <div className="flex items-center justify-between font-mono text-[11px] mb-1">
                <span className="font-bold text-white">MAINTENANCE CREW B (HIGH CENTRALITY)</span>
                <span className="text-critical font-bold">7 OF 9 FAILURES</span>
              </div>
              <p className="text-secondary leading-relaxed font-sans text-xs">
                Crew B was involved in maintenance touchpoints across 7 of 9 recent equipment deviations. Average handover duration was 4.1 minutes vs. 15-minute standard protocol.
              </p>
            </div>

            {/* AlloyTech Criticality */}
            <div className="p-3 rounded bg-raised border border-subtle">
              <div className="flex items-center justify-between font-mono text-[11px] mb-1">
                <span className="font-bold text-white">ALLOYTECH GLOBAL (TIER-3 SUPPLIER)</span>
                <span className="text-caution font-bold">1,200 KG INVENTORY</span>
              </div>
              <p className="text-secondary leading-relaxed font-sans text-xs">
                Lot #40921 was distributed to Line 01 and Line 03. Line 01 still holds 240kg in hopper storage. Immediate ERP quarantine prevents $34,000 in secondary scrap on Line 01.
              </p>
            </div>
          </div>

          <div className="flex justify-end pt-2 border-t border-subtle">
            <button
              onClick={() => navigate('/approvals')}
              className="px-3 py-1.5 rounded bg-critical text-white font-mono text-xs font-bold hover:bg-red-600 transition-colors flex items-center gap-1.5"
            >
              <span>Proceed to Human-in-the-Loop Approval Gate</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
