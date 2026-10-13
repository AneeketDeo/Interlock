import { Sun, Moon, AlertTriangle, CheckCircle2, Lock } from 'lucide-react';
import { useAppStore } from '../../state/useAppStore';

export function DesignSystemScreen() {
  const { theme, toggleTheme } = useAppStore();

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* ── Header ───────────────────────────────────────────────────────────── */}
      <div className="p-5 bg-panel border border-subtle rounded-md flex items-center justify-between">
        <div>
          <span className="font-mono text-xs text-dim uppercase tracking-wider block">
            INDUSTRIAL DESIGN SYSTEM SPECIFICATION
          </span>
          <h2 className="font-heading font-bold text-2xl text-white mt-1">
            RCA-Sentinel Token &amp; Component System
          </h2>
          <p className="text-xs text-secondary mt-1">
            Demonstrating control-room semantics across Night Shift and Day Shift themes.
          </p>
        </div>

        <button
          onClick={toggleTheme}
          className="px-3.5 py-2 rounded bg-raised border border-subtle text-white font-mono text-xs flex items-center gap-2 hover:border-strong transition-colors"
        >
          {theme === 'night' ? <Sun className="h-4 w-4 text-caution" /> : <Moon className="h-4 w-4" />}
          <span>Current: {theme === 'night' ? 'Night Shift (Dark)' : 'Day Shift (Light)'} [T]</span>
        </button>
      </div>

      {/* ── Semantic Palette ─────────────────────────────────────────────────── */}
      <div className="bg-panel border border-subtle rounded-md p-5 space-y-4">
        <h3 className="font-heading font-bold text-base text-white">
          1. Semantic Color Tokens
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-4 rounded border border-subtle bg-canvas">
            <span className="h-6 w-full rounded bg-healthy block mb-2" />
            <strong className="text-white">Seafoam (Healthy)</strong>
            <p className="text-dim text-[11px] mt-1">#3DD6A5 &bull; Nominal yield, verified clean batch, contained</p>
          </div>
          <div className="p-4 rounded border border-subtle bg-canvas">
            <span className="h-6 w-full rounded bg-caution block mb-2" />
            <strong className="text-white">Amber (Caution)</strong>
            <p className="text-dim text-[11px] mt-1">#FFB000 &bull; Anomaly drift, pending engineer decision, dry-run</p>
          </div>
          <div className="p-4 rounded border border-subtle bg-canvas">
            <span className="h-6 w-full rounded bg-critical block mb-2" />
            <strong className="text-white">Vermilion (Critical)</strong>
            <p className="text-dim text-[11px] mt-1">#FF5A3C &bull; Scrap spike, out-of-spec lot, halted line</p>
          </div>
          <div className="p-4 rounded border border-subtle bg-canvas">
            <span className="h-6 w-full rounded bg-cobalt block mb-2" />
            <strong className="text-white">Cobalt (Agent AI)</strong>
            <p className="text-dim text-[11px] mt-1">#4C8DFF &bull; Google ADK synthesis, multi-hop traversal</p>
          </div>
        </div>
      </div>

      {/* ── Typography & Numerals ────────────────────────────────────────────── */}
      <div className="bg-panel border border-subtle rounded-md p-5 space-y-4">
        <h3 className="font-heading font-bold text-base text-white">
          2. Industrial Typography Hierarchy
        </h3>
        <div className="space-y-3 font-sans">
          <div className="border-b border-subtle/50 pb-2">
            <span className="font-heading font-bold text-3xl text-white block">
              Barlow Semi Condensed 700: 99.4% YIELD
            </span>
            <span className="text-dim font-mono text-xs">Used for Display KPIs, screen headers, and dense technical signage.</span>
          </div>
          <div className="border-b border-subtle/50 pb-2">
            <span className="font-body text-sm text-secondary block">
              Public Sans 400: Standardized government and technical publication body font, optical sizing, high legibility.
            </span>
          </div>
          <div>
            <span className="font-mono text-sm text-white block">
              Tabular Numerals: 0123456789 vs $184,800.00
            </span>
            <span className="text-dim font-mono text-xs">Enforces non-jittering tabular numerals on all telemetry grids.</span>
          </div>
        </div>
      </div>

      {/* ── Component Primitives ─────────────────────────────────────────────── */}
      <div className="bg-panel border border-subtle rounded-md p-5 space-y-4">
        <h3 className="font-heading font-bold text-base text-white">
          3. Component Primitives
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-3 bg-critical-bg border border-critical rounded text-xs">
            <div className="flex items-center gap-2 text-critical font-bold font-mono">
              <AlertTriangle className="h-4 w-4" />
              <span>CRITICAL ALERT PILL</span>
            </div>
            <p className="text-primary text-[11px] mt-1 font-sans">12.2% scrap spike detected on Station-03b.</p>
          </div>

          <div className="p-3 bg-caution-bg border border-caution rounded text-xs">
            <div className="flex items-center gap-2 text-caution font-bold font-mono">
              <Lock className="h-4 w-4" />
              <span>DRY RUN ACTIVE</span>
            </div>
            <p className="text-primary text-[11px] mt-1 font-sans">Physical PLC interlocks safely simulated.</p>
          </div>

          <div className="p-3 bg-healthy-bg border border-healthy rounded text-xs">
            <div className="flex items-center gap-2 text-healthy font-bold font-mono">
              <CheckCircle2 className="h-4 w-4" />
              <span>CONTAINMENT SECURED</span>
            </div>
            <p className="text-primary text-[11px] mt-1 font-sans">$128,400 in avoided loss recovered.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
