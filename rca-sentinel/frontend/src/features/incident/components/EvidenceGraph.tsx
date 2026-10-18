import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  Node,
  Edge,
  MarkerType,
  Position,
  Handle,
  NodeProps,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Package,
  Wrench,
  Factory,
  Cpu,
  Layers,
  RotateCcw,
  Eye,
  EyeOff,
  Info,
} from 'lucide-react';
import { useAppStore } from '../../../state/useAppStore';

export interface GraphNodeData {
  [key: string]: unknown;
  label: string;
  category: 'machine' | 'lot' | 'maintenance' | 'supplier' | 'assembly' | 'decoy';
  subLabel?: string;
  isCulprit?: boolean;
  isDecoy?: boolean;
  metric?: string;
  spec?: string;
  sourceSystem?: string;
  recordId?: string;
  evidenceHash?: string;
  whyItMatters?: string;
}

// ── Custom Node Renderers ────────────────────────────────────────────────────────

function EvidenceNodeRenderer({ data, selected }: NodeProps<Node<GraphNodeData>>) {
  const isCulprit = data.isCulprit;
  const isDecoy = data.isDecoy;

  return (
    <div
      className={`relative px-3.5 py-2.5 rounded border min-w-52 transition-all select-none shadow-md ${
        isCulprit
          ? 'bg-panel border-critical ring-2 ring-critical/50 shadow-critical/20'
          : isDecoy
          ? 'bg-raised/30 border-subtle/50 opacity-50'
          : selected
          ? 'bg-panel border-active ring-2 ring-active/40'
          : 'bg-panel border-subtle hover:border-strong'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-secondary !w-2 !h-2" />
      <Handle type="source" position={Position.Bottom} className="!bg-secondary !w-2 !h-2" />

      {/* Header Badge */}
      <div className="flex items-center justify-between mb-1">
        <span className="font-mono text-[9px] uppercase font-bold tracking-wider text-dim">
          {data.category}
        </span>
        {isCulprit && (
          <span className="px-1 py-0.2 rounded bg-critical text-white font-mono text-[9px] font-bold animate-pulse">
            ROOT CAUSE
          </span>
        )}
        {isDecoy && (
          <span className="px-1 py-0.2 rounded bg-raised text-dim font-mono text-[9px]">
            RULED OUT
          </span>
        )}
      </div>

      {/* Title */}
      <div className="font-heading font-bold text-xs text-primary leading-tight flex items-center gap-1.5">
        {data.category === 'machine' && <Cpu className="h-3.5 w-3.5 text-critical shrink-0" />}
        {data.category === 'lot' && <Package className="h-3.5 w-3.5 text-caution shrink-0" />}
        {data.category === 'maintenance' && <Wrench className="h-3.5 w-3.5 text-caution shrink-0" />}
        {data.category === 'supplier' && <Factory className="h-3.5 w-3.5 text-cobalt shrink-0" />}
        {data.category === 'assembly' && <Layers className="h-3.5 w-3.5 text-healthy shrink-0" />}
        <span className={isDecoy ? 'line-through text-secondary' : 'truncate'}>{data.label}</span>
      </div>

      {/* Sublabel / Metric */}
      {data.subLabel && (
        <div className="text-[11px] text-secondary mt-0.5 leading-tight truncate">
          {data.subLabel}
        </div>
      )}

      {/* Metrics Row */}
      {data.metric && (
        <div className="mt-1.5 pt-1 border-t border-subtle/60 flex items-center justify-between text-[10px] font-mono">
          <span className={isCulprit ? 'text-critical font-bold' : 'text-primary'}>
            {data.metric}
          </span>
          {data.spec && <span className="text-dim">Spec: {data.spec}</span>}
        </div>
      )}
    </div>
  );
}

// ── Initial Nodes & Edges for the Golden Scenario Evidence Graph ───────────────

const INITIAL_NODES: Node<GraphNodeData>[] = [
  // Tier 3 Supplier
  {
    id: 'n-supplier',
    type: 'evidenceNode',
    position: { x: 100, y: 30 },
    data: {
      label: 'AlloyTech Global (Vendor-8812)',
      category: 'supplier',
      subLabel: 'Tier-3 Raw Metallurgy Partner',
      metric: 'Historical PPM: 1,420',
      sourceSystem: 'SAP-MM Vendor Master',
      recordId: 'VEND-8812-US',
      evidenceHash: 'a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0',
      whyItMatters: 'Supplier Tier-3 provides un-audited structural bar stock used in Lot #40921.',
    },
  },
  // Culprit Material Lot
  {
    id: 'n-lot',
    type: 'evidenceNode',
    position: { x: 100, y: 150 },
    data: {
      label: 'Material Lot #40921',
      category: 'lot',
      subLabel: 'Structural Alloy A36 Mod (1,200kg)',
      isCulprit: true,
      metric: 'Silicon: 1.82%',
      spec: '<= 1.35%',
      sourceSystem: 'SAP-QM Spectrometry Log',
      recordId: 'LOT-REC-20240915-0012',
      evidenceHash: '8f9a2b71c4d5e89a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a',
      whyItMatters: '+34.8% excess silicon induces severe workpiece hardness and abrasive tool friction.',
    },
  },
  // Maintenance Crew
  {
    id: 'n-crew',
    type: 'evidenceNode',
    position: { x: 420, y: 30 },
    data: {
      label: 'Maintenance Crew B',
      category: 'maintenance',
      subLabel: 'Lead: J. Kowalski • Friday Shift B',
      metric: 'Handover: 4 mins (Rushed)',
      spec: '>= 15 mins standard',
      sourceSystem: 'Kronos Shift & Time Log',
      recordId: 'SHIFT-HANDOVER-20240915-B',
      evidenceHash: '5e6f7a8b9c0d1e2f3a8f9a2b71c4d5e89a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d',
      whyItMatters: 'Rushed handover led to skipping dynamic indicator calibration step on Station-03b.',
    },
  },
  // Skipped Calibration Step
  {
    id: 'n-calibration',
    type: 'evidenceNode',
    position: { x: 420, y: 150 },
    data: {
      label: 'Skipped Dynamic Tramming',
      category: 'maintenance',
      subLabel: 'Step 4.2 Spindle Dial Indicator Check',
      isCulprit: true,
      metric: 'Runout: 0.035 mm',
      spec: '+-0.010 mm',
      sourceSystem: 'Maximo CMMS Work Order #WO-88914',
      recordId: 'CMMS-WO-88914-TASK-02',
      evidenceHash: 'c4d5e6f7a8b9c0d1e2f3a8f9a2b71c4d5e89a0b1c2d3e4f5a6b7c8d9e0f1a2b3',
      whyItMatters: 'Spindle eccentricity (3.5x over tolerance) creates tool chatter under hard alloy feed.',
    },
  },
  // Failing Machine
  {
    id: 'n-machine',
    type: 'evidenceNode',
    position: { x: 260, y: 280 },
    data: {
      label: 'Machine Station-03B',
      category: 'machine',
      subLabel: 'Precision Spindle Assembly • Line 03',
      isCulprit: true,
      metric: 'Vibration: 4.82 mm/s • Temp: 78.4C',
      spec: '<= 2.2 mm/s',
      sourceSystem: 'Beckhoff PLC High-Speed Telemetry',
      recordId: 'PLC-LINE03-ST03B-SENSOR-VIB',
      evidenceHash: '7a8b9c0d1e2f3a8f9a2b71c4d5e89a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f',
      whyItMatters: 'Thermal warp of spindle bearing housing induces 12.2% dimensional scrap spike.',
    },
  },
  // Decoy 1: Tool Wear on 03A
  {
    id: 'n-decoy-tool',
    type: 'evidenceNode',
    position: { x: -160, y: 280 },
    data: {
      label: 'Station-03A Tool Wear (Decoy)',
      category: 'decoy',
      subLabel: 'Tool cycle count at 82% life limit',
      isDecoy: true,
      metric: 'Vibration: 1.9 mm/s (Nominal)',
      sourceSystem: 'Tool Management System (TMS)',
      recordId: 'TOOL-ST03A-CYC-992',
      evidenceHash: '2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a',
      whyItMatters: 'Ruled out: vibration signatures remained stable and did not propagate downstream.',
    },
  },
  // Downstream Affected Assemblies
  {
    id: 'n-assemblies',
    type: 'evidenceNode',
    position: { x: 260, y: 410 },
    data: {
      label: 'Affected Assemblies (Batch #40921)',
      category: 'assembly',
      subLabel: '420 Units at CMM Inspection Gate',
      metric: 'Scrap Rate: 12.2% • Exposure: $184.8k',
      sourceSystem: 'MES Job Tracking & CMM Station',
      recordId: 'MES-JOB-LINE03-BATCH-40921',
      evidenceHash: '1a2b3c4d5e6f7a8b9c0d1e2f3a8f9a2b71c4d5e89a0b1c2d3e4f5a6b7c8d9e0f',
      whyItMatters: 'Batches quarantined at CMM gate before dispatch to Tesla PO-9912.',
    },
  },
];

const INITIAL_EDGES: Edge[] = [
  {
    id: 'e-supplier-lot',
    source: 'n-supplier',
    target: 'n-lot',
    label: 'SUPPLIED_BY',
    animated: true,
    style: { stroke: '#4C8DFF', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#4C8DFF' },
  },
  {
    id: 'e-crew-calib',
    source: 'n-crew',
    target: 'n-calibration',
    label: 'CONDUCTED_BY',
    animated: true,
    style: { stroke: '#FFB000', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#FFB000' },
  },
  {
    id: 'e-lot-machine',
    source: 'n-lot',
    target: 'n-machine',
    label: 'CONSUMED_BY (COMPOUND CAUSE)',
    animated: true,
    style: { stroke: '#FF5A3C', strokeWidth: 3 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#FF5A3C' },
  },
  {
    id: 'e-calib-machine',
    source: 'n-calibration',
    target: 'n-machine',
    label: 'OCCURRED_ON',
    animated: true,
    style: { stroke: '#FF5A3C', strokeWidth: 3 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#FF5A3C' },
  },
  {
    id: 'e-decoy-machine',
    source: 'n-decoy-tool',
    target: 'n-machine',
    label: 'PART_TRANSFER (RULED OUT)',
    style: { stroke: '#2A4157', strokeDasharray: '4 4' },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#2A4157' },
  },
  {
    id: 'e-machine-assemblies',
    source: 'n-machine',
    target: 'n-assemblies',
    label: 'PRODUCED_ON',
    animated: true,
    style: { stroke: '#FF5A3C', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#FF5A3C' },
  },
];

interface EvidenceGraphProps {
  onSelectNode: (nodeData: GraphNodeData) => void;
  nodes?: Node<GraphNodeData>[];
  edges?: Edge[];
  customNodes?: Node<GraphNodeData>[];
  customEdges?: Edge[];
  isLoading?: boolean;
}

export function EvidenceGraph({
  onSelectNode,
  nodes: propNodes,
  edges: propEdges,
  customNodes,
  customEdges,
  isLoading,
}: EvidenceGraphProps) {
  const { theme } = useAppStore();
  const activeNodes = customNodes || propNodes;
  const activeEdges = customEdges || propEdges;
  const [nodes, setNodes] = useState<Node<GraphNodeData>[]>(activeNodes || INITIAL_NODES);
  const [edges, setEdges] = useState<Edge[]>(activeEdges || INITIAL_EDGES);
  const [dimDecoys, setDimDecoys] = useState(false);

  useEffect(() => {
    if (activeNodes) setNodes(activeNodes);
  }, [activeNodes]);

  useEffect(() => {
    if (activeEdges) setEdges(activeEdges);
  }, [activeEdges]);

  const nodeTypes = useMemo(() => ({ evidenceNode: EvidenceNodeRenderer }), []);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      onSelectNode(node.data as unknown as GraphNodeData);
    },
    [onSelectNode]
  );

  const toggleDimDecoys = () => {
    const nextDim = !dimDecoys;
    setDimDecoys(nextDim);
    setNodes((prev) =>
      prev.map((n) => {
        if (n.data.isDecoy) {
          return {
            ...n,
            style: { opacity: nextDim ? 0.15 : 0.5 },
          };
        }
        return n;
      })
    );
  };

  const resetLayout = () => {
    setNodes(customNodes || INITIAL_NODES);
    setEdges(customEdges || INITIAL_EDGES);
    setDimDecoys(false);
  };

  return (
    <div className="relative h-[480px] w-full bg-canvas border border-subtle rounded-md overflow-hidden">
      {isLoading && (
        <div className="absolute inset-0 z-20 bg-canvas/80 flex items-center justify-center backdrop-blur-sm">
          <div className="flex items-center gap-2 text-xs font-mono text-cobalt">
            <div className="h-4 w-4 border-2 border-cobalt border-t-transparent rounded-full animate-spin" />
            <span>Querying Cloud Spanner ISO GQL...</span>
          </div>
        </div>
      )}
      {/* Floating Toolbar Controls */}
      <div className="absolute top-3 left-3 z-10 flex items-center gap-2 bg-panel/90 border border-subtle px-3 py-1.5 rounded backdrop-blur-sm text-xs font-mono shadow-md">
        <button
          onClick={toggleDimDecoys}
          className={`flex items-center gap-1.5 px-2 py-1 rounded transition-colors ${
            dimDecoys ? 'bg-raised text-primary font-bold' : 'text-secondary hover:text-primary'
          }`}
          title="Dim Decoys [D]"
        >
          {dimDecoys ? <EyeOff className="h-3.5 w-3.5 text-caution" /> : <Eye className="h-3.5 w-3.5" />}
          <span>{dimDecoys ? 'Decoys Dimmed' : 'Dim Decoys'}</span>
        </button>

        <span className="text-subtle">|</span>

        <button
          onClick={resetLayout}
          className="flex items-center gap-1.5 px-2 py-1 rounded text-secondary hover:text-primary transition-colors"
          title="Reset Graph Layout"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          <span>Reset Layout</span>
        </button>

        <span className="text-subtle">|</span>

        <div className="flex items-center gap-2 text-[11px] text-dim">
          <span className="h-2 w-2 rounded-full bg-critical animate-ping" />
          <span>Compound Traversal Pulse Active</span>
        </div>
      </div>

      {/* React Flow Component */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={handleNodeClick}
        fitView
        attributionPosition="bottom-right"
        className="bg-canvas"
      >
        <Background color={theme === 'day' ? '#CBD5E1' : '#1C3044'} gap={18} size={1} />
        <Controls className="!bg-panel !border-subtle !text-primary fill-current" />
      </ReactFlow>

      {/* Bottom Graph Banner */}
      <div className="absolute bottom-3 left-3 right-3 z-10 bg-panel/90 border border-subtle px-3 py-2 rounded backdrop-blur-sm flex items-center justify-between text-xs font-mono">
        <div className="flex items-center gap-2">
          <Info className="h-4 w-4 text-cobalt shrink-0" />
          <span className="text-secondary">
            Click any node to view <strong>cryptographic provenance hash</strong> and raw ERP/CMMS source records.
          </span>
        </div>
        <span className="text-healthy font-bold">100% EVIDENCE GROUNDING CITATIONS</span>
      </div>
    </div>
  );
}
