"""Multi-hop ISO GQL traversal queries for Google Cloud Spanner Graph."""

from __future__ import annotations

import json
from typing import Any

from google.cloud.spanner_v1 import param_types

from app.core.config import get_settings
from app.graph.cache import cached_graph_query
from app.graph.client import (
    Neo4jClient,
    SpannerGraphClient,
    get_neo4j_client,
    get_spanner_graph_client,
)


class GraphTraversalQueries:
    """Traverses manufacturing ontology graphs to discover multi-hop causal chains.

    Supports native Google Cloud Spanner Graph (ISO GQL) and Neo4j Cypher.
    """

    def __init__(
        self, client: SpannerGraphClient | Neo4jClient | None = None
    ) -> None:
        self._client = client

    @property
    def client(self) -> SpannerGraphClient | Neo4jClient:
        if self._client is not None:
            return self._client
        settings = get_settings()
        # Default to SpannerGraphClient for native GCP, fallback if Neo4j explicitly configured
        if hasattr(settings, "spanner_database_id") and settings.spanner_database_id:
            try:
                return get_spanner_graph_client()
            except Exception:
                pass
        return get_neo4j_client()

    @cached_graph_query(ttl_seconds=30)
    async def trace_lot_provenance(self, lot_id: str) -> dict[str, Any]:
        """Multi-hop backward traversal: traces MaterialLot upstream through suppliers."""
        if isinstance(self.client, SpannerGraphClient):
            return await self._trace_lot_provenance_spanner(lot_id)
        return await self._trace_lot_provenance_neo4j(lot_id)

    async def _trace_lot_provenance_spanner(self, lot_id: str) -> dict[str, Any]:
        """ISO GQL multi-hop supplier provenance traversal matching exact FactoryGraph ontology."""
        query = """
        GRAPH FactoryGraph
        MATCH (target:MaterialLot {id: @lot_id})
        OPTIONAL MATCH (target_sup:Supplier)-[:SUPPLIED_BY]->(target)
        RETURN target.id AS target_id,
               target.lot_number AS target_lot_number,
               target.material_type AS target_material_type,
               target.silicon_content_pct AS target_silicon_pct,
               target.properties AS target_properties,
               target_sup.id AS target_sup_id,
               target_sup.name AS target_supplier,
               target_sup.tier AS target_sup_tier
        """
        records = await self.client.execute_gql(
            query,
            parameters={"lot_id": lot_id},
            param_types_map={"lot_id": param_types.STRING},
        )
        if not records:
            return {"target_lot": None, "upstream_lots": [], "total_hops": 0}

        first = records[0]
        target_props = first.get("target_properties")
        if isinstance(target_props, str):
            try:
                target_props = json.loads(target_props)
            except Exception:
                pass
        if not target_props and first.get("target_silicon_pct") is not None:
            target_props = {"silicon_content_pct": first.get("target_silicon_pct")}

        target_lot = {
            "id": first.get("target_id"),
            "lot_number": first.get("target_lot_number"),
            "material_type": first.get("target_material_type"),
            "properties": target_props,
            "supplier": {
                "id": first.get("target_sup_id"),
                "name": first.get("target_supplier"),
                "tier": first.get("target_sup_tier"),
            } if first.get("target_supplier") else None,
        }

        upstream_lots = []
        seen = set()
        for r in records:
            uid = r.get("target_id")
            if uid and uid not in seen:
                seen.add(uid)
                upstream_lots.append(target_lot)

        return {
            "target_lot": target_lot,
            "upstream_lots": upstream_lots,
            "total_hops": len(upstream_lots),
        }

    async def _trace_lot_provenance_neo4j(self, lot_id: str) -> dict[str, Any]:
        query = """
        MATCH (target:MaterialLot {id: $lot_id})
        OPTIONAL MATCH (target_sup:Supplier)-[:SUPPLIED_LOT]->(target)
        OPTIONAL MATCH path = (target)-[:CONSUMED_LOT*1..6]->(upstream:MaterialLot)
        OPTIONAL MATCH (upstream_sup:Supplier)-[:SUPPLIED_LOT]->(upstream)
        WITH target, target_sup,
             collect(DISTINCT upstream {
                 .*,
                 supplier: upstream_sup {.*}
             }) AS upstream_chain
        RETURN {
            target_lot: target {.*, supplier: target_sup {.*}},
            upstream_lots: upstream_chain,
            total_hops: size(upstream_chain)
        } AS provenance
        """
        records = await self.client.execute_read(query, {"lot_id": lot_id})
        if records and records[0].get("provenance"):
            return records[0]["provenance"]  # type: ignore[no-any-return]
        return {"target_lot": None, "upstream_lots": [], "total_hops": 0}

    @cached_graph_query(ttl_seconds=30)
    async def get_machine_subgraph(self, machine_id: str) -> dict[str, Any]:
        """Get 2-hop neighborhood around a machine: line, sensors, maintenance, logs, and lots."""
        if isinstance(self.client, SpannerGraphClient):
            return await self._get_machine_subgraph_spanner(machine_id)
        return await self._get_machine_subgraph_neo4j(machine_id)

    async def _get_machine_subgraph_spanner(self, machine_id: str) -> dict[str, Any]:
        """ISO GQL machine subgraph query using exact ontology labels."""
        query = """
        GRAPH FactoryGraph
        MATCH (m:Machine {id: @machine_id})
        OPTIONAL MATCH (s:Sensor)
        OPTIONAL MATCH (ml:MaterialLot)-[:PROCESSED_ON]->(m)
        OPTIONAL MATCH (sup:Supplier)-[:SUPPLIED_BY]->(ml)
        OPTIONAL MATCH (crew:Crew)-[:MAINTAINED_BY]->(m)
        OPTIONAL MATCH (cal:Calibration)-[:CALIBRATED]->(m)
        RETURN m.id AS machine_id, m.name AS machine_name, m.code AS machine_code, m.machine_type AS machine_type,
               s.id AS sensor_id, s.tag AS sensor_tag, s.sensor_type AS sensor_type,
               ml.id AS ml_id, ml.lot_number AS ml_lot_number, ml.material_type AS ml_material_type,
               ml.silicon_content_pct AS ml_silicon_pct, ml.properties AS ml_props,
               sup.id AS sup_id, sup.name AS sup_name, sup.tier AS sup_tier,
               crew.id AS crew_id, crew.name AS crew_name, crew.shift AS crew_shift,
               cal.id AS cal_id, cal.offset_mm AS calibration_offset_mm, cal.tolerance_mm AS tolerance_limit_mm,
               cal.status AS cal_status, cal.notes AS cal_notes, cal.timestamp AS cal_timestamp
        """
        records = await self.client.execute_gql(
            query,
            parameters={"machine_id": machine_id},
            param_types_map={"machine_id": param_types.STRING},
        )
        if not records:
            return {}

        first = records[0]
        machine = {
            "id": first.get("machine_id"),
            "name": first.get("machine_name"),
            "code": first.get("machine_code"),
            "machine_type": first.get("machine_type"),
        }

        sensors = []
        maintenance = []
        logs = []
        lots = []
        seen_s, seen_cal, seen_crew, seen_ml = set(), set(), set(), set()

        for r in records:
            if r.get("sensor_id") and r["sensor_id"] not in seen_s:
                seen_s.add(r["sensor_id"])
                sensors.append({
                    "id": r["sensor_id"],
                    "tag": r.get("sensor_tag"),
                    "sensor_type": r.get("sensor_type"),
                })
            if r.get("cal_id") and r["cal_id"] not in seen_cal:
                seen_cal.add(r["cal_id"])
                maintenance.append({
                    "id": r["cal_id"],
                    "title": f"Calibration on {r.get('machine_name', machine_id)}",
                    "calibration_offset_mm": r.get("calibration_offset_mm"),
                    "tolerance_limit_mm": r.get("tolerance_limit_mm"),
                    "status": r.get("cal_status"),
                    "notes": r.get("cal_notes"),
                    "timestamp": str(r.get("cal_timestamp")),
                    "crew_name": r.get("crew_name"),
                })
            if r.get("crew_id") and r["crew_id"] not in seen_crew:
                seen_crew.add(r["crew_id"])
                logs.append({
                    "id": r["crew_id"],
                    "crew_name": r.get("crew_name"),
                    "shift": r.get("crew_shift"),
                    "text": f"Shift {r.get('crew_shift')} maintenance handover by {r.get('crew_name')}",
                })
            if r.get("ml_id") and r["ml_id"] not in seen_ml:
                seen_ml.add(r["ml_id"])
                lots.append({
                    "id": r["ml_id"],
                    "lot_number": r.get("ml_lot_number"),
                    "material_type": r.get("ml_material_type"),
                    "silicon_content_pct": r.get("ml_silicon_pct"),
                    "supplier": {
                        "id": r.get("sup_id"),
                        "name": r.get("sup_name"),
                        "tier": r.get("sup_tier"),
                    },
                })

        return {
            "machine": machine,
            "line": {"id": "line-03", "name": "Assembly Line 03"},
            "sensors": sensors,
            "maintenance_events": maintenance,
            "operator_logs": logs,
            "processed_lots": lots,
        }

    async def _get_machine_subgraph_neo4j(self, machine_id: str) -> dict[str, Any]:
        query = """
        MATCH (m:Machine {id: $machine_id})
        OPTIONAL MATCH (l:ProductionLine)-[:CONTAINS_MACHINE]->(m)
        OPTIONAL MATCH (m)-[:HAS_SENSOR]->(s:Sensor)
        OPTIONAL MATCH (m)-[:HAS_MAINTENANCE_EVENT]->(me:MaintenanceEvent)
        OPTIONAL MATCH (m)-[:HAS_OPERATOR_LOG]->(ol:OperatorLog)
        OPTIONAL MATCH (m)-[:PROCESSED_LOT]->(ml:MaterialLot)
        OPTIONAL MATCH (sup:Supplier)-[:SUPPLIED_LOT]->(ml)
        RETURN {
            machine: m {.*},
            line: l {.*},
            sensors: collect(DISTINCT s {.*}),
            maintenance_events: collect(DISTINCT me {.*}),
            operator_logs: collect(DISTINCT ol {.*}),
            processed_lots: collect(DISTINCT ml {.*, supplier: sup {.*}})
        } AS neighborhood
        """
        records = await self.client.execute_read(query, {"machine_id": machine_id})
        if records and records[0].get("neighborhood"):
            return records[0]["neighborhood"]  # type: ignore[no-any-return]
        return {}

    @cached_graph_query(ttl_seconds=30)
    async def find_recent_maintenance(
        self, machine_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Find recent maintenance events and calibration offsets for a machine."""
        if isinstance(self.client, SpannerGraphClient):
            query = """
            GRAPH FactoryGraph
            MATCH (cal:Calibration)-[:CALIBRATED]->(m:Machine {id: @machine_id})
            OPTIONAL MATCH (crew:Crew)-[:MAINTAINED_BY]->(m)
            RETURN cal.id AS id,
                   cal.offset_mm AS calibration_offset_mm,
                   cal.tolerance_mm AS tolerance_limit_mm,
                   cal.status AS status,
                   cal.notes AS notes,
                   cal.timestamp AS timestamp,
                   crew.id AS crew_id,
                   crew.name AS crew_name,
                   crew.shift AS shift
            ORDER BY cal.timestamp DESC
            LIMIT @limit
            """
            return await self.client.execute_gql(
                query,
                parameters={"machine_id": machine_id, "limit": limit},
                param_types_map={
                    "machine_id": param_types.STRING,
                    "limit": param_types.INT64,
                },
            )

        query = """
        MATCH (m:Machine {id: $machine_id})-[:HAS_MAINTENANCE_EVENT]->(me:MaintenanceEvent)
        RETURN me {.*} AS event
        ORDER BY me.timestamp DESC
        LIMIT $limit
        """
        records = await self.client.execute_read(
            query, {"machine_id": machine_id, "limit": limit}
        )
        return [r["event"] for r in records]

    @cached_graph_query(ttl_seconds=30)
    async def find_operator_logs(
        self, machine_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Find operator shift notes for a machine."""
        if isinstance(self.client, SpannerGraphClient):
            query = """
            GRAPH FactoryGraph
            MATCH (crew:Crew)-[:MAINTAINED_BY]->(m:Machine {id: @machine_id})
            RETURN crew.id AS id,
                   crew.name AS name,
                   crew.shift AS shift_number,
                   crew.notes AS text,
                   crew.timestamp AS timestamp
            ORDER BY crew.timestamp DESC
            LIMIT @limit
            """
            return await self.client.execute_gql(
                query,
                parameters={"machine_id": machine_id, "limit": limit},
                param_types_map={
                    "machine_id": param_types.STRING,
                    "limit": param_types.INT64,
                },
            )

        query = """
        MATCH (m:Machine {id: $machine_id})-[:HAS_OPERATOR_LOG]->(ol:OperatorLog)
        RETURN ol {.*} AS log
        ORDER BY ol.timestamp DESC
        LIMIT $limit
        """
        records = await self.client.execute_read(
            query, {"machine_id": machine_id, "limit": limit}
        )
        return [r["log"] for r in records]
