import { Printer } from 'lucide-react';
import { useAppStore } from '../../state/useAppStore';

interface ReportScreenProps {
  onBack?: () => void;
}

export function ReportScreen({ onBack }: ReportScreenProps = {}) {
  const { activeCase, timelineStage, dataMode } = useAppStore();

  const isLive = dataMode === 'live';

  const dSteps = [
    {
      step: 'D1: TEAM FORMATION',
      title: 'Multidisciplinary RCA Response Team',
      content: 'Champion: Plant Director J. Martinez; Lead: M. Vance (PE Reliability); Quality: S. Chen (QE); Operations: Lines L1, L2, L3 Machining Supervisors.',
      status: 'complete',
    },
    {
      step: 'D2: PROBLEM DESCRIPTION',
      title: isLive
        ? 'Scrap Rate Spike (11.8%) on CNC Milling Centers (M02, M03, M06, M09, M11)'
        : 'Scrap Rate Spike (12.2%) on Precision Spindle Station-03b',
      content: isLive
        ? 'Dimensional defect spike of 11.8% confirmed across 5 CNC milling centers spanning Lines L1, L2, and L3. Workpieces failed automated CMM inspection gate.'
        : 'At 22:01 UTC, vibration telemetry reached 4.82 mm/s with 78.4°C spindle thermal warp. 42 consecutive cycles failed CMM tolerance check on Line 03.',
      status: 'complete',
    },
    {
      step: 'D3: INTERIM CONTAINMENT ACTIONS',
      title: isLive
        ? 'Emergency Feed Hold on M02, M03, M06, M09, M11 & Buffer Reroute to LOT-377'
        : 'Emergency Feed Hold Interlock & Buffer Reroute',
      content: isLive
        ? 'Emergency PLC feed-hold placed on affected CNC centers; LOT-409 placed on ERP quality hold. Feeder lines rerouted to Verified Buffer Lot LOT-377 (Helix Powertrain).'
        : 'Interlock placed on Station-03b; 420 contaminated assemblies quarantined at CMM gate. Feeder rerouted to Verified Buffer Lot #40889.',
      status: timelineStage >= 7 ? 'complete' : 'in_progress',
    },
    {
      step: 'D4: ROOT CAUSE ANALYSIS',
      title: isLive
        ? 'Compound Cause: Upper-Edge Hardness Lot LOT-409 + Crew A Skipped Calibration'
        : 'Compound Cause: High-Silicon Lot #40921 + Skipped Calibration',
      content: isLive
        ? '1) Tier-3 steel lot LOT-409 (Apex Drivetrain / Meridian Specialty Steels) was within nominal spec but at upper edge on hardness (31.7 HRC) and carbon (0.219%). 2) Maintenance Crew A rushed shift handover HO-20261014-S (6.0 mins), skipping Step 6: Thermal offset verification (CAL-0021..CAL-0027). The compound interaction generated tool chatter and uncompensated thermal drift.'
        : '1) AlloyTech Global Tier-3 Lot #40921 contained 1.82% silicon (+34.8% over ceiling). 2) Maintenance Crew B skipped dial-indicator dynamic tramming during rushed 4-min handover (0.035mm offset).',
      status: 'complete',
    },
    {
      step: 'D5: PERMANENT CORRECTIVE ACTIONS',
      title: isLive
        ? 'ERP Quarantine of LOT-409 & Priority Thermal Offset Recalibration'
        : 'Quarantine Supplier Lot & Emergency Dynamic Spindle Tramming',
      content: isLive
        ? 'Global quality block placed on Lot LOT-409. Priority CMMS work order MO-0028 dispatched to Crew B to execute Step 6 dynamic thermal offset verification on all affected centers.'
        : 'Global quality hold placed on Vendor-8812 (AlloyTech). Priority CMMS work order WO-9921 dispatched to Crew A for spindle realignment to ±0.005mm.',
      status: timelineStage >= 7 ? 'complete' : 'pending',
    },
    {
      step: 'D6: IMPLEMENT & VALIDATE PCA',
      title: 'Spindle Runout Verification & Test Run',
      content: 'Verify thermal offset indicators <= +-0.010mm before clearing machines for production. Execute 50-part pilot run with 100% CMM inspection.',
      status: 'pending',
    },
    {
      step: 'D7: PREVENT RECURRENCE',
      title: 'Automated Handover Gate & Inbound Hardness Testing',
      content: 'Enforce mandatory 15-minute electronic shift handover signoff in CMMS. Add automated hardness/carbon verification for Tier-3 steel deliveries.',
      status: 'pending',
    },
    {
      step: 'D8: RECOGNIZE TEAM',
      title: 'Fast Containment Sign-Off',
      content: 'Response team contained incident in 4m 08s, avoiding $128,400 in compounded scrap and preventing customer delivery failure.',
      status: 'pending',
    },
  ];

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* ── Report Actions Header ────────────────────────────────────────────── */}
      <div className="p-5 bg-panel border border-subtle rounded-md flex flex-wrap items-center justify-between gap-4 print:hidden">
        <div>
          <span className="font-mono text-xs text-dim uppercase tracking-wider block">
            FORMAL 8D PROBLEM SOLVING REPORT
          </span>
          <h2 className="font-heading font-bold text-2xl text-primary mt-1">
            8D Corrective Action Report &bull; #{activeCase.id}
          </h2>
          <p className="text-xs text-secondary mt-1">
            Auto-populated from Google ADK agentic pipeline and Google Cloud Spanner Graph evidence.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {onBack && (
            <button
              onClick={onBack}
              className="px-3.5 py-2 rounded bg-raised border border-subtle text-primary font-mono text-xs hover:border-strong transition-colors flex items-center gap-1.5"
            >
              <span>&larr; Back</span>
            </button>
          )}
          <button
            onClick={handlePrint}
            className="px-3.5 py-2 rounded bg-cobalt-bg text-cobalt border border-cobalt-border font-mono text-xs font-bold hover:bg-cobalt/20 transition-colors flex items-center gap-2"
          >
            <Printer className="h-4 w-4" />
            <span>Print / PDF Export</span>
          </button>
        </div>
      </div>

      {/* ── Printable 8D Document ────────────────────────────────────────────── */}
      <div className="bg-panel border border-subtle rounded-md p-8 space-y-6 print:border-none print:p-0 print:bg-white print:text-black">
        {/* Document Header */}
        <div className="border-b-2 border-subtle pb-4 flex justify-between items-start print:border-black">
          <div>
            <h1 className="font-heading font-bold text-2xl text-primary print:text-black uppercase">
              THREADTRACE 8D INVESTIGATION REPORT
            </h1>
            <p className="font-mono text-xs text-secondary mt-1 print:text-gray-700">
              FACILITY: AUSTIN ADVANCED MANUFACTURING &bull; WORK CENTER: LINE 03 (ST-03B)
            </p>
          </div>
          <div className="text-right font-mono text-xs">
            <span className="font-bold text-critical print:text-black block">SEVERITY 8 / CRITICAL</span>
            <span className="text-dim">DATE: 2024-09-15 &bull; SHIFT B</span>
          </div>
        </div>

        {/* 8D Steps (D1 - D8) */}
        <div className="space-y-4">
          {dSteps.map((s) => (
            <div
              key={s.step}
              className="p-4 bg-raised/40 border border-subtle rounded print:bg-transparent print:border-gray-300"
            >
              <div className="flex items-center justify-between font-mono text-xs mb-1">
                <span className="font-bold text-cobalt print:text-black">{s.step}</span>
                <span
                  className={`px-2 py-0.2 rounded text-[10px] uppercase font-bold ${
                    s.status === 'complete'
                      ? 'bg-healthy/20 text-healthy print:text-black'
                      : s.status === 'in_progress'
                      ? 'bg-caution/20 text-caution print:text-black'
                      : 'bg-raised text-dim print:text-gray-400'
                  }`}
                >
                  {s.status.replace('_', ' ')}
                </span>
              </div>
              <h3 className="font-heading font-bold text-sm text-primary print:text-black mt-0.5">
                {s.title}
              </h3>
              <p className="text-xs text-secondary print:text-gray-800 mt-1 font-sans leading-relaxed">
                {s.content}
              </p>
            </div>
          ))}
        </div>

        {/* Signatures Footer */}
        <div className="pt-6 border-t-2 border-subtle grid grid-cols-2 gap-8 text-xs font-mono print:border-black">
          <div>
            <span className="text-dim block">LEAD RELIABILITY ENGINEER:</span>
            <div className="mt-4 border-b border-subtle print:border-black pb-1 font-bold text-primary print:text-black">
              M. Vance, PE (Signed Electronically)
            </div>
            <span className="text-[10px] text-dim">SHA-256: 8f9a2b...c38e &bull; 2024-09-15 22:04 UTC</span>
          </div>
          <div>
            <span className="text-dim block">PLANT QUALITY DIRECTOR:</span>
            <div className="mt-4 border-b border-subtle print:border-black pb-1 font-bold text-primary print:text-black">
              J. Martinez (Approved)
            </div>
            <span className="text-[10px] text-dim">Audit Record Verified via FastMCP</span>
          </div>
        </div>
      </div>
    </div>
  );
}
