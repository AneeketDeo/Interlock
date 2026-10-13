import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  Layers,
  Clock,
  TrendingDown,
} from 'lucide-react';
import { useAppStore } from '../../state/useAppStore';
import { MachineStation } from '../../mock/fixtures';
import { formatPercent } from '../../lib/formatters';

import { PlantFloorMimic } from './components/PlantFloorMimic';
import { MachineDrawer } from './components/MachineDrawer';
import { FinancialWaterfallPanel } from './components/FinancialWaterfallPanel';
import { RcaPerformancePanel } from './components/RcaPerformancePanel';
import { AgentActivityStream } from './components/AgentActivityStream';
import { NeedsAttentionPanel } from './components/NeedsAttentionPanel';

export function CommandCenter() {
  const navigate = useNavigate();
  const { lines, timelineStage } = useAppStore();
  const [selectedStation, setSelectedStation] = useState<MachineStation | null>(null);

  const isScrapSpike = timelineStage >= 1 && timelineStage < 7;
  const isContained = timelineStage >= 7;

  // Plant-wide weighted calculations
  const avgYield = lines.reduce((acc, l) => acc + l.currentYield, 0) / lines.length;
  const avgScrap = lines.reduce((acc, l) => acc + l.scrapRate, 0) / lines.length;

  return (
    <div className="space-y-6">
      {/* ── Operational Health & "So What?" KPI Strip ─────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-3">
        {/* Plant First-Pass Yield */}
        <div className="p-3 bg-panel border border-subtle rounded-md">
          <div className="flex items-center justify-between text-secondary font-mono text-[10px] uppercase">
            <span>FIRST-PASS YIELD</span>
            {isScrapSpike ? (
              <ArrowDownRight className="h-3 w-3 text-critical" />
            ) : (
              <ArrowUpRight className="h-3 w-3 text-healthy" />
            )}
          </div>
          <div className="font-heading font-bold text-2xl text-white mt-1 tabular-nums">
            {formatPercent(avgYield)}
          </div>
          <span className="text-[10px] text-dim block mt-0.5">
            Target: 99.2% {isScrapSpike ? <strong className="text-critical">(-2.9%)</strong> : ''}
          </span>
        </div>

        {/* Plant Scrap Rate */}
        <div className={`p-3 rounded-md border ${
          isScrapSpike ? 'bg-critical-bg/40 border-critical' : 'bg-panel border-subtle'
        }`}>
          <div className="flex items-center justify-between font-mono text-[10px] uppercase">
            <span className={isScrapSpike ? 'text-critical font-bold' : 'text-secondary'}>SCRAP RATE</span>
            {isScrapSpike && <AlertTriangle className="h-3 w-3 text-critical animate-pulse" />}
          </div>
          <div className={`font-heading font-bold text-2xl mt-1 tabular-nums ${
            isScrapSpike ? 'text-critical' : 'text-white'
          }`}>
            {formatPercent(avgScrap)}
          </div>
          <span className="text-[10px] text-dim block mt-0.5">Norm: 0.8%</span>
        </div>

        {/* Plant OEE */}
        <div className="p-3 bg-panel border border-subtle rounded-md">
          <div className="flex items-center justify-between text-secondary font-mono text-[10px] uppercase">
            <span>PLANT OEE</span>
            <Activity className="h-3 w-3 text-cobalt" />
          </div>
          <div className="font-heading font-bold text-2xl text-white mt-1 tabular-nums">
            {isScrapSpike ? '81.4%' : '92.6%'}
          </div>
          <span className="text-[10px] text-dim block mt-0.5">Avail: 92% • Perf: 94% • Q: 88%</span>
        </div>

        {/* Throughput vs Plan */}
        <div className="p-3 bg-panel border border-subtle rounded-md">
          <div className="flex items-center justify-between text-secondary font-mono text-[10px] uppercase">
            <span>THROUGHPUT</span>
            <Layers className="h-3 w-3 text-healthy" />
          </div>
          <div className="font-heading font-bold text-2xl text-white mt-1 tabular-nums">
            1,045 <span className="text-xs text-secondary font-normal font-sans">ppm</span>
          </div>
          <span className="text-[10px] text-dim block mt-0.5">Plan: 1,135 ppm (-8.0%)</span>
        </div>

        {/* Unplanned Downtime */}
        <div className="p-3 bg-panel border border-subtle rounded-md">
          <div className="flex items-center justify-between text-secondary font-mono text-[10px] uppercase">
            <span>UNPLANNED DOWNTIME</span>
            <Clock className="h-3 w-3 text-caution" />
          </div>
          <div className="font-heading font-bold text-2xl text-white mt-1 tabular-nums">
            {isContained ? '0.6 hrs' : '1.8 hrs'}
          </div>
          <span className="text-[10px] text-dim block mt-0.5">Cost: $15.5k / hour</span>
        </div>

        {/* WIP At Risk */}
        <div className="p-3 bg-panel border border-subtle rounded-md">
          <div className="flex items-center justify-between text-secondary font-mono text-[10px] uppercase">
            <span>WIP AT RISK</span>
            <TrendingDown className="h-3 w-3 text-critical" />
          </div>
          <div className={`font-heading font-bold text-2xl mt-1 tabular-nums ${
            isScrapSpike ? 'text-critical' : 'text-white'
          }`}>
            420 <span className="text-xs text-secondary font-normal font-sans">units</span>
          </div>
          <span className="text-[10px] text-dim block mt-0.5">Batches #40921-A/B/C</span>
        </div>

        {/* Active Incidents */}
        <div
          onClick={() => navigate('/incident')}
          className={`p-3 rounded-md border cursor-pointer hover:border-strong transition-all ${
            isScrapSpike ? 'bg-critical-bg border-critical' : 'bg-panel border-subtle'
          }`}
        >
          <div className="flex items-center justify-between font-mono text-[10px] uppercase">
            <span className={isScrapSpike ? 'text-critical font-bold' : 'text-secondary'}>INCIDENTS</span>
            <AlertTriangle className={`h-3 w-3 ${isScrapSpike ? 'text-critical' : 'text-healthy'}`} />
          </div>
          <div className={`font-heading font-bold text-2xl mt-1 tabular-nums ${
            isScrapSpike ? 'text-critical' : 'text-healthy'
          }`}>
            {isScrapSpike ? '1 CRITICAL' : '0 ACTIVE'}
          </div>
          <span className="text-[10px] text-dim block mt-0.5 underline">
            Case #INC-8921 &rarr;
          </span>
        </div>
      </div>

      {/* ── Hero: Plant Floor Schematic (Flow Mimic) ─────────────────────────── */}
      <PlantFloorMimic onSelectStation={(st) => setSelectedStation(st)} />

      {/* ── Operational Analysis Split Row ───────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FinancialWaterfallPanel />
        <RcaPerformancePanel />
      </div>

      {/* ── Bottom Orchestration & Attention Split Row ───────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AgentActivityStream />
        <NeedsAttentionPanel />
      </div>

      {/* ── Machine Diagnostic Drawer (Slideover) ────────────────────────────── */}
      <MachineDrawer
        station={selectedStation}
        onClose={() => setSelectedStation(null)}
        onOpenCase={() => navigate('/incident')}
      />
    </div>
  );
}
