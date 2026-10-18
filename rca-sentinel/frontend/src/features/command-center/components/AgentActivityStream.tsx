import { Bot } from 'lucide-react';
import { useAppStore } from '../../../state/useAppStore';

export function AgentActivityStream() {
  const { timelineStage, dataMode } = useAppStore();

  const isLive = dataMode === 'live';

  const events = [
    {
      agent: 'DetectAgent',
      stage: 'Stage 1 (D2)',
      time: '2026-10-15 07:15',
      status: timelineStage >= 2 ? 'done' : 'pending',
      summary: isLive
        ? 'Confirmed scrap spike (11.8%) on CNC milling centers M02, M03, M06, M09, M11 across Lines L1, L2, L3. Transient noise rejected.'
        : 'Confirmed CUSUM step-shift on sensor-vib-03b and 12.2% scrap spike on Line 03. Transient noise rejected.',
    },
    {
      agent: 'DiagnoseAgent',
      stage: 'Stage 2 (D4)',
      time: '2026-10-15 07:16',
      status: timelineStage >= 3 ? 'done' : 'pending',
      summary: isLive
        ? 'Traversed Spanner FactoryGraph across 4 hops. Identified Lot LOT-409 (31.7 HRC / 0.219% C) & Crew A skipped thermal calibration (HO-20261014-S). Decoys dimmed.'
        : 'Traversed graph across 4 hops. Identified AlloyTech Lot #40921 (1.82% Si) & Crew B uncalibrated spindle runout (0.035mm). Decoys dimmed.',
    },
    {
      agent: 'ClassifyAgent',
      stage: 'Stage 3 (PFMEA)',
      time: '2026-10-15 07:16',
      status: timelineStage >= 4 ? 'done' : 'pending',
      summary: isLive
        ? 'Matched FM-01 / FM-02 (Upper-Edge Hardness Alloy Chatter & Unverified Thermal Spindle Offset). RPN calculated at 280 (S8 O5 D7).'
        : 'Matched FM-WAF-001 (Thermal Spindle Warp). RPN calculated at 280 (S8 O5 D7). Recurrence risk flagged as high without tramming.',
    },
    {
      agent: 'ForecastAgent',
      stage: 'Stage 4 (Risk)',
      time: '2026-10-15 07:17',
      status: timelineStage >= 5 ? 'done' : 'pending',
      summary: isLive
        ? 'Forward blast radius computed: 8 machines that processed LOT-409 across Lines L1, L2, L3. Unmitigated exposure: $184,800.'
        : 'Forward blast radius computed: 420 assemblies across 3 active customer delivery batches. Total exposure: $184,800.',
    },
    {
      agent: 'RemediateAgent',
      stage: 'Stage 5 (D3/D5)',
      time: '2026-10-15 07:18',
      status: timelineStage >= 6 ? 'done' : 'pending',
      summary: isLive
        ? 'Drafted 3 containment proposals: Feed hold on M02/M03/M06/M09/M11, ERP lot quarantine with switch to LOT-377, priority CMMS recalibration. Awaiting human approval.'
        : 'Drafted 3 containment proposals: Station-03b interlock, ERP lot quarantine with switch to Lot #40889, priority CMMS recalibration. Awaiting human approval.',
    },
  ];

  return (
    <div className="bg-panel border border-subtle rounded-md p-5 flex flex-col justify-between">
      <div className="border-b border-subtle pb-3 flex items-center justify-between">
        <div>
          <h3 className="font-heading font-bold text-sm text-white tracking-wide flex items-center gap-2">
            <Bot className="h-4 w-4 text-cobalt" />
            LIVE AGENT REASONING STREAM (ADK ORCHESTRATION)
          </h3>
          <p className="text-xs text-secondary mt-0.5">
            Sequential execution across 5 specialized diagnostic agents.
          </p>
        </div>
        <span className="text-[10px] font-mono text-dim">
          Gemini 2.5 Flash &bull; FastMCP Grounded
        </span>
      </div>

      <div className="my-4 space-y-3">
        {events.map((evt, idx) => {
          const isCurrent = timelineStage === idx + 2;
          const isDone = timelineStage > idx + 2;

          return (
            <div
              key={evt.agent}
              className={`p-3 rounded border text-xs transition-all ${
                isCurrent
                  ? 'bg-cobalt-bg border-cobalt shadow-sm'
                  : isDone
                  ? 'bg-raised/40 border-subtle'
                  : 'bg-raised/10 border-subtle/30 opacity-40'
              }`}
            >
              <div className="flex items-center justify-between font-mono mb-1">
                <div className="flex items-center gap-2">
                  <span className={`font-bold ${isCurrent ? 'text-cobalt' : isDone ? 'text-healthy' : 'text-dim'}`}>
                    {evt.agent}
                  </span>
                  <span className="text-dim text-[10px]">[{evt.stage}]</span>
                </div>
                <span className="text-[10px] text-dim">{evt.time}</span>
              </div>
              <p className="text-secondary leading-relaxed">{evt.summary}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
