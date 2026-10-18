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
        lot_key = lot_id.strip()
        # Resolve common demo alias lot-40921 / 40921 -> LOT-409 (planted culprit in Spanner)
        if lot_key.lower().replace("-", "").replace("#", "") in ("lot40921", "40921"):
            lot_key = "LOT-409"

        query = """
        GRAPH FactoryGraph
        MATCH (target:MaterialLot)
        WHERE UPPER(target.lot_id) = UPPER(@lot_id)
        OPTIONAL MATCH (target)-[:SUPPLIED_BY]->(target_sup:Supplier)
        OPTIONAL MATCH (target)-[:HAS_CERT]->(cert:MillCertificate)
        OPTIONAL MATCH (upstream_sup:Supplier)-[:SUPPLIES]->(target_sup)
        RETURN target.lot_id AS lot_id,
               target.material_id AS material_id,
               target.qty_kg AS qty_kg,
               target.status AS status,
               target_sup.supplier_id AS supplier_id,
               target_sup.name AS supplier_name,
               target_sup.tier AS supplier_tier,
               cert.mill_cert_id AS mill_cert_id,
               cert.heat_number AS heat_number,
               cert.hardness_hrc AS hardness_hrc,
               cert.carbon_pct AS carbon_pct,
               cert.within_spec AS cert_within_spec,
               cert.edge_flag AS cert_edge_flag,
               upstream_sup.supplier_id AS upstream_supplier_id,
               upstream_sup.name AS upstream_supplier_name,
               upstream_sup.tier AS upstream_supplier_tier
        """
        records = await self.client.execute_gql(
            query,
            parameters={"lot_id": lot_key},
            param_types_map={"lot_id": param_types.STRING},
        )
        if not records:
            return {"target_lot": None, "upstream_lots": [], "total_hops": 0}

        first = records[0]
        cert_props = {
            "hardness_hrc": first.get("hardness_hrc"),
            "carbon_pct": first.get("carbon_pct"),
            "within_spec": first.get("cert_within_spec"),
            "edge_flag": first.get("cert_edge_flag"),
            "heat_number": first.get("heat_number"),
        }

        target_lot = {
            "id": first.get("lot_id"),
            "lot_id": first.get("lot_id"),
            "material_id": first.get("material_id"),
            "qty_kg": first.get("qty_kg"),
            "status": first.get("status"),
            "properties": cert_props,
            "mill_certificate": cert_props,
            "supplier": {
                "id": first.get("supplier_id"),
                "name": first.get("supplier_name"),
                "tier": first.get("supplier_tier"),
            } if first.get("supplier_name") else None,
        }

        upstream_lots = [target_lot]
        if first.get("upstream_supplier_id"):
            upstream_lots.append({
                "id": f"lot-upstream-{first.get('upstream_supplier_id')}",
                "supplier": {
                    "id": first.get("upstream_supplier_id"),
                    "name": first.get("upstream_supplier_name"),
                    "tier": first.get("upstream_supplier_tier"),
                },
            })

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
        """ISO GQL machine subgraph query using exact ontology labels from spanner_schema_backup.sql."""
        machine_key = machine_id.strip()
        # Resolve demo alias station-03b -> M12
        if machine_key.lower().replace("-", "").replace("_", "") in ("station03b", "stn03b"):
            machine_key = "M12"

        query = """
        GRAPH FactoryGraph
        MATCH (m:Machine)
        WHERE UPPER(m.machine_id) = UPPER(@machine_id)
        OPTIONAL MATCH (m)-[:HAS_SENSOR]->(s:Sensor)
        OPTIONAL MATCH (m)-[:PROCESSED]->(lot:MaterialLot)
        OPTIONAL MATCH (lot)-[:SUPPLIED_BY]->(sup:Supplier)
        OPTIONAL MATCH (lot)-[:HAS_CERT]->(cert:MillCertificate)
        OPTIONAL MATCH (cal:Calibration)-[:CALIBRATED]->(m)
        OPTIONAL MATCH (cal)-[:DURING_HANDOVER]->(h:Handover)
        OPTIONAL MATCH (h)-[:HANDOVER_FROM]->(crew:Crew)
        RETURN m.machine_id AS machine_id, m.name AS machine_name, m.machine_type AS machine_type, m.line_id AS line_id,
               s.sensor_id AS sensor_id, s.sensor_type AS sensor_type, s.unit AS sensor_unit,
               lot.lot_id AS lot_id, lot.material_id AS material_id, lot.status AS lot_status,
               sup.supplier_id AS supplier_id, sup.name AS supplier_name, sup.tier AS supplier_tier,
               cert.mill_cert_id AS mill_cert_id, cert.within_spec AS cert_within_spec, cert.edge_flag AS cert_edge_flag,
               cal.calibration_id AS calibration_id, cal.steps_required AS steps_required,
               cal.steps_completed AS steps_completed, cal.skipped_step AS skipped_step,
               cal.duration_min AS duration_min, cal.verification_signed_off AS verification_signed_off,
               cal.recorded_result AS recorded_result,
               h.handover_id AS handover_id, h.rushed AS handover_rushed, h.notes AS handover_notes,
               crew.crew_id AS crew_id, crew.name AS crew_name
        """
        records = await self.client.execute_gql(
            query,
            parameters={"machine_id": machine_key},
            param_types_map={"machine_id": param_types.STRING},
        )
        if not records:
            return {}

        first = records[0]
        machine = {
            "id": first.get("machine_id"),
            "machine_id": first.get("machine_id"),
            "name": first.get("machine_name"),
            "machine_type": first.get("machine_type"),
            "line_id": first.get("line_id"),
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
                    "tag": r.get("sensor_id"),
                    "sensor_type": r.get("sensor_type"),
                    "unit": r.get("sensor_unit"),
                })
            if r.get("calibration_id") and r["calibration_id"] not in seen_cal:
                seen_cal.add(r["calibration_id"])
                maintenance.append({
                    "id": r["calibration_id"],
                    "title": f"Calibration on {r.get('machine_name', machine_id)}",
                    "steps_required": r.get("steps_required"),
                    "steps_completed": r.get("steps_completed"),
                    "skipped_step": r.get("skipped_step"),
                    "duration_min": r.get("duration_min"),
                    "verification_signed_off": r.get("verification_signed_off"),
                    "recorded_result": r.get("recorded_result"),
                    "crew_name": r.get("crew_name"),
                    "handover_rushed": r.get("handover_rushed"),
                })
            if r.get("crew_id") and r["crew_id"] not in seen_crew:
                seen_crew.add(r["crew_id"])
                logs.append({
                    "id": r["crew_id"],
                    "crew_name": r.get("crew_name"),
                    "text": r.get("handover_notes") or f"Handover notes for {r.get('crew_name')}",
                    "rushed": r.get("handover_rushed"),
                })
            if r.get("lot_id") and r["lot_id"] not in seen_ml:
                seen_ml.add(r["lot_id"])
                lots.append({
                    "id": r["lot_id"],
                    "lot_id": r.get("lot_id"),
                    "material_id": r.get("material_id"),
                    "status": r.get("lot_status"),
                    "mill_cert_id": r.get("mill_cert_id"),
                    "within_spec": r.get("cert_within_spec"),
                    "supplier": {
                        "id": r.get("supplier_id"),
                        "name": r.get("supplier_name"),
                        "tier": r.get("supplier_tier"),
                    },
                })

        return {
            "machine": machine,
            "line": {"id": first.get("line_id", "line-03"), "name": "Assembly Line 03"},
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
        machine_key = machine_id.strip()
        if machine_key.lower().replace("-", "").replace("_", "") in ("station03b", "stn03b"):
            machine_key = "M12"

        if isinstance(self.client, SpannerGraphClient):
            query = """
            GRAPH FactoryGraph
            MATCH (cal:Calibration)-[:CALIBRATED]->(m:Machine)
            WHERE UPPER(m.machine_id) = UPPER(@machine_id)
            OPTIONAL MATCH (cal)-[:DURING_HANDOVER]->(h:Handover)
            OPTIONAL MATCH (h)-[:HANDOVER_FROM]->(crew:Crew)
            RETURN cal.calibration_id AS id,
                   cal.steps_required AS steps_required,
                   cal.steps_completed AS steps_completed,
                   cal.skipped_step AS skipped_step,
                   cal.duration_min AS duration_min,
                   cal.recorded_result AS recorded_result,
                   cal.verification_signed_off AS verification_signed_off,
                   cal.started_at AS timestamp,
                   h.rushed AS handover_rushed,
                   h.notes AS handover_notes,
                   crew.crew_id AS crew_id,
                   crew.name AS crew_name
            ORDER BY cal.started_at DESC
            LIMIT @limit
            """
            return await self.client.execute_gql(
                query,
                parameters={"machine_id": machine_key, "limit": limit},
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
            MATCH (cal:Calibration)-[:CALIBRATED]->(m:Machine)
            WHERE m.machine_id = @machine_id
            MATCH (cal)-[:DURING_HANDOVER]->(h:Handover)
            OPTIONAL MATCH (h)-[:HANDOVER_FROM]->(crew:Crew)
            RETURN h.handover_id AS id,
                   h.notes AS text,
                   h.rushed AS rushed,
                   h.handover_time AS timestamp,
                   crew.name AS crew_name
            ORDER BY h.handover_time DESC
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
