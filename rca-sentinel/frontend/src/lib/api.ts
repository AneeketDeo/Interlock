/**
 * API client connecting the React frontend to the FastAPI backend and Cloud Spanner Graph.
 */

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'https://rca-sentinel-864573324943.asia-south1.run.app').replace(/\/+$/, '');

export interface HealthStatusResponse {
  status: 'ok' | 'degraded' | 'error';
  version: string;
  environment: string;
  checks?: {
    spanner_graph?: boolean;
    pubsub?: boolean;
    bigquery?: boolean;
    vertex_ai?: boolean;
    [key: string]: boolean | undefined;
  };
}

export interface GraphStatusResponse {
  status: string;
  cloud_provider: string;
  spanner_instance: string;
  spanner_database: string;
  graph_name: string;
  query_language: string;
  historian: {
    dataset: string;
    table: string;
    stream_topic: string;
  };
}

export interface SubgraphResponse {
  machine_id: string;
  nodes: Array<{ id: string; label: string; properties?: Record<string, any> }>;
  edges: Array<{ id: string; type: string; from_id: string; to_id: string; properties?: Record<string, any> }>;
  node_count: number;
  edge_count: number;
}

export async function fetchHealthStatus(): Promise<HealthStatusResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/health/ready`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchGraphStatus(): Promise<GraphStatusResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/graph/status`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchMachineSubgraph(machineId: string): Promise<SubgraphResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/graph/subgraph/${machineId}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchLotProvenance(lotId: string): Promise<any | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/graph/lot/${lotId}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function executeGqlQuery(query: string, parameters: Record<string, any> = {}): Promise<any[] | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/graph/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, parameters }),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export interface SpannerMachine {
  id: string;
  name: string;
  type: string;
  line_id: string;
}

export async function fetchMachines(): Promise<SpannerMachine[] | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/graph/machines`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export interface SpannerLot {
  lot_id: string;
  material_id: string;
  status: string;
  qty_kg: number;
  supplier_id?: string;
  supplier_name?: string;
  supplier_tier?: number;
  mill_cert_id?: string;
  heat_number?: string;
  hardness_hrc?: number;
  carbon_pct?: number;
  within_spec?: boolean;
  edge_flag?: string | null;
}

export async function fetchSpannerLots(): Promise<SpannerLot[] | null> {
  const query = `
  GRAPH FactoryGraph
  MATCH (lot:MaterialLot)
  OPTIONAL MATCH (lot)-[:SUPPLIED_BY]->(sup:Supplier)
  OPTIONAL MATCH (lot)-[:HAS_CERT]->(cert:MillCertificate)
  RETURN lot.lot_id AS lot_id,
         lot.material_id AS material_id,
         lot.status AS status,
         lot.qty_kg AS qty_kg,
         sup.supplier_id AS supplier_id,
         sup.name AS supplier_name,
         sup.tier AS supplier_tier,
         cert.mill_cert_id AS mill_cert_id,
         cert.heat_number AS heat_number,
         cert.hardness_hrc AS hardness_hrc,
         cert.carbon_pct AS carbon_pct,
         cert.within_spec AS within_spec,
         cert.edge_flag AS edge_flag
  `;
  const rows = await executeGqlQuery(query);
  if (!rows) return null;

  // Deduplicate by lot_id, prioritizing Tier 1 or highest tier supplier
  const map = new Map<string, SpannerLot>();
  for (const r of rows) {
    const existing = map.get(r.lot_id);
    if (!existing || (r.supplier_tier && (!existing.supplier_tier || r.supplier_tier < existing.supplier_tier))) {
      map.set(r.lot_id, r);
    }
  }
  return Array.from(map.values());
}

export async function fetchMaintenanceEvents(machineId?: string): Promise<any[] | null> {
  try {
    if (machineId) {
      const res = await fetch(`${API_BASE_URL}/api/v1/graph/maintenance/${machineId}`);
      if (!res.ok) return null;
      return await res.json();
    }
    const query = `
    GRAPH FactoryGraph
    MATCH (cal:Calibration)-[:CALIBRATED]->(m:Machine)
    OPTIONAL MATCH (cal)-[:DURING_HANDOVER]->(h:Handover)
    OPTIONAL MATCH (h)-[:HANDOVER_FROM]->(crew:Crew)
    RETURN m.machine_id AS machine_id,
           cal.calibration_id AS id,
           cal.steps_required AS steps_required,
           cal.steps_completed AS steps_completed,
           cal.skipped_step AS skipped_step,
           cal.duration_min AS duration_min,
           cal.recorded_result AS recorded_result,
           cal.verification_signed_off AS verification_signed_off,
           cal.started_at AS timestamp,
           h.rushed AS handover_rushed,
           h.notes AS handover_notes,
           crew.name AS crew_name
    ORDER BY cal.started_at DESC
    LIMIT 50
    `;
    return await executeGqlQuery(query);
  } catch {
    return null;
  }
}

