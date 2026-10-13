import { useState } from 'react';
import { Search, Database } from 'lucide-react';
import { EvidenceGraph, GraphNodeData } from '../incident/components/EvidenceGraph';
import { ProvenanceDrawer } from '../incident/components/ProvenanceDrawer';

export function GraphExplorerScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [pathFrom, setPathFrom] = useState('Supplier: AlloyTech Global');
  const [pathTo, setPathTo] = useState('Machine: Station-03b');
  const [selectedNode, setSelectedNode] = useState<GraphNodeData | null>(null);

  const categories = ['all', 'machine', 'lot', 'maintenance', 'supplier', 'assembly'];

  return (
    <div className="space-y-6">
      {/* ── Header & Path Finder ─────────────────────────────────────────────── */}
      <div className="p-5 bg-panel border border-subtle rounded-md space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-subtle pb-3">
          <div>
            <span className="font-mono text-xs text-dim uppercase tracking-wider block">
              AD-HOC KNOWLEDGE GRAPH EXPLORER
            </span>
            <h2 className="font-heading font-bold text-2xl text-white mt-1">
              Multi-Hop Topology &amp; Lineage Traversal
            </h2>
          </div>
          <div className="flex items-center gap-2 font-mono text-xs text-secondary">
            <Database className="h-4 w-4 text-cobalt" />
            <span>Target: Neo4j Aura Enterprise &bull; Node Cap: 50 max</span>
          </div>
        </div>

        {/* Search & Path Finder Bar */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="relative">
            <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-dim" />
            <input
              type="text"
              placeholder="Search graph nodes (e.g. lot-40921, station-03b)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-raised border border-subtle rounded pl-9 pr-3 py-2 text-xs text-white placeholder-dim outline-none font-mono focus:border-active"
            />
          </div>

          <div className="flex items-center gap-2 bg-raised border border-subtle rounded px-3 py-1 text-xs font-mono">
            <span className="text-dim shrink-0">FROM:</span>
            <input
              type="text"
              value={pathFrom}
              onChange={(e) => setPathFrom(e.target.value)}
              className="bg-transparent text-white outline-none w-full truncate"
            />
          </div>

          <div className="flex items-center gap-2 bg-raised border border-subtle rounded px-3 py-1 text-xs font-mono">
            <span className="text-dim shrink-0">TO:</span>
            <input
              type="text"
              value={pathTo}
              onChange={(e) => setPathTo(e.target.value)}
              className="bg-transparent text-white outline-none w-full truncate"
            />
            <button className="px-2 py-1 bg-active text-white rounded text-[11px] font-bold shrink-0">
              Find Path &rarr;
            </button>
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-2 pt-1 overflow-x-auto text-xs font-mono">
          <span className="text-dim text-[10px] uppercase font-bold mr-1">FILTER NODE TYPE:</span>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded capitalize transition-colors ${
                selectedCategory === cat
                  ? 'bg-active text-white font-bold'
                  : 'bg-raised border border-subtle text-secondary hover:text-white'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* ── Interactive Graph Canvas ─────────────────────────────────────────── */}
      <EvidenceGraph onSelectNode={(node) => setSelectedNode(node)} />

      {/* ── Ontology & Class Hierarchy Overview ──────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-panel border border-subtle rounded-md">
          <span className="font-mono text-[10px] text-dim uppercase">OWL ONTO CLASS</span>
          <h4 className="font-heading font-bold text-sm text-white mt-1">ManufacturingMachine</h4>
          <p className="text-xs text-secondary mt-1 font-sans">
            Inherits: <code>owl:Thing</code> &bull; Rel: <code>CONSUMES_LOT</code>, <code>CALIBRATED_BY</code>
          </p>
        </div>
        <div className="p-4 bg-panel border border-subtle rounded-md">
          <span className="font-mono text-[10px] text-dim uppercase">OWL ONTO CLASS</span>
          <h4 className="font-heading font-bold text-sm text-white mt-1">MaterialLot</h4>
          <p className="text-xs text-secondary mt-1 font-sans">
            Inherits: <code>owl:Thing</code> &bull; Rel: <code>SUPPLIED_BY</code>, <code>USED_IN</code>
          </p>
        </div>
        <div className="p-4 bg-panel border border-subtle rounded-md">
          <span className="font-mono text-[10px] text-dim uppercase">OWL ONTO CLASS</span>
          <h4 className="font-heading font-bold text-sm text-white mt-1">MaintenanceEvent</h4>
          <p className="text-xs text-secondary mt-1 font-sans">
            Inherits: <code>owl:Thing</code> &bull; Rel: <code>CONDUCTED_BY</code>, <code>OCCURRED_ON</code>
          </p>
        </div>
      </div>

      <ProvenanceDrawer nodeData={selectedNode} onClose={() => setSelectedNode(null)} />
    </div>
  );
}
