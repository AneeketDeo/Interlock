import { X, Wrench, Package, AlertTriangle, Activity } from 'lucide-react';
import { MachineStation } from '../../../mock/fixtures';
import { formatPercent, formatTolerance } from '../../../lib/formatters';

interface MachineDrawerProps {
  station: MachineStation | null;
  onClose: () => void;
  onOpenCase: () => void;
}

export function MachineDrawer({ station, onClose, onOpenCase }: MachineDrawerProps) {
  if (!station) return null;

  const isCulprit = station.id === 'st-03b';

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-panel border-l border-strong shadow-2xl z-50 flex flex-col justify-between animate-in slide-in-from-right duration-200">
      <div>
        {/* Drawer Header */}
        <div className="p-4 border-b border-subtle flex items-center justify-between bg-muted/30">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-dim uppercase">{station.id}</span>
              <span
                className={`px-1.5 py-0.2 rounded text-[10px] font-mono font-bold uppercase ${
                  station.status === 'critical'
                    ? 'bg-critical text-white'
                    : station.status === 'interlocked'
                    ? 'bg-caution text-black'
                    : 'bg-healthy/20 text-healthy'
                }`}
              >
                {station.status}
              </span>
            </div>
            <h3 className="font-heading font-bold text-lg text-white mt-1">{station.name}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-secondary hover:text-white hover:bg-raised transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4 text-xs">
          {/* Key Sensor Telemetry Strip */}
          <div className="grid grid-cols-2 gap-2">
            <div className="p-3 bg-raised rounded border border-subtle">
              <span className="text-secondary block font-mono text-[10px]">VIBRATION</span>
              <span className={`font-heading font-bold text-xl tabular-nums ${isCulprit ? 'text-critical' : 'text-white'}`}>
                {station.vibrationMmS.toFixed(2)} <span className="text-xs font-normal text-secondary">mm/s</span>
              </span>
              <span className="text-[10px] text-dim block mt-0.5">Ceiling: 2.2 mm/s</span>
            </div>
            <div className="p-3 bg-raised rounded border border-subtle">
              <span className="text-secondary block font-mono text-[10px]">SPINDLE TEMP</span>
              <span className={`font-heading font-bold text-xl tabular-nums ${isCulprit ? 'text-critical' : 'text-white'}`}>
                {station.temperatureC.toFixed(1)} <span className="text-xs font-normal text-secondary">°C</span>
              </span>
              <span className="text-[10px] text-dim block mt-0.5">Threshold: 55.0°C</span>
            </div>
          </div>

          {/* Operational Metrics */}
          <div className="p-3 bg-raised/50 rounded border border-subtle space-y-2">
            <h4 className="font-heading font-bold text-xs uppercase text-white flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5 text-cobalt" /> Operational Health
            </h4>
            <div className="flex justify-between py-1 border-b border-subtle/40">
              <span className="text-secondary">OEE (Overall Efficiency):</span>
              <span className="font-mono text-white font-bold">{formatPercent(station.oee)}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-subtle/40">
              <span className="text-secondary">Station Scrap Rate:</span>
              <span className={`font-mono font-bold ${isCulprit ? 'text-critical' : 'text-white'}`}>
                {formatPercent(station.scrapRate)}
              </span>
            </div>
            {station.spindleOffsetMm !== undefined && (
              <div className="flex justify-between py-1 border-b border-subtle/40">
                <span className="text-secondary">Spindle Runout Offset:</span>
                <span className="font-mono font-bold text-critical">
                  {formatTolerance(station.spindleOffsetMm)} (Tol: ±0.010 mm)
                </span>
              </div>
            )}
          </div>

          {/* Material Lineage */}
          <div className="p-3 bg-raised/50 rounded border border-subtle space-y-2">
            <h4 className="font-heading font-bold text-xs uppercase text-white flex items-center gap-1.5">
              <Package className="h-3.5 w-3.5 text-healthy" /> In-Feed Material Lot
            </h4>
            <div className="flex justify-between py-1 border-b border-subtle/40">
              <span className="text-secondary">Current Lot ID:</span>
              <span className="font-mono text-white font-semibold">{station.currentLotId}</span>
            </div>
            {isCulprit && (
              <div className="p-2 rounded bg-critical-bg text-critical text-[11px] font-mono border border-critical-border">
                <strong>[OUT-OF-SPECIFICATION]</strong> Silicon measured at 1.82% (Spec: ≤ 1.35%). AlloyTech Global Tier-3 supplier.
              </div>
            )}
          </div>

          {/* Maintenance & Calibration */}
          <div className="p-3 bg-raised/50 rounded border border-subtle space-y-2">
            <h4 className="font-heading font-bold text-xs uppercase text-white flex items-center gap-1.5">
              <Wrench className="h-3.5 w-3.5 text-caution" /> Calibration Status
            </h4>
            <div className="flex justify-between py-1 border-b border-subtle/40">
              <span className="text-secondary">Last Calibrated:</span>
              <span className="font-mono text-white">{station.lastCalibrationDate}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-subtle/40">
              <span className="text-secondary">Assigned Crew:</span>
              <span className="font-mono text-white">{station.lastCalibratedBy}</span>
            </div>
            {isCulprit && (
              <div className="p-2 rounded bg-caution-bg text-caution text-[11px] font-mono border border-caution-border">
                <strong>[RUSHED HANDOVER]</strong> Crew B skipped dial-indicator dynamic tramming on 2024-08-28.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Drawer Action Footer */}
      <div className="p-4 border-t border-subtle bg-panel space-y-2">
        {isCulprit && (
          <button
            onClick={onOpenCase}
            className="w-full py-2.5 rounded bg-critical text-white font-mono text-xs font-bold hover:bg-red-600 transition-colors flex items-center justify-center gap-2"
          >
            <AlertTriangle className="h-4 w-4" />
            Inspect Root Cause Case #INC-8921 &rarr;
          </button>
        )}
        <button
          onClick={onClose}
          className="w-full py-2 rounded bg-raised border border-subtle text-secondary hover:text-white text-xs font-mono transition-colors"
        >
          Close Drawer
        </button>
      </div>
    </div>
  );
}
