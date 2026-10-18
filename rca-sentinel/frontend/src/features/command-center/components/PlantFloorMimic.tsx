import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, CheckCircle2, AlertTriangle, ShieldCheck, ArrowRight, CornerDownRight } from 'lucide-react';
import { useAppStore } from '../../../state/useAppStore';
import { MachineStation } from '../../../mock/fixtures';
import { formatPercent } from '../../../lib/formatters';

interface PlantFloorMimicProps {
  onSelectStation: (station: MachineStation) => void;
}

export function PlantFloorMimic({ onSelectStation }: PlantFloorMimicProps) {
  const navigate = useNavigate();
  const { lines, stations, timelineStage } = useAppStore();
  const [hoveredStation, setHoveredStation] = useState<MachineStation | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Particle simulation for live product flow along conveyor belts
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let width = (canvas.width = canvas.offsetWidth);
    let height = (canvas.height = canvas.offsetHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.offsetWidth;
      height = canvas.height = canvas.offsetHeight;
    };
    window.addEventListener('resize', handleResize);

    // Particles per line
    interface Particle {
      x: number;
      lineIdx: number;
      speed: number;
      status: 'nominal' | 'scrap' | 'rerouted';
    }

    const particles: Particle[] = [];
    const numParticles = 60;

    for (let i = 0; i < numParticles; i++) {
      particles.push({
        x: Math.random() * width,
        lineIdx: Math.floor(Math.random() * 4),
        speed: 0.8 + Math.random() * 0.5,
        status: 'nominal',
      });
    }

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      const rowHeight = height / 4;

      particles.forEach((p) => {
        const isLine3 = p.lineIdx === 2; // Line 03
        const isHalted = isLine3 && timelineStage >= 7;
        const isScrapSpike = isLine3 && timelineStage >= 1 && timelineStage < 7;

        // Advance particle if not halted
        if (!isHalted) {
          p.x += p.speed;
          if (p.x > width) p.x = 0;
        }

        const y = p.lineIdx * rowHeight + rowHeight * 0.5;

        // Particle color logic
        let color = '#3DD6A5'; // healthy seafoam
        if (isScrapSpike && p.x > width * 0.28) {
          color = '#FF5A3C'; // vermilion scrap after station 03b
        } else if (isHalted) {
          color = '#FFB000'; // halted / yellow
        } else if (timelineStage >= 7 && isLine3) {
          color = '#4C8DFF'; // rerouted cobalt batch
        }

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(p.x, y, 2.5, 0, Math.PI * 2);
        ctx.fill();
      });

      animationId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationId);
    };
  }, [timelineStage]);

  return (
    <div className="relative bg-panel border border-subtle rounded-md overflow-hidden">
      {/* Schematic Header */}
      <div className="p-4 border-b border-subtle flex flex-wrap items-center justify-between gap-3 bg-muted/40">
        <div>
          <h2 className="font-heading font-bold text-base text-primary tracking-wide flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-healthy animate-ping" />
            LIVE PLANT FLOOR SCHEMATIC (PRODUCTION FLOW MIMIC)
          </h2>
          <p className="text-xs text-secondary mt-0.5">
            Real-time material takt progression across 4 production lines. Click any station for diagnostic telemetry.
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-healthy" />
            <span className="text-secondary">Nominal (99%+ Yield)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-caution" />
            <span className="text-secondary">Vibration Caution</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-critical animate-pulse" />
            <span className="text-secondary">Scrap Violation / Halted</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-cobalt" />
            <span className="text-secondary">Rerouted Batch Flow</span>
          </div>
        </div>
      </div>

      {/* Schematic Canvas + Interactive Station Nodes */}
      <div className="relative p-6 min-h-[360px] flex flex-col justify-between">
        {/* Background Flow Canvas for Particles */}
        <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none opacity-40 z-0" />

        {/* Production Lines */}
        <div className="space-y-6 relative z-10">
          {lines.map((line) => {
            const isCriticalSpike = line.status === 'degraded' || (line.id === 'line-03' && timelineStage >= 1 && timelineStage < 7);
            const isHalted = line.status === 'halted' || (line.id === 'line-03' && timelineStage >= 7);
            const gridCols = line.stations.length <= 4 ? 'grid-cols-2 md:grid-cols-4' : 'grid-cols-2 md:grid-cols-5';

            return (
              <div
                key={line.id}
                className={`relative p-3 rounded border transition-all ${
                  isCriticalSpike
                    ? 'border-critical/60 bg-critical-bg/20'
                    : isHalted
                    ? 'border-caution/60 bg-caution-bg/20'
                    : 'border-subtle/80 bg-raised/30'
                }`}
              >
                {/* Line Meta Header */}
                <div className="flex items-center justify-between mb-3 text-xs">
                  <div className="flex items-center gap-3">
                    <span className="font-heading font-bold text-sm text-primary">{line.name}</span>
                    <span
                      className={`px-1.5 py-0.2 rounded font-mono text-[10px] uppercase font-semibold ${
                        isCriticalSpike
                          ? 'bg-critical text-white'
                          : isHalted
                          ? 'bg-caution text-black'
                          : 'bg-healthy/20 text-healthy'
                      }`}
                    >
                      {isCriticalSpike ? `SCRAP ELEVATED (${line.scrapRate.toFixed(1)}%)` : isHalted ? 'LINE HALTED (INTERLOCKED)' : 'NOMINAL'}
                    </span>
                  </div>

                  <div className="flex items-center gap-4 font-mono text-secondary">
                    <span>
                      Yield:{' '}
                      <strong className={isCriticalSpike ? 'text-critical' : 'text-primary'}>
                        {formatPercent(line.currentYield)}
                      </strong>
                    </span>
                    <span>
                      Scrap:{' '}
                      <strong className={isCriticalSpike ? 'text-critical' : 'text-primary'}>
                        {formatPercent(line.scrapRate)}
                      </strong>
                    </span>
                    <span>
                      Takt: <strong>{line.currentOutputPpm} ppm</strong>
                    </span>
                  </div>
                </div>

                {/* Stations Row */}
                <div className={`grid ${gridCols} gap-3 items-center`}>
                  {line.stations.map((stationId, stIdx) => {
                    const station = stations.find((s) => s.id === stationId);
                    if (!station) return null;

                    const isFocalStation = station.status === 'critical' || station.id === 'st-03b' || station.id === 'M02';
                    const isFocalSpike = (isFocalStation || station.status === 'critical') && timelineStage >= 1 && timelineStage < 7;
                    const isFocalInterlocked = station.status === 'interlocked' || (isFocalStation && timelineStage >= 7);

                    return (
                      <div key={station.id} className="relative group/station">
                        <button
                          onClick={() => onSelectStation(station)}
                          onMouseEnter={() => setHoveredStation(station)}
                          onMouseLeave={() => setHoveredStation(null)}
                          className={`w-full text-left p-2.5 rounded border transition-all relative ${
                            isFocalSpike
                              ? 'bg-critical-bg border-critical ring-2 ring-critical/40 shadow-lg'
                              : isFocalInterlocked
                              ? 'bg-caution-bg border-caution ring-2 ring-caution/40'
                              : station.status === 'warning'
                              ? 'bg-caution-bg/40 border-caution-border hover:border-caution'
                              : 'bg-panel border-subtle hover:border-strong hover:bg-raised'
                          }`}
                        >
                          {/* Station Label & Icon */}
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="font-mono text-[10px] text-dim uppercase">{station.id}</span>
                            {isFocalSpike ? (
                              <AlertCircle className="h-4 w-4 text-critical animate-bounce" />
                            ) : isFocalInterlocked ? (
                              <ShieldCheck className="h-4 w-4 text-caution" />
                            ) : station.status === 'warning' ? (
                              <AlertTriangle className="h-3.5 w-3.5 text-caution" />
                            ) : (
                              <CheckCircle2 className="h-3.5 w-3.5 text-healthy opacity-60" />
                            )}
                          </div>

                          <div className="font-heading font-semibold text-xs text-primary truncate">
                            {station.name}
                          </div>

                          {/* Quick Sensor Readings */}
                          <div className="mt-1 flex items-center justify-between text-[10px] font-mono text-secondary">
                            <span>{station.vibrationMmS.toFixed(1)} mm/s</span>
                            <span>{station.temperatureC.toFixed(0)}°C</span>
                          </div>

                          {/* Special Callout Beacon for Station 03B */}
                          {isFocalSpike && (
                            <div className="mt-2 pt-1 border-t border-critical/40 flex items-center justify-between text-[10px] text-critical font-bold">
                              <span>WARP DETECTED</span>
                              <span className="underline">INSPECT &rarr;</span>
                            </div>
                          )}
                          {isFocalInterlocked && (
                            <div className="mt-2 pt-1 border-t border-caution/40 flex items-center justify-between text-[10px] text-caution font-bold">
                              <span>INTERLOCKED</span>
                              <span>FEED HOLD</span>
                            </div>
                          )}
                        </button>

                        {/* Hover Quick Diagnostic Tooltip */}
                        {hoveredStation?.id === station.id && (
                          <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 z-50 w-52 p-2.5 bg-panel border border-strong rounded shadow-xl pointer-events-none text-[11px]">
                            <div className="flex items-center justify-between pb-1 border-b border-subtle mb-1">
                              <span className="font-heading font-bold text-primary">{station.name}</span>
                              <span className="font-mono text-[10px] text-dim">{station.id}</span>
                            </div>
                            <div className="grid grid-cols-2 gap-y-1 font-mono text-[10px]">
                              <span className="text-secondary">Live OEE:</span>
                              <span className="text-right font-bold text-primary">{formatPercent(station.oee)}</span>
                              <span className="text-secondary">Scrap Rate:</span>
                              <span className={`text-right font-bold ${station.scrapRate > 5 ? 'text-critical' : 'text-primary'}`}>
                                {formatPercent(station.scrapRate)}
                              </span>
                              <span className="text-secondary">Current Lot:</span>
                              <span className={`text-right font-bold ${station.currentLotId === 'LOT-40921' ? 'text-critical' : 'text-primary'}`}>
                                {station.currentLotId}
                              </span>
                              <span className="text-secondary">Last Cal:</span>
                              <span className="text-right text-dim">{station.lastCalibrationDate}</span>
                            </div>
                            <div className="mt-1 pt-1 border-t border-subtle text-[9px] text-dim flex justify-between">
                              <span>Tech: {station.lastCalibratedBy}</span>
                              <span className="text-cobalt font-semibold">Click for drawer</span>
                            </div>
                          </div>
                        )}

                        {/* Conveyor Arrow between stations */}
                        {stIdx < 4 && (
                          <div className="hidden xl:block absolute -right-2 top-1/2 -translate-y-1/2 z-20 pointer-events-none text-subtle">
                            <ArrowRight className="h-3 w-3" />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* If line is in spike or containment, show actionable path banner */}
                {isCriticalSpike && (
                  <div className="mt-3 p-2 bg-critical-bg border border-critical-border rounded flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-critical">[INCIDENT ACTIVE]</span>
                      <span className="text-primary">
                        Root cause identified as <strong>Lot LOT-409 (Upper-Edge Hardness Alloy)</strong> + <strong>Crew A Skipped Calibration (Step 6 Thermal Offset)</strong>.
                      </span>
                    </div>
                    <button
                      onClick={() => navigate('/incident')}
                      className="px-2.5 py-1 rounded bg-critical text-white font-mono text-xs font-bold hover:bg-red-600 transition-colors shrink-0"
                    >
                      Open Case Board & Reveal Graph &rarr;
                    </button>
                  </div>
                )}

                {isHalted && (
                  <div className="mt-3 p-2 bg-cobalt-bg border border-cobalt-border rounded flex items-center justify-between text-xs text-cobalt font-mono">
                    <div className="flex items-center gap-2">
                      <CornerDownRight className="h-4 w-4 shrink-0 text-cobalt" />
                      <span>
                        FEEDER REROUTED: Active lot switched to <strong>Verified Buffer Lot LOT-377 (Helix Powertrain)</strong>. Machining restart pending recalibration.
                      </span>
                    </div>
                    <span className="font-bold text-healthy">$128,400 LOSS AVOIDED</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
