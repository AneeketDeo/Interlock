"""Cloud Spanner Graph and Live Topology API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.logging import get_logger
from app.graph.client import get_spanner_graph_client
from app.graph.queries.traversal import GraphTraversalQueries

router = APIRouter(prefix="/graph", tags=["Graph & Topology"])
logger = get_logger(__name__)


class GqlQueryRequest(BaseModel):
    query: str = Field(..., description="ISO GQL query to execute against Spanner Graph")
    parameters: dict[str, Any] = Field(default_factory=dict)


@router.get("/status")
async def get_graph_status() -> dict[str, Any]:
    """Get active Cloud Spanner Graph and BigQuery Historian topology status."""
    settings = get_settings()
    client = get_spanner_graph_client()
    is_healthy = await client.health_check()

    return {
        "status": "connected" if is_healthy else "disconnected",
        "cloud_provider": "Google Cloud Platform",
        "spanner_instance": settings.spanner_instance_id,
        "spanner_database": settings.spanner_database_id,
        "graph_name": settings.spanner_graph_name,
        "query_language": "ISO GQL",
        "historian": {
            "dataset": settings.bigquery_dataset,
            "table": settings.bigquery_table,
            "stream_topic": settings.pubsub_topic_id,
        },
    }


@router.get("/machines")
async def list_machines() -> list[dict[str, Any]]:
    """List machines in the FactoryGraph topology."""
    client = get_spanner_graph_client()
    query = """
    GRAPH FactoryGraph
    MATCH (m:Machine)
    RETURN m.machine_id AS id, m.name AS name, m.machine_type AS type, m.line_id AS line_id
    LIMIT 50
    """
    try:
        return await client.execute_gql(query)
    except Exception as exc:
        logger.warning("machines_query_fallback", error=str(exc))
        # Return fallback machine topology if Spanner offline
        return [
            {"id": "station-03b", "name": "Precision Spindle Station 03B", "type": "CNC_MILL", "line_id": "line-03"},
            {"id": "station-03a", "name": "Roughing Mill Station 03A", "type": "CNC_MILL", "line_id": "line-03"},
            {"id": "station-03c", "name": "Finishing Lathe Station 03C", "type": "LATHE", "line_id": "line-03"},
            {"id": "station-03d", "name": "CMM Inspection Gate", "type": "INSPECTION_CMM", "line_id": "line-03"},
        ]


def _format_subgraph(machine_id: str, subgraph: dict[str, Any]) -> dict[str, Any]:
    """Transform machine neighborhood dictionary into graph nodes and edges representation."""
    if not subgraph:
        return {
            "machine_id": machine_id,
            "nodes": [],
            "edges": [],
            "node_count": 0,
            "edge_count": 0,
            "neighborhood": {},
        }

    # If already formatted with nodes and edges
    if isinstance(subgraph.get("nodes"), list) and isinstance(subgraph.get("edges"), list):
        nodes = subgraph["nodes"]
        edges = subgraph["edges"]
        return {
            "machine_id": machine_id,
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "neighborhood": subgraph.get("neighborhood", subgraph),
        }

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_node_ids: set[str] = set()

    # 1. Machine node
    machine = subgraph.get("machine") or {}
    m_id = str(machine.get("id") or machine.get("machine_id") or machine_id)
    if m_id not in seen_node_ids:
        seen_node_ids.add(m_id)
        nodes.append({
            "id": m_id,
            "label": "Machine",
            "properties": machine,
        })

    # 2. ProductionLine node and CONTAINS_MACHINE edge
    line = subgraph.get("line")
    if line and isinstance(line, dict):
        l_id = str(line.get("id") or machine.get("line_id") or "line-03")
        if l_id not in seen_node_ids:
            seen_node_ids.add(l_id)
            nodes.append({
                "id": l_id,
                "label": "ProductionLine",
                "properties": line,
            })
        edges.append({
            "id": f"{l_id}-CONTAINS_MACHINE-{m_id}",
            "type": "CONTAINS_MACHINE",
            "from_id": l_id,
            "to_id": m_id,
            "properties": {},
        })

    # 3. Sensor nodes and HAS_SENSOR edges
    for sensor in subgraph.get("sensors", []):
        if not isinstance(sensor, dict):
            continue
        s_id = str(sensor.get("id") or sensor.get("sensor_id") or "")
        if not s_id:
            continue
        if s_id not in seen_node_ids:
            seen_node_ids.add(s_id)
            nodes.append({
                "id": s_id,
                "label": "Sensor",
                "properties": sensor,
            })
        edges.append({
            "id": f"{m_id}-HAS_SENSOR-{s_id}",
            "type": "HAS_SENSOR",
            "from_id": m_id,
            "to_id": s_id,
            "properties": {},
        })

    # 4. Maintenance / Calibration nodes and CALIBRATED edges
    for me in subgraph.get("maintenance_events", []):
        if not isinstance(me, dict):
            continue
        me_id = str(me.get("id") or me.get("calibration_id") or "")
        if not me_id:
            continue
        if me_id not in seen_node_ids:
            seen_node_ids.add(me_id)
            nodes.append({
                "id": me_id,
                "label": "MaintenanceEvent",
                "properties": me,
            })
        edges.append({
            "id": f"{me_id}-CALIBRATED-{m_id}",
            "type": "CALIBRATED",
            "from_id": me_id,
            "to_id": m_id,
            "properties": {},
        })

    # 5. Operator log nodes and HAS_OPERATOR_LOG edges
    for log in subgraph.get("operator_logs", []):
        if not isinstance(log, dict):
            continue
        log_id = str(log.get("id") or log.get("crew_id") or log.get("log_id") or "")
        if not log_id:
            continue
        if log_id not in seen_node_ids:
            seen_node_ids.add(log_id)
            nodes.append({
                "id": log_id,
                "label": "OperatorLog",
                "properties": log,
            })
        edges.append({
            "id": f"{m_id}-HAS_OPERATOR_LOG-{log_id}",
            "type": "HAS_OPERATOR_LOG",
            "from_id": m_id,
            "to_id": log_id,
            "properties": {},
        })

    # 6. Material lot nodes and PROCESSED edges (+ Supplier nodes & SUPPLIED_BY edges)
    for lot in subgraph.get("processed_lots", []):
        if not isinstance(lot, dict):
            continue
        lot_id = str(lot.get("id") or lot.get("lot_id") or "")
        if not lot_id:
            continue
        if lot_id not in seen_node_ids:
            seen_node_ids.add(lot_id)
            nodes.append({
                "id": lot_id,
                "label": "MaterialLot",
                "properties": lot,
            })
        edges.append({
            "id": f"{m_id}-PROCESSED-{lot_id}",
            "type": "PROCESSED",
            "from_id": m_id,
            "to_id": lot_id,
            "properties": {},
        })

        supplier = lot.get("supplier")
        if supplier and isinstance(supplier, dict) and (supplier.get("id") or supplier.get("supplier_id")):
            sup_id = str(supplier.get("id") or supplier.get("supplier_id"))
            if sup_id not in seen_node_ids:
                seen_node_ids.add(sup_id)
                nodes.append({
                    "id": sup_id,
                    "label": "Supplier",
                    "properties": supplier,
                })
            edges.append({
                "id": f"{sup_id}-SUPPLIED_BY-{lot_id}",
                "type": "SUPPLIED_BY",
                "from_id": sup_id,
                "to_id": lot_id,
                "properties": {},
            })

    return {
        "machine_id": machine_id,
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "neighborhood": subgraph,
    }


@router.get("/subgraph/{machine_id}")
async def get_subgraph(machine_id: str) -> dict[str, Any]:
    """Get 1-hop and 2-hop machine subgraph from Spanner Graph."""
    try:
        queries = GraphTraversalQueries()
        subgraph = await queries.get_machine_subgraph(machine_id)
        return _format_subgraph(machine_id, subgraph)
    except Exception as exc:
        logger.error("subgraph_error", machine_id=machine_id, error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/lot/{lot_id}")
async def get_lot_provenance(lot_id: str) -> dict[str, Any]:
    """Trace raw material lot provenance, supplier, and mill cert in Spanner Graph."""
    try:
        queries = GraphTraversalQueries()
        return await queries.trace_lot_provenance(lot_id)
    except Exception as exc:
        logger.error("provenance_error", lot_id=lot_id, error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/maintenance/{machine_id}")
async def get_maintenance(machine_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Query recent calibrations and handovers for a machine."""
    try:
        queries = GraphTraversalQueries()
        return await queries.find_recent_maintenance(machine_id, limit=limit)
    except Exception as exc:
        logger.error("maintenance_error", machine_id=machine_id, error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/query")
async def execute_ad_hoc_gql(req: GqlQueryRequest) -> list[dict[str, Any]]:
    """Execute parameterized ISO GQL query against Spanner Graph."""
    client = get_spanner_graph_client()
    try:
        return await client.execute_gql(req.query, parameters=req.parameters)
    except Exception as exc:
        logger.error("ad_hoc_gql_failed", query=req.query, error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
