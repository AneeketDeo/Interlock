import { Wrench } from 'lucide-react';
import { useAppStore } from '../../state/useAppStore';
import { formatPercent } from '../../lib/formatters';

export function MaintenanceScreen() {
  const { crews } = useAppStore();

  // Calibration Matrix data (Machine vs. Weeks)
  const heatmapData = [
    { machine: 'Station-01A (Blanker)', w34: 'ok', w35: 'ok', w36: 'ok', w37: 'ok', crew: 'Crew A', skipped: 0 },
    { machine: 'Station-02B (5-Axis Center)', w34: 'ok', w35: 'warn', w36: 'ok', w37: 'ok', crew: 'Crew C', skipped: 1 },
    { machine: 'Station-03A (Face Mill)', w34: 'ok', w35: 'ok', w36: 'ok', w37: 'ok', crew: 'Crew B', skipped: 0 },
    { machine: 'Station-03B (Precision Spindle)', w34: 'ok', w35: 'ok', w36: 'warn', w37: 'critical', crew: 'Crew B (Rushed)', skipped: 1 },
    { machine: 'Station-03C (High-Torque Tap)', w34: 'ok', w35: 'ok', w36: 'ok', w37: 'warn', crew: 'Crew B', skipped: 0 },
    { machine: 'Station-04D (Burn-in Rack)', w34: 'ok', w35: 'ok', w36: 'ok', w37: 'ok', crew: 'Crew A', skipped: 0 },
  ];

  return (
    <div className="space-y-6">
      {/* ── Header ───────────────────────────────────────────────────────────── */}
      <div className="p-5 bg-panel border border-subtle rounded-md flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="font-mono text-xs text-dim uppercase tracking-wider block">
            MAINTENANCE &amp; SHIFT HANDOVER INTELLIGENCE
          </span>
          <h2 className="font-heading font-bold text-2xl text-white mt-1">
            Calibration Compliance &amp; Handover Correlation
          </h2>
          <p className="text-xs text-secondary mt-1 max-w-2xl font-sans">
            Tracking preventive maintenance compliance, skipped calibration procedures, and shift handover duration correlation.
          </p>
        </div>

        <div className="p-3 bg-critical-bg rounded border border-critical-border font-mono text-xs text-right">
          <span className="text-critical text-[10px] block font-bold">CRITICAL PM VIOLATION</span>
          <span className="text-white font-bold">Step 4.2 Spindle Tramming</span>
          <span className="text-critical text-[11px] block mt-0.5">Crew B &bull; Runout 0.035 mm</span>
        </div>
      </div>

      {/* ── Calibration Compliance Heatmap ────────────────────────────────────── */}
      <div className="bg-panel border border-subtle rounded-md p-5 space-y-4">
        <div className="border-b border-subtle pb-3 flex items-center justify-between">
          <div>
            <h3 className="font-heading font-bold text-base text-white tracking-wide flex items-center gap-2">
              <Wrench className="h-4 w-4 text-caution" />
              CALIBRATION COMPLIANCE MATRIX (MACHINES VS. 4 WEEKS)
            </h3>
            <p className="text-xs text-secondary mt-0.5">
              Weekly dynamic indicator inspections across key machining work centers.
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-healthy" /> Passed</span>
            <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-caution" /> Minor Deviation</span>
            <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-critical animate-pulse" /> Skipped / OOT</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-subtle text-secondary">
                <th className="p-3 font-semibold">WORK CENTER</th>
                <th className="p-3 font-semibold text-center">WEEK 34</th>
                <th className="p-3 font-semibold text-center">WEEK 35</th>
                <th className="p-3 font-semibold text-center">WEEK 36</th>
                <th className="p-3 font-semibold text-center">WEEK 37 (CURR)</th>
                <th className="p-3 font-semibold">SKIPPED STEPS</th>
                <th className="p-3 font-semibold">LAST CREW</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-subtle/50">
              {heatmapData.map((row) => (
                <tr key={row.machine} className="hover:bg-raised/40 transition-colors">
                  <td className="p-3 font-bold text-white">{row.machine}</td>
                  {['w34', 'w35', 'w36', 'w37'].map((wKey) => {
                    const status = row[wKey as keyof typeof row];
                    return (
                      <td key={wKey} className="p-3 text-center">
                        <span
                          className={`inline-block h-6 w-14 rounded-sm transition-all ${
                            status === 'critical'
                              ? 'bg-critical text-white font-bold flex items-center justify-center text-[10px] animate-pulse'
                              : status === 'warn'
                              ? 'bg-caution text-black font-semibold flex items-center justify-center text-[10px]'
                              : 'bg-healthy/30 border border-healthy/40'
                          }`}
                        >
                          {status === 'critical' ? 'SKIPPED' : status === 'warn' ? 'WARN' : 'NOMINAL'}
                        </span>
                      </td>
                    );
                  })}
                  <td className="p-3">
                    <span className={row.skipped > 0 ? 'text-critical font-bold' : 'text-secondary'}>
                      {row.skipped} skipped
                    </span>
                  </td>
                  <td className="p-3 text-secondary">{row.crew}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Shift Handover Anomaly & Crew Scorecards ─────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {crews.map((crew) => {
          const isCrewB = crew.id === 'crew-b';

          return (
            <div
              key={crew.id}
              className={`p-5 rounded-md border flex flex-col justify-between ${
                isCrewB ? 'bg-critical-bg/30 border-critical' : 'bg-panel border-subtle'
              }`}
            >
              <div>
                <div className="flex items-center justify-between border-b border-subtle pb-3">
                  <div>
                    <span className="font-mono text-[10px] text-dim uppercase">SHIFT {crew.shift}</span>
                    <h4 className="font-heading font-bold text-base text-white mt-0.5">{crew.name}</h4>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                      crew.handoverQuality === 'rushed'
                        ? 'bg-critical text-white'
                        : crew.handoverQuality === 'exemplary'
                        ? 'bg-healthy text-black'
                        : 'bg-raised text-secondary'
                    }`}
                  >
                    {crew.handoverQuality} handover
                  </span>
                </div>

                <div className="my-4 space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b border-subtle/40">
                    <span className="text-secondary">Lead Technician:</span>
                    <span className="text-white font-bold">{crew.leadTechnician}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-subtle/40">
                    <span className="text-secondary">PM Compliance Rate:</span>
                    <span className={`font-bold ${crew.complianceRate < 90 ? 'text-critical' : 'text-healthy'}`}>
                      {formatPercent(crew.complianceRate)}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-subtle/40">
                    <span className="text-secondary">Avg Handover Duration:</span>
                    <span className={`font-bold ${crew.avgHandoverMinutes < 10 ? 'text-critical' : 'text-white'}`}>
                      {crew.avgHandoverMinutes} mins (Std: &ge; 15m)
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-subtle/40">
                    <span className="text-secondary">Equipment MTBF:</span>
                    <span className="text-white font-bold">{crew.mtbfHours} hours</span>
                  </div>
                </div>
              </div>

              {isCrewB && (
                <div className="p-2.5 rounded bg-critical-bg text-critical text-[11px] font-mono border border-critical-border">
                  <strong>ROOT CAUSE CORRELATION:</strong> Crew B rushed shift handover on 2024-09-15 (4.1 mins), omitting dynamic dial-indicator calibration on Station-03b.
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
