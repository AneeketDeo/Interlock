import { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  GitBranch,
  ShieldCheck,
  Truck,
  Wrench,
  Search,
  FileText,
  Database,
  Palette,
  Sun,
  Moon,
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  Presentation,
  KeyRound,
  Lock,
} from 'lucide-react';
import { useAppStore, UserRole } from '../state/useAppStore';
import { scenarioEngine, SCENARIO_STEPS } from '../mock/scenario';
import { CommandPalette } from '../components/command/CommandPalette';

export function Shell() {
  const {
    theme,
    toggleTheme,
    role,
    setRole,
    dataMode,
    toggleDataMode,
    isSpannerConnected,
    timelineStage,
    isPlaying,
    playbackSpeed,
    setPlaybackSpeed,
    presenterActive,
    setPresenterActive,
    commandPaletteOpen,
    setCommandPaletteOpen,
    proposals,
    isDryRun,
  } = useAppStore();

  const [shortcutsModalOpen, setShortcutsModalOpen] = useState(false);
  const pendingApprovalsCount = proposals.filter((p) => p.status === 'pending').length;

  // Sync theme from URL query param if present
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const themeParam = params.get('theme');
    if (themeParam === 'day' || themeParam === 'night') {
      useAppStore.getState().setTheme(themeParam);
    }
  }, []);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept typing in inputs
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return;

      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(!commandPaletteOpen);
      } else if (e.key.toLowerCase() === 't') {
        e.preventDefault();
        toggleTheme();
      } else if (e.key.toLowerCase() === 'p') {
        e.preventDefault();
        setPresenterActive(!presenterActive);
      } else if (e.key === '?') {
        e.preventDefault();
        setShortcutsModalOpen(true);
      } else if (e.code === 'Space') {
        e.preventDefault();
        if (isPlaying) scenarioEngine.pause();
        else scenarioEngine.play();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        scenarioEngine.stepForward();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        scenarioEngine.stepBackward();
      } else if (e.key.toLowerCase() === 'g') {
        e.preventDefault();
        scenarioEngine.reset();
        scenarioEngine.play();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [commandPaletteOpen, presenterActive, isPlaying, toggleTheme, setCommandPaletteOpen, setPresenterActive]);

  const navItems = [
    { to: '/', label: 'Command Center', icon: Activity },
    { to: '/incident', label: 'Incident Case #8921', icon: AlertTriangle, badge: timelineStage >= 1 ? '1' : undefined },
    { to: '/impact', label: 'Blast Radius & Impact', icon: GitBranch },
    { to: '/approvals', label: 'Approval Gate (HITL)', icon: ShieldCheck, badge: pendingApprovalsCount > 0 ? `${pendingApprovalsCount}` : undefined },
    { to: '/supply-chain', label: 'Supply Chain Lineage', icon: Truck },
    { to: '/maintenance', label: 'Shift & Maintenance', icon: Wrench },
    { to: '/graph', label: 'Graph Explorer', icon: Search },
    { to: '/report', label: '8D Report (Export)', icon: FileText },
    { to: '/trust', label: 'Data & Trust Audit', icon: Database },
    { to: '/design', label: 'Design System', icon: Palette },
  ];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-canvas text-primary select-none">
      {/* ── Left Navigation Rail ──────────────────────────────────────────────── */}
      <aside className="w-16 hover:w-64 transition-all duration-200 z-30 flex flex-col justify-between border-r border-subtle bg-panel group">
        <div>
          {/* Logo / Header */}
          <div className="h-14 flex items-center px-4 border-b border-subtle gap-3 overflow-hidden">
            <div className="h-8 w-8 rounded bg-critical flex items-center justify-center shrink-0 shadow-sm">
              <span className="font-heading font-bold text-white text-base tracking-tighter">RCA</span>
            </div>
            <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-150 whitespace-nowrap overflow-hidden">
              <h1 className="font-heading font-bold text-base tracking-wider uppercase text-white leading-none">
                Sentinel
              </h1>
              <p className="text-[10px] text-secondary font-mono tracking-wider mt-0.5">MFG ROOT CAUSE AI</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-2 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded transition-colors relative ${
                      isActive
                        ? 'bg-raised text-white border-l-2 border-active font-medium'
                        : 'text-secondary hover:text-primary hover:bg-raised/50'
                    }`
                  }
                  title={item.label}
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  <span className="opacity-0 group-hover:opacity-100 transition-opacity duration-150 whitespace-nowrap text-xs truncate">
                    {item.label}
                  </span>
                  {item.badge && (
                    <span className="absolute right-3 top-2.5 px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-critical text-white opacity-0 group-hover:opacity-100 transition-opacity">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Rail Footer */}
        <div className="p-2 border-t border-subtle space-y-1">
          <button
            onClick={() => setShortcutsModalOpen(true)}
            className="w-full flex items-center gap-3 px-3 py-2 rounded text-secondary hover:text-primary hover:bg-raised text-xs transition-colors"
            title="Keyboard Shortcuts (?)"
          >
            <KeyRound className="h-5 w-5 shrink-0" />
            <span className="opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">Shortcuts (?)</span>
          </button>
          <div className="px-3 py-1 opacity-0 group-hover:opacity-100 transition-opacity text-[10px] font-mono text-dim">
            v0.1.0 • GCP Spanner Graph Ready
          </div>
        </div>
      </aside>

      {/* ── Main Content Area ─────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* ── Global Top Operations Bar ───────────────────────────────────────── */}
        <header className="h-14 border-b border-subtle bg-panel px-4 flex items-center justify-between z-20 shrink-0">
          {/* Left: Plant & Incident Quick Context */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-healthy animate-pulse" />
              <span className="font-heading font-semibold text-sm tracking-wide text-primary">
                PLANT 01 (AUSTIN ADVANCED)
              </span>
              <span className="text-dim text-xs">/</span>
              <span className="text-xs text-secondary font-mono">LINE 03 • PRECISION SPINDLE</span>
            </div>

            {/* Dry-run badge */}
            {isDryRun && (
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-caution-bg text-caution border border-caution-border">
                <Lock className="h-3 w-3" /> DRY_RUN ACTIVE
              </span>
            )}

            {/* Live Spanner vs Mock Mode indicator/toggle */}
            <button
              onClick={toggleDataMode}
              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-mono font-semibold border transition-colors ${
                dataMode === 'live'
                  ? 'bg-healthy-bg text-healthy border-healthy-border'
                  : 'bg-raised text-secondary border-subtle'
              }`}
              title="Click to toggle between Live Spanner and Mock Data"
            >
              <Database className="h-3 w-3" />
              <span>{dataMode === 'live' ? (isSpannerConnected ? 'LIVE SPANNER GRAPH' : 'SPANNER (SYNCING)') : 'MOCK MODE'}</span>
            </button>
          </div>

          {/* Center: Scenario Playback / Stepper Controller */}
          <div className="hidden lg:flex items-center gap-2 bg-raised/80 border border-subtle px-3 py-1 rounded">
            <span className="text-[11px] font-mono text-dim uppercase tracking-wider mr-1">SCENARIO:</span>
            
            <button
              onClick={() => scenarioEngine.reset()}
              className="p-1 text-secondary hover:text-primary rounded hover:bg-panel transition-colors"
              title="Reset Scenario [G]"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => {
                if (isPlaying) scenarioEngine.pause();
                else scenarioEngine.play();
              }}
              className="p-1 text-secondary hover:text-primary rounded hover:bg-panel transition-colors"
              title={isPlaying ? 'Pause [Space]' : 'Play [Space]'}
            >
              {isPlaying ? <Pause className="h-3.5 w-3.5 text-caution" /> : <Play className="h-3.5 w-3.5 text-healthy" />}
            </button>
            <button
              onClick={() => scenarioEngine.stepForward()}
              className="p-1 text-secondary hover:text-primary rounded hover:bg-panel transition-colors"
              title="Step Forward [Right Arrow]"
            >
              <SkipForward className="h-3.5 w-3.5" />
            </button>

            {/* Stepper Dots */}
            <div className="flex items-center gap-1.5 ml-2">
              {SCENARIO_STEPS.map((step) => (
                <button
                  key={step.index}
                  onClick={() => useAppStore.getState().setTimelineStage(step.index)}
                  className={`h-2 rounded-full transition-all ${
                    timelineStage === step.index
                      ? 'w-5 bg-active'
                      : timelineStage > step.index
                      ? 'w-2 bg-healthy'
                      : 'w-2 bg-subtle hover:bg-strong'
                  }`}
                  title={`${step.name}: ${step.badge}`}
                />
              ))}
            </div>

            <span className="text-[11px] font-mono text-primary font-medium ml-2 min-w-28 text-center truncate">
              {SCENARIO_STEPS[timelineStage]?.badge}
            </span>

            {/* Speed Toggles */}
            <div className="flex items-center text-[10px] font-mono text-dim ml-2 pl-2 border-l border-subtle gap-1">
              {[0.5, 1, 2].map((s) => (
                <button
                  key={s}
                  onClick={() => setPlaybackSpeed(s)}
                  className={`px-1.5 py-0.5 rounded ${
                    playbackSpeed === s ? 'bg-active text-white' : 'hover:text-secondary'
                  }`}
                >
                  {s}x
                </button>
              ))}
            </div>
          </div>

          {/* Right: Actions, Role & Theme Toggles */}
          <div className="flex items-center gap-3">
            {/* Presenter Mode Button */}
            <button
              onClick={() => setPresenterActive(!presenterActive)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-medium border transition-colors ${
                presenterActive
                  ? 'bg-cobalt-bg text-cobalt border-cobalt-border'
                  : 'bg-raised text-secondary border-subtle hover:text-white'
              }`}
              title="Presenter Walkthrough Mode [P]"
            >
              <Presentation className="h-3.5 w-3.5" />
              <span>3-MIN DEMO</span>
            </button>

            {/* Role Switcher */}
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              className="bg-raised border border-subtle text-xs text-secondary rounded px-2 py-1 outline-none font-mono cursor-pointer hover:border-strong"
            >
              <option value="reliability_engineer">Role: Reliability Eng (Signer)</option>
              <option value="operator">Role: Floor Operator (View Only)</option>
              <option value="quality_engineer">Role: Quality Eng</option>
              <option value="plant_manager">Role: Plant Manager</option>
            </select>

            {/* Day / Night Shift Theme Button */}
            <button
              onClick={toggleTheme}
              className="p-1.5 rounded bg-raised border border-subtle text-secondary hover:text-white transition-colors"
              title={`Switch to ${theme === 'night' ? 'Day Shift (Warm Light)' : 'Night Shift (Dark)'} [T]`}
            >
              {theme === 'night' ? <Sun className="h-4 w-4 text-caution" /> : <Moon className="h-4 w-4" />}
            </button>
          </div>
        </header>

        {/* ── Presenter Mode Walkthrough Banner (When Active) ───────────────────── */}
        {presenterActive && (
          <div className="bg-cobalt-bg border-b border-cobalt-border px-4 py-2 flex items-center justify-between text-xs animate-in slide-in-from-top-2">
            <div className="flex items-center gap-3">
              <span className="font-mono font-bold text-cobalt uppercase px-1.5 py-0.5 rounded bg-cobalt/20">
                PRESENTER MODE • STEP {timelineStage + 1}/8
              </span>
              <p className="text-primary font-medium">
                "{SCENARIO_STEPS[timelineStage]?.talkingPoint}"
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => scenarioEngine.stepBackward()}
                disabled={timelineStage === 0}
                className="px-2 py-1 rounded bg-panel border border-subtle text-secondary hover:text-white disabled:opacity-40"
              >
                Previous
              </button>
              <button
                onClick={() => scenarioEngine.stepForward()}
                disabled={timelineStage === 7}
                className="px-2 py-1 rounded bg-active text-white font-medium hover:bg-blue-600 disabled:opacity-40"
              >
                Next Step &rarr;
              </button>
              <button
                onClick={() => setPresenterActive(false)}
                className="text-dim hover:text-white ml-2 text-xs"
              >
                Exit
              </button>
            </div>
          </div>
        )}

        {/* ── Viewport Router Outlet ───────────────────────────────────────────── */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6 bg-canvas">
          <Outlet />
        </main>
      </div>

      {/* ── Keyboard Shortcuts Modal ─────────────────────────────────────────── */}
      {shortcutsModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-overlay border border-strong rounded-lg max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-subtle pb-3">
              <h3 className="font-heading font-bold text-lg text-white">Industrial Console Shortcuts</h3>
              <button onClick={() => setShortcutsModalOpen(false)} className="text-dim hover:text-white text-sm">
                Esc
              </button>
            </div>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-subtle/50">
                <span className="text-secondary">Toggle Day / Night Shift Theme</span>
                <span className="bg-raised px-2 py-0.5 rounded border border-subtle text-white">T</span>
              </div>
              <div className="flex justify-between py-1 border-b border-subtle/50">
                <span className="text-secondary">Toggle 3-Min Presenter Walkthrough</span>
                <span className="bg-raised px-2 py-0.5 rounded border border-subtle text-white">P</span>
              </div>
              <div className="flex justify-between py-1 border-b border-subtle/50">
                <span className="text-secondary">Play / Pause Scenario Timeline</span>
                <span className="bg-raised px-2 py-0.5 rounded border border-subtle text-white">Space</span>
              </div>
              <div className="flex justify-between py-1 border-b border-subtle/50">
                <span className="text-secondary">Step Forward Scenario</span>
                <span className="bg-raised px-2 py-0.5 rounded border border-subtle text-white">&rarr;</span>
              </div>
              <div className="flex justify-between py-1 border-b border-subtle/50">
                <span className="text-secondary">Step Backward Scenario</span>
                <span className="bg-raised px-2 py-0.5 rounded border border-subtle text-white">&larr;</span>
              </div>
              <div className="flex justify-between py-1 border-b border-subtle/50">
                <span className="text-secondary">Reset & Run Golden Scenario</span>
                <span className="bg-raised px-2 py-0.5 rounded border border-subtle text-white">G</span>
              </div>
              <div className="flex justify-between py-1 border-b border-subtle/50">
                <span className="text-secondary">Command Palette</span>
                <span className="bg-raised px-2 py-0.5 rounded border border-subtle text-white">Cmd / Ctrl + K</span>
              </div>
            </div>
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShortcutsModalOpen(false)}
                className="px-4 py-1.5 bg-raised border border-subtle text-white rounded text-xs hover:bg-panel"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Global Command Palette */}
      <CommandPalette />
    </div>
  );
}
