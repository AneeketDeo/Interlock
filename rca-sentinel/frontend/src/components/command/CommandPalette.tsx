import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Command } from 'cmdk';
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
  Sun,
  Moon,
  Play,
} from 'lucide-react';
import { useAppStore } from '../../state/useAppStore';
import { scenarioEngine } from '../../mock/scenario';

export function CommandPalette() {
  const navigate = useNavigate();
  const { commandPaletteOpen, setCommandPaletteOpen, toggleTheme, theme, approveProposal } = useAppStore();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.key === 'k' && (e.metaKey || e.ctrlKey)) || (e.key === 'Escape' && commandPaletteOpen)) {
        e.preventDefault();
        setCommandPaletteOpen(!commandPaletteOpen);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [commandPaletteOpen, setCommandPaletteOpen]);

  if (!commandPaletteOpen) return null;

  const runAndClose = (fn: () => void) => {
    fn();
    setCommandPaletteOpen(false);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-overlay border border-strong rounded-lg max-w-xl w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-100">
        <Command className="bg-transparent text-primary font-mono text-xs">
          <div className="flex items-center px-3 border-b border-subtle">
            <Search className="h-4 w-4 text-dim mr-2 shrink-0" />
            <Command.Input
              placeholder="Type an operation, screen, or action (e.g. approve, case, lot)..."
              className="w-full bg-transparent py-3 text-xs outline-none text-primary placeholder-dim"
              autoFocus
            />
          </div>

          <Command.List className="max-h-80 overflow-y-auto p-2 space-y-1">
            <Command.Empty className="p-4 text-center text-dim text-xs">
              No matching operations found.
            </Command.Empty>

            <Command.Group heading="NAVIGATION SCREENS" className="text-[10px] text-dim px-2 py-1 uppercase font-bold">
              <Command.Item
                onSelect={() => runAndClose(() => navigate('/'))}
                className="flex items-center gap-2.5 p-2 rounded hover:bg-raised cursor-pointer text-secondary hover:text-primary"
              >
                <Activity className="h-4 w-4 text-healthy" />
                <span>Command Center (Plant Floor Hero)</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runAndClose(() => navigate('/incident'))}
                className="flex items-center gap-2.5 p-2 rounded hover:bg-raised cursor-pointer text-secondary hover:text-primary"
              >
                <AlertTriangle className="h-4 w-4 text-critical" />
                <span>Incident Dashboard &amp; Fleet Anomalies</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runAndClose(() => navigate('/impact'))}
                className="flex items-center gap-2.5 p-2 rounded hover:bg-raised cursor-pointer text-secondary hover:text-primary"
              >
                <GitBranch className="h-4 w-4 text-cobalt" />
                <span>Forward Blast Radius &amp; Impact (Sankey Flow)</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runAndClose(() => navigate('/approvals'))}
                className="flex items-center gap-2.5 p-2 rounded hover:bg-raised cursor-pointer text-secondary hover:text-primary"
              >
                <ShieldCheck className="h-4 w-4 text-caution" />
                <span>Approval Gate (Human in the Loop)</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runAndClose(() => navigate('/supply-chain'))}
                className="flex items-center gap-2.5 p-2 rounded hover:bg-raised cursor-pointer text-secondary hover:text-primary"
              >
                <Truck className="h-4 w-4" />
                <span>Supply Chain Lineage &amp; Lot Risk</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runAndClose(() => navigate('/maintenance'))}
                className="flex items-center gap-2.5 p-2 rounded hover:bg-raised cursor-pointer text-secondary hover:text-primary"
              >
                <Wrench className="h-4 w-4" />
                <span>Maintenance &amp; Shift Handover Intelligence</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runAndClose(() => navigate('/report'))}
                className="flex items-center gap-2.5 p-2 rounded hover:bg-raised cursor-pointer text-secondary hover:text-primary"
              >
                <FileText className="h-4 w-4" />
                <span>8D Problem Solving Report (Print / Export)</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runAndClose(() => navigate('/trust'))}
                className="flex items-center gap-2.5 p-2 rounded hover:bg-raised cursor-pointer text-secondary hover:text-primary"
              >
                <Database className="h-4 w-4" />
                <span>Data &amp; Trust Audit Trail (Admin)</span>
              </Command.Item>
            </Command.Group>

            <Command.Group heading="QUICK OPERATIONS &amp; ACTIONS" className="text-[10px] text-dim px-2 py-1 uppercase font-bold pt-2">
              <Command.Item
                onSelect={() => runAndClose(() => toggleTheme())}
                className="flex items-center gap-2.5 p-2 rounded hover:bg-raised cursor-pointer text-secondary hover:text-primary"
              >
                {theme === 'night' ? <Sun className="h-4 w-4 text-caution" /> : <Moon className="h-4 w-4" />}
                <span>Toggle Shift Theme (Day / Night) [T]</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runAndClose(() => { scenarioEngine.reset(); scenarioEngine.play(); })}
                className="flex items-center gap-2.5 p-2 rounded hover:bg-raised cursor-pointer text-secondary hover:text-primary"
              >
                <Play className="h-4 w-4 text-healthy" />
                <span>Run Operational Scenario Walkthrough [G]</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runAndClose(() => approveProposal('act-001-interlock'))}
                className="flex items-center gap-2.5 p-2 rounded hover:bg-raised cursor-pointer text-critical hover:text-critical font-bold"
              >
                <ShieldCheck className="h-4 w-4 text-critical" />
                <span>Approve Action: Emergency PLC Interlock (ST-03b)</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runAndClose(() => approveProposal('act-002-quarantine'))}
                className="flex items-center gap-2.5 p-2 rounded hover:bg-raised cursor-pointer text-cobalt hover:text-cobalt font-bold"
              >
                <ShieldCheck className="h-4 w-4 text-cobalt" />
                <span>Approve Action: ERP Lot Quarantine &amp; Reroute to Lot #40889</span>
              </Command.Item>
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
