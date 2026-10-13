import { useState } from 'react';
import { Package, ShieldCheck } from 'lucide-react';
import { useAppStore } from '../../state/useAppStore';
import { SupplierLot } from '../../mock/fixtures';

export function SupplyChainScreen() {
  const { lots } = useAppStore();
  const [selectedLot, setSelectedLot] = useState<SupplierLot>(lots[0]);

  return (
    <div className="space-y-6">
      {/* ── Header ───────────────────────────────────────────────────────────── */}
      <div className="p-5 bg-panel border border-subtle rounded-md flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="font-mono text-xs text-dim uppercase tracking-wider block">
            RAW MATERIAL &amp; SUPPLIER GENEALOGY
          </span>
          <h2 className="font-heading font-bold text-2xl text-white mt-1">
            Supplier Lot Traceability &amp; Risk Quarantine
          </h2>
          <p className="text-xs text-secondary mt-1 max-w-2xl font-sans">
            Multi-tier supply chain lineage tracing alloy metallurgy, supplier defect PPM, and verified clean backup lots.
          </p>
        </div>

        {/* Quick Buffer Readiness Badge */}
        <div className="p-3 bg-healthy-bg rounded border border-healthy-border font-mono text-xs text-right">
          <span className="text-healthy text-[10px] block font-bold">VERIFIED BACKUP BATCH</span>
          <span className="text-white font-bold">Lot #40889 (PrecisionAlloy)</span>
          <span className="text-healthy text-[11px] block mt-0.5">Staged at Buffer 03 &bull; Ready</span>
        </div>
      </div>

      {/* ── Lots Table ───────────────────────────────────────────────────────── */}
      <div className="bg-panel border border-subtle rounded-md overflow-hidden">
        <div className="p-4 border-b border-subtle flex items-center justify-between bg-muted/30">
          <h3 className="font-heading font-bold text-sm text-white flex items-center gap-2">
            <Package className="h-4 w-4 text-caution" />
            ACTIVE ALLOY INVENTORY LOTS
          </h3>
          <span className="text-xs font-mono text-secondary">
            ASTM-A36 Specification Ceiling: &le; 1.35% Silicon
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-subtle bg-muted/20 text-secondary">
                <th className="p-3 font-semibold">LOT ID</th>
                <th className="p-3 font-semibold">SUPPLIER</th>
                <th className="p-3 font-semibold">TIER</th>
                <th className="p-3 font-semibold">SILICON %</th>
                <th className="p-3 font-semibold">DEFECT PPM</th>
                <th className="p-3 font-semibold">QUANTITY</th>
                <th className="p-3 font-semibold">STATUS</th>
                <th className="p-3 font-semibold text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-subtle/50">
              {lots.map((lot) => {
                const isCulprit = lot.id === 'lot-40921';
                const isVerified = lot.id === 'lot-40889';

                return (
                  <tr
                    key={lot.id}
                    onClick={() => setSelectedLot(lot)}
                    className={`hover:bg-raised/60 transition-colors cursor-pointer ${
                      selectedLot.id === lot.id ? 'bg-raised' : ''
                    }`}
                  >
                    <td className="p-3 font-bold text-white flex items-center gap-2">
                      <Package className={`h-4 w-4 ${isCulprit ? 'text-critical' : isVerified ? 'text-healthy' : 'text-secondary'}`} />
                      <span>{lot.id}</span>
                    </td>
                    <td className="p-3 text-secondary">{lot.supplierName}</td>
                    <td className="p-3">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        lot.supplierTier === 3 ? 'bg-critical/20 text-critical' : 'bg-raised text-secondary'
                      }`}>
                        Tier-{lot.supplierTier}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={`font-bold ${lot.siliconContentPct > lot.specCeilingPct ? 'text-critical' : 'text-healthy'}`}>
                        {lot.siliconContentPct.toFixed(2)}%
                      </span>
                      <span className="text-dim text-[10px] ml-1">(&le; {lot.specCeilingPct}%)</span>
                    </td>
                    <td className="p-3 text-secondary">{lot.defectPpmHistory.toLocaleString()} ppm</td>
                    <td className="p-3 text-secondary">{lot.quantityKg.toLocaleString()} kg</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        lot.quarantineStatus === 'quarantined'
                          ? 'bg-critical text-white'
                          : lot.quarantineStatus === 'verified_buffer'
                          ? 'bg-healthy text-black'
                          : 'bg-healthy/20 text-healthy'
                      }`}>
                        {lot.quarantineStatus.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedLot(lot);
                        }}
                        className="text-cobalt font-bold hover:underline"
                      >
                        Inspect &rarr;
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Selected Lot Deep-Dive Card ───────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-panel border border-subtle rounded-md p-5 space-y-4">
          <div className="border-b border-subtle pb-3">
            <span className="font-mono text-[10px] text-dim uppercase">METALLURGY CERTIFICATE</span>
            <h4 className="font-heading font-bold text-lg text-white mt-0.5">
              Spectrometry Certificate: {selectedLot.id}
            </h4>
          </div>

          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between py-1 border-b border-subtle/40">
              <span className="text-secondary">Vendor Code:</span>
              <span className="text-white font-bold">{selectedLot.vendorCode}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-subtle/40">
              <span className="text-secondary">Material Specification:</span>
              <span className="text-white">{selectedLot.materialType}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-subtle/40">
              <span className="text-secondary">Measured Silicon Content:</span>
              <span className={`font-bold ${selectedLot.siliconContentPct > selectedLot.specCeilingPct ? 'text-critical' : 'text-healthy'}`}>
                {selectedLot.siliconContentPct}% ({selectedLot.siliconContentPct > selectedLot.specCeilingPct ? '+34.8% OVER CEILING' : 'WITHIN CEILING'})
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-subtle/40">
              <span className="text-secondary">Historical Risk Score:</span>
              <span className="font-bold text-white">{selectedLot.riskScore} / 100</span>
            </div>
          </div>
        </div>

        {/* Verified Alternative Solution */}
        <div className="bg-healthy-bg/20 border border-healthy-border rounded-md p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-healthy font-mono text-xs font-bold uppercase mb-1">
              <ShieldCheck className="h-4 w-4" />
              <span>VERIFIED CLEAN BUFFER ALTERNATIVE</span>
            </div>
            <h4 className="font-heading font-bold text-lg text-white">
              PrecisionAlloy Lot #40889 (Staged at Buffer 03)
            </h4>
            <p className="text-xs text-secondary mt-1 font-sans leading-relaxed">
              Fully certified Tier-1 supplier batch with 1.12% silicon (nominal tolerance). Ready for pneumatic hopper transfer to Line 03 within 8 minutes of engineering approval.
            </p>
          </div>

          <div className="mt-4 pt-3 border-t border-healthy-border/40 flex items-center justify-between text-xs font-mono">
            <span className="text-healthy">Readiness: 100% Staged</span>
            <span className="text-white font-bold">2,800 kg In Reserve</span>
          </div>
        </div>
      </div>
    </div>
  );
}
