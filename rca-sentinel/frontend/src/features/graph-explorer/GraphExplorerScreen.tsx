import { useState, useEffect, useCallback } from 'react';
import { Search, RefreshCw } from 'lucide-react';
import { Node, Edge, MarkerType } from '@xyflow/react';
import { EvidenceGraph, GraphNodeData } from '../incident/components/EvidenceGraph';
import { ProvenanceDrawer } from '../incident/components/ProvenanceDrawer';
import { fetchMachineSubgraph, fetchLotProvenance, SubgraphResponse } from '../../lib/api';

function formatSpannerNodesAndEdges(subgraph: SubgraphResponse): { nodes: Node<GraphNodeData>[]; edges: Edge[] } {
  const nodes: Node<GraphNodeData>[] = [];
  const edges: Edge[] = [];

  const lineNodes = subgraph.nodes.filter((n) => n.label === 'ProductionLine');
  const machineNodes = subgraph.nodes.filter((n) => n.label === 'Machine');
  const sensorNodes = subgraph.nodes.filter((n) => n.label === 'Sensor');
  const maintenanceNodes = subgraph.nodes.filter((n) => n.label === 'MaintenanceEvent');
  const logNodes = subgraph.nodes.filter((n) => n.label === 'OperatorLog');
  const lotNodes = subgraph.nodes.filter((n) => n.label === 'MaterialLot');
  const supplierNodes = subgraph.nodes.filter((n) => n.label === 'Supplier');

  // 1. Line
  lineNodes.forEach((n, i) => {
    nodes.push({
      id: n.id,
      type: 'evidenceNode',
      position: { x: 280 + i * 200, y: 20 },
      data: {
        label: `Line ${n.properties?.id || n.id}`,
        category: 'assembly',
        subLabel: n.properties?.name || 'Production Line',
        sourceSystem: 'Google Cloud Spanner (FactoryGraph)',
        recordId: n.id,
      },
    });
  });

  // 2. Machine
  machineNodes.forEach((n, i) => {
    const isAffected = ['M02', 'M03', 'M06', 'M09', 'M11'].includes(n.id);
    nodes.push({
      id: n.id,
      type: 'evidenceNode',
      position: { x: 280 + i * 220, y: 150 },
      data: {
        label: `Machine ${n.id} (${n.properties?.name || 'Station'})`,
        category: 'machine',
        subLabel: n.properties?.machine_type || 'Machine',
        isCulprit: isAffected,
        metric: isAffected ? 'Vib: 4.82 mm/s • Scrap: 11.8%' : 'Vib: 1.25 mm/s • Scrap: 0.6%',
        sourceSystem: 'Google Cloud Spanner (FactoryGraph)',
        recordId: n.id,
        whyItMatters: isAffected
          ? 'Thermal warp of spindle bearing housing induces scrap spike.'
          : 'Nominal operational machine baseline.',
      },
    });
  });

  // 3. Sensors
  sensorNodes.forEach((n, i) => {
    nodes.push({
      id: n.id,
      type: 'evidenceNode',
      position: { x: 30, y: 50 + i * 110 },
      data: {
        label: `Sensor: ${n.id}`,
        category: 'machine',
        subLabel: `${n.properties?.sensor_type || 'Telemetry'} (${n.properties?.unit || ''})`,
        sourceSystem: 'Google Cloud Spanner (FactoryGraph)',
        recordId: n.id,
      },
    });
  });

  // 4. Maintenance & Handover Logs
  [...maintenanceNodes, ...logNodes].forEach((n, i) => {
    const isMaint = n.label === 'MaintenanceEvent';
    const isRushed = Boolean(n.properties?.handover_rushed || n.properties?.skipped_step);
    nodes.push({
      id: n.id,
      type: 'evidenceNode',
      position: { x: 550, y: 50 + i * 110 },
      data: {
        label: isMaint ? `Calibration ${n.id}` : `Shift Handover (${n.properties?.crew_name || 'Crew'})`,
        category: 'maintenance',
        subLabel: isMaint
          ? `Steps: ${n.properties?.steps_completed}/${n.properties?.steps_required}`
          : n.properties?.text || 'Handover log',
        isCulprit: isRushed,
        metric: isMaint && n.properties?.skipped_step ? `Skipped: ${n.properties?.skipped_step}` : undefined,
        sourceSystem: 'Google Cloud Spanner (FactoryGraph)',
        recordId: n.id,
        whyItMatters: isRushed ? 'Rushed handover omitting thermal verification.' : 'Standard maintenance signoff.',
      },
    });
  });

  // 5. Material Lots
  lotNodes.forEach((n, i) => {
    const isCulprit = n.id === 'LOT-409' || n.properties?.edge_flag === 'UPPER_EDGE_ALL';
    nodes.push({
      id: n.id,
      type: 'evidenceNode',
      position: { x: 200 + i * 220, y: 300 },
      data: {
        label: `Material Lot ${n.id}`,
        category: 'lot',
        subLabel: `Alloy ${n.properties?.material_id || '20MnCr5'}`,
        isCulprit,
        metric: isCulprit ? 'Hardness: 31.7 HRC • Flag: UPPER_EDGE' : 'Nominal Spec',
        sourceSystem: 'Google Cloud Spanner (FactoryGraph)',
        recordId: n.id,
        whyItMatters: isCulprit ? '+34.8% excess silicon induces severe tool chatter.' : 'Within tolerance limit.',
      },
    });
  });

  // 6. Suppliers
  supplierNodes.forEach((n, i) => {
    nodes.push({
      id: n.id,
      type: 'evidenceNode',
      position: { x: 200 + i * 220, y: 430 },
      data: {
        label: `Supplier: ${n.properties?.name || n.id}`,
        category: 'supplier',
        subLabel: `Tier ${n.properties?.tier || '1'} Partner`,
        sourceSystem: 'Google Cloud Spanner (FactoryGraph)',
        recordId: n.id,
      },
    });
  });

  // Edges
  subgraph.edges.forEach((e) => {
    edges.push({
      id: e.id,
      source: e.from_id,
      target: e.to_id,
      label: e.type,
      animated: ['PROCESSED', 'HAS_SENSOR'].includes(e.type),
      style: { stroke: '#4C8DFF', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#4C8DFF' },
    });
  });

  return { nodes, edges };
}

export function GraphExplorerScreen() {
  const [searchQuery, setSearchQuery] = useState('M12');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedNode, setSelectedNode] = useState<GraphNodeData | null>(null);

  const [liveNodes, setLiveNodes] = useState<Node<GraphNodeData>[]>([]);
  const [liveEdges, setLiveEdges] = useState<Edge[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeEntityId, setActiveEntityId] = useState('M12');
  const [stats, setStats] = useState<{ nodeCount: number; edgeCount: number }>({ nodeCount: 0, edgeCount: 0 });

  const categories = ['all', 'machine', 'lot', 'maintenance', 'supplier', 'assembly'];

  const loadGraph = useCallback(async (entityId: string) => {
    setIsLoading(true);
    setActiveEntityId(entityId);
    try {
      const cleanId = entityId.trim();
      const subgraph = await fetchMachineSubgraph(cleanId);
      if (subgraph && subgraph.nodes.length > 0) {
        const { nodes, edges } = formatSpannerNodesAndEdges(subgraph);
        setLiveNodes(nodes);
        setLiveEdges(edges);
        setStats({ nodeCount: subgraph.node_count, edgeCount: subgraph.edge_count });
      } else {
        // Try searching lot provenance
        const lotData = await fetchLotProvenance(cleanId);
        if (lotData && lotData.target_lot) {
          const target = lotData.target_lot;
          const nodes: Node<GraphNodeData>[] = [
            {
              id: target.id,
              type: 'evidenceNode',
              position: { x: 280, y: 180 },
              data: {
                label: `Material Lot ${target.id}`,
                category: 'lot',
                subLabel: target.material_id,
                isCulprit: target.id === 'LOT-409' || target.properties?.edge_flag === 'UPPER_EDGE_ALL',
                metric: target.properties?.hardness_hrc ? `Hardness: ${target.properties.hardness_hrc} HRC` : undefined,
                sourceSystem: 'Google Cloud Spanner (FactoryGraph)',
                recordId: target.id,
              },
            },
          ];
          const edges: Edge[] = [];
          if (target.supplier) {
            nodes.push({
              id: target.supplier.id,
              type: 'evidenceNode',
              position: { x: 280, y: 320 },
              data: {
                label: target.supplier.name,
                category: 'supplier',
                subLabel: `Tier ${target.supplier.tier} Supplier`,
                sourceSystem: 'Google Cloud Spanner (FactoryGraph)',
                recordId: target.supplier.id,
              },
            });
            edges.push({
              id: `${target.supplier.id}-SUPPLIED-${target.id}`,
              source: target.supplier.id,
              target: target.id,
              label: 'SUPPLIED_BY',
              style: { stroke: '#4C8DFF', strokeWidth: 2 },
              markerEnd: { type: MarkerType.ArrowClosed, color: '#4C8DFF' },
            });
          }
          setLiveNodes(nodes);
          setLiveEdges(edges);
          setStats({ nodeCount: nodes.length, edgeCount: edges.length });
        }
      }
    } catch (err) {
      console.error('Failed to load subgraph:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGraph('M12');
  }, [loadGraph]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      loadGraph(searchQuery);
    }
  };

  const filteredNodes = selectedCategory === 'all'
    ? liveNodes
    : liveNodes.filter((n) => n.data.category === selectedCategory);

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
          <div className="flex items-center gap-3 font-mono text-xs text-secondary">
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-healthy-bg text-healthy border border-healthy-border rounded">
              <span className="h-2 w-2 rounded-full bg-healthy animate-pulse" />
              <span>Cloud Spanner: FactoryGraph (ISO GQL)</span>
            </div>
            {stats.nodeCount > 0 && (
              <span className="text-dim">
                ({stats.nodeCount} nodes, {stats.edgeCount} edges)
              </span>
            )}
          </div>
        </div>

        {/* Quick Entity Selectors */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <span className="text-dim text-[11px] uppercase mr-1">LOAD SPANNER ENTITY:</span>
          {['M12', 'M02', 'M06', 'M09', 'LOT-409', 'LOT-377'].map((id) => (
            <button
              key={id}
              onClick={() => {
                setSearchQuery(id);
                loadGraph(id);
              }}
              className={`px-2.5 py-1 rounded border transition-colors ${
                activeEntityId.toUpperCase() === id
                  ? 'bg-active text-white border-active font-bold'
                  : 'bg-raised border-subtle text-secondary hover:text-white hover:border-strong'
              }`}
            >
              {id === 'LOT-409' ? 'LOT-409 (Culprit Lot)' : id === 'M02' ? 'M02 (Affected Mill)' : id}
            </button>
          ))}
          <button
            onClick={() => loadGraph(activeEntityId)}
            className="p-1 rounded text-secondary hover:text-white hover:bg-raised ml-auto"
            title="Refresh from Spanner"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin text-cobalt' : ''}`} />
          </button>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-dim" />
            <input
              type="text"
              placeholder="Query Spanner node ID (e.g. M12, M02, LOT-409, LOT-377)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-raised border border-subtle rounded pl-9 pr-3 py-2 text-xs text-white placeholder-dim outline-none font-mono focus:border-active"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-active text-white rounded text-xs font-mono font-bold hover:bg-blue-600 transition-colors"
          >
            Traverse Graph &rarr;
          </button>
        </form>

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

      {/* ── Interactive Graph Canvas with Real Spanner Data ─────────────────── */}
      <EvidenceGraph
        onSelectNode={(node) => setSelectedNode(node)}
        nodes={filteredNodes}
        edges={liveEdges}
        isLoading={isLoading}
      />

      {/* ── Spanner Property Graph Ontology Overview ────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-panel border border-subtle rounded-md">
          <span className="font-mono text-[10px] text-dim uppercase">SPANNER GRAPH NODE</span>
          <h4 className="font-heading font-bold text-sm text-white mt-1">Machine</h4>
          <p className="text-xs text-secondary mt-1 font-sans">
            Properties: <code>machine_id</code>, <code>line_id</code>, <code>install_year</code> &bull; Edges: <code>PROCESSED</code>, <code>CALIBRATED</code>, <code>HAS_SENSOR</code>
          </p>
        </div>
        <div className="p-4 bg-panel border border-subtle rounded-md">
          <span className="font-mono text-[10px] text-dim uppercase">SPANNER GRAPH NODE</span>
          <h4 className="font-heading font-bold text-sm text-white mt-1">MaterialLot</h4>
          <p className="text-xs text-secondary mt-1 font-sans">
            Properties: <code>lot_id</code>, <code>material_id</code>, <code>status</code> &bull; Edges: <code>SUPPLIED_BY</code>, <code>HAS_CERT</code>
          </p>
        </div>
        <div className="p-4 bg-panel border border-subtle rounded-md">
          <span className="font-mono text-[10px] text-dim uppercase">SPANNER GRAPH NODE</span>
          <h4 className="font-heading font-bold text-sm text-white mt-1">Calibration &amp; Handover</h4>
          <p className="text-xs text-secondary mt-1 font-sans">
            Properties: <code>skipped_step</code>, <code>rushed</code>, <code>notes</code> &bull; Edges: <code>DURING_HANDOVER</code>, <code>HANDOVER_FROM</code>
          </p>
        </div>
      </div>

      <ProvenanceDrawer nodeData={selectedNode} onClose={() => setSelectedNode(null)} />
    </div>
  );
}
