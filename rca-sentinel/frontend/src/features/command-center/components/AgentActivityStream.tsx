import { Bot } from 'lucide-react';
import { useAppStore } from '../../../state/useAppStore';

export function AgentActivityStream() {
  const { timelineStage } = useAppStore();

  const events = [
    {
      agent: 'DetectAgent',
      stage: 'Stage 1 (D2)',
      time: '22:01:14',
      status: timelineStage >= 2 ? 'done' : 'pending',
      summary: 'Confirmed CUSUM step-shift on sensor-vib-03b and 12.2% scrap spike on Line 03. Transient noise rejected.',
    },
    {
      agent: 'DiagnoseAgent',
      stage: 'Stage 2 (D4)',
      time: '22:01:15',
      status: timelineStage >= 3 ? 'done' : 'pending',
      summary: 'Traversed graph across 4 hops. Identified AlloyTech Lot #40921 (1.82% Si) & Crew B uncalibrated spindle runout (0.035mm). Decoys dimmed.',
    },
    {
      agent: 'ClassifyAgent',
      stage: 'Stage 3 (PFMEA)',
      time: '22:01:16',
      status: timelineStage >= 4 ? 'done' : 'pending',
      summary: 'Matched FM-WAF-001 (Thermal Spindle Warp). RPN calculated at 280 (S8 O5 D7). Recurrence risk flagged as high without tramming.',
    },
    {
      agent: 'ForecastAgent',
      stage: 'Stage 4 (Risk)',
      time: '22:01:17',
      status: timelineStage >= 5 ? 'done' : 'pending',
      summary: 'Forward blast radius computed: 420 assemblies across 3 active customer delivery batches. Total exposure: $184,800.',
    },
    {
      agent: 'RemediateAgent',
      stage: 'Stage 5 (D3/D5)',
      time: '22:01:18',
      status: timelineStage >= 6 ? 'done' : 'pending',
      summary: 'Drafted 3 containment proposals: Station-03b interlock, ERP lot quarantine with switch to Lot #40889, priority CMMS recalibration. Awaiting human approval.',
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
