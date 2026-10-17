"""Backward analysis and commonality scoring across multi-silo manufacturing graph."""

from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.graph.client import (
    Neo4jClient,
    SpannerGraphClient,
    get_neo4j_client,
    get_spanner_graph_client,
)

logger = get_logger(__name__)


class BackwardAnalysisEngine:
    """Performs multi-hop backward reasoning from an anomaly to identify root causes."""

    def __init__(
        self, client: SpannerGraphClient | Neo4jClient | None = None
    ) -> None:
        self._client = client

    @property
    def client(self) -> SpannerGraphClient | Neo4jClient:
        if self._client is not None:
            return self._client
        settings = get_settings()
        if hasattr(settings, "spanner_database_id") and settings.spanner_database_id:
            try:
                return get_spanner_graph_client()
            except Exception:
                pass
        return get_neo4j_client()

    async def analyze_incident(
        self,
        line_id: str = "line-03",
        machine_id: str = "station-03b",
    ) -> dict[str, Any]:
        """Perform comprehensive backward traversal to diagnose root cause."""
        logger.info("backward_analysis_started", line_id=line_id, machine_id=machine_id)

        if isinstance(self.client, SpannerGraphClient):
            return await self._analyze_incident_spanner(line_id=line_id, machine_id=machine_id)
        return await self._analyze_incident_neo4j(line_id=line_id, machine_id=machine_id)

    async def _analyze_incident_spanner(
        self,
        line_id: str,
        machine_id: str,
    ) -> dict[str, Any]:
        """Execute multi-hop ISO GQL finding the intersection of MaterialLot and Crew on Machine."""
        from google.cloud.spanner_v1 import param_types

        gql_query = """
        GRAPH FactoryGraph
        MATCH (lot:MaterialLot)-[:PROCESSED_ON]->(m:Machine {id: @machine_id})
        MATCH (crew:Crew)-[:MAINTAINED_BY]->(m)
        OPTIONAL MATCH (cal:Calibration)-[:CALIBRATED]->(m)
        OPTIONAL MATCH (sup:Supplier)-[:SUPPLIED_BY]->(lot)
        RETURN m.id AS machine_id,
               m.name AS machine_name,
               crew.id AS crew_id,
               crew.name AS crew_name,
               crew.shift AS crew_shift,
               crew.notes AS crew_notes,
               cal.id AS calibration_id,
               cal.offset_mm AS calibration_offset_mm,
               cal.tolerance_mm AS tolerance_limit_mm,
               cal.status AS calibration_status,
               cal.notes AS calibration_notes,
               lot.id AS culprit_lot_id,
               lot.lot_number AS culprit_lot_number,
               lot.material_type AS material_type,
               lot.silicon_content_pct AS silicon_content_pct,
               lot.properties AS culprit_properties,
               sup.id AS supplier_id,
               sup.name AS supplier_name,
               sup.tier AS supplier_tier
        """
        records = await self.client.execute_gql(
            gql_query,
            parameters={"machine_id": machine_id},
            param_types_map={"machine_id": param_types.STRING},
        )

        suspicious_maintenance: list[dict[str, Any]] = []
        culprit_material_lots: list[dict[str, Any]] = []
        relevant_operator_logs: list[dict[str, Any]] = []
        seen_events: set[str] = set()
        seen_lots: set[str] = set()
        seen_crews: set[str] = set()

        for row in records:
            ev_id = row.get("calibration_id")
            if ev_id and ev_id not in seen_events:
                seen_events.add(ev_id)
                offset = float(row.get("calibration_offset_mm") or 0.0)
                tol = float(row.get("tolerance_limit_mm") or 0.010)
                status = str(row.get("calibration_status") or "")
                if offset > tol or status.upper() in ["SKIPPED", "OUT_OF_SPEC"]:
                    suspicious_maintenance.append({
                        "event_id": ev_id,
                        "title": f"Calibration on {row.get('machine_name', machine_id)}",
                        "technician_name": row.get("crew_name"),
                        "crew_name": row.get("crew_name"),
                        "calibration_offset_mm": offset,
                        "tolerance_limit_mm": tol,
                        "status": status,
                        "exceeded_by_pct": round(((offset - tol) / tol) * 100, 1) if tol else 0.0,
                        "notes": row.get("calibration_notes"),
                    })

            lot_id = row.get("culprit_lot_id")
            if lot_id and lot_id not in seen_lots:
                seen_lots.add(lot_id)
                props_raw = row.get("culprit_properties") or {}
                if isinstance(props_raw, str):
                    try:
                        props_raw = json.loads(props_raw)
                    except Exception:
                        props_raw = {}
                si_pct = float(row.get("silicon_content_pct") or props_raw.get("silicon_content_pct", 0.0))
                if not props_raw and si_pct:
                    props_raw = {"silicon_content_pct": si_pct}
                if props_raw.get("out_of_spec") or si_pct > 1.35:
                    culprit_material_lots.append({
                        "lot_id": lot_id,
                        "lot_number": row.get("culprit_lot_number"),
                        "supplier": {
                            "id": row.get("supplier_id"),
                            "name": row.get("supplier_name"),
                            "tier": row.get("supplier_tier"),
                        },
                        "properties": props_raw,
                        "material_type": row.get("material_type"),
                        "silicon_content_pct": si_pct,
                    })

            crew_id = row.get("crew_id")
            if crew_id and crew_id not in seen_crews:
                seen_crews.add(crew_id)
                text = str(row.get("crew_notes") or f"Shift handover by {row.get('crew_name')} (Shift {row.get('crew_shift')})")
                relevant_operator_logs.append({
                    "id": crew_id,
                    "crew_name": row.get("crew_name"),
                    "shift": row.get("crew_shift"),
                    "text": text,
                })

        hypotheses: list[dict[str, Any]] = []
        if suspicious_maintenance and culprit_material_lots:
            crew_name = suspicious_maintenance[0].get("crew_name", "Maintenance Crew")
            lot_num = culprit_material_lots[0].get("lot_number", "40921")
            si_val = culprit_material_lots[0].get("silicon_content_pct", 1.82)
            sup_name = culprit_material_lots[0].get("supplier", {}).get("name", "Tier-3 Vendor")
            hypotheses.append({
                "type": "compound_failure",
                "confidence": 0.98,
                "title": "Spindle Bearing Miscalibration Compounded by Out-of-Spec Alloy Lot",
                "primary_cause": suspicious_maintenance[0],
                "compounding_cause": culprit_material_lots[0],
                "operator_corroboration": relevant_operator_logs,
                "description": (
                    f"Spanner Graph ISO GQL identified intersection on Machine {machine_id}: "
                    f"Calibration offset (+{suspicious_maintenance[0]['calibration_offset_mm']}mm vs ±{suspicious_maintenance[0]['tolerance_limit_mm']}mm) "
                    f"during rushed handover by {crew_name} compounded by out-of-spec hard alloy Lot #{lot_num} "
                    f"({si_val}% Si from {sup_name}), inducing excessive tool chatter and thermal runaway."
                ),
            })
        elif suspicious_maintenance:
            hypotheses.append({
                "type": "mechanical_miscalibration",
                "confidence": 0.85,
                "title": "Spindle Runout Miscalibration",
                "cause": suspicious_maintenance[0],
            })

        return {
            "machine_id": machine_id,
            "line_id": line_id,
            "station_data": {"machine": {"id": machine_id}},
            "suspicious_maintenance": suspicious_maintenance,
            "culprit_lots": culprit_material_lots,
            "relevant_operator_logs": relevant_operator_logs,
            "hypotheses": hypotheses,
        }

    async def _analyze_incident_neo4j(
        self,
        line_id: str,
        machine_id: str,
    ) -> dict[str, Any]:
        """Execute legacy Cypher queries on Neo4j."""
        # 1. Inspect Station B Neighborhood
        machine_query = """
        MATCH (m:Machine {id: $machine_id})
        OPTIONAL MATCH (m)-[:HAS_MAINTENANCE_EVENT]->(me:MaintenanceEvent)
        OPTIONAL MATCH (m)-[:HAS_OPERATOR_LOG]->(ol:OperatorLog)
        OPTIONAL MATCH (m)-[:PROCESSED_LOT]->(ml:MaterialLot)
        RETURN {
            machine: m {.*},
            maintenance_events: collect(DISTINCT me {.*}),
            operator_logs: collect(DISTINCT ol {.*}),
            processed_lots: collect(DISTINCT ml {.*})
        } AS data
        """
        records = await self.client.execute_read(machine_query, {"machine_id": machine_id})
        station_data = records[0]["data"] if records else {}

        # 2. Upstream multi-hop provenance for processed lots
        processed_lots = station_data.get("processed_lots", [])
        lineage_chains: list[dict[str, Any]] = []

        for p_lot in processed_lots:
            lot_id = p_lot.get("id")
            if not lot_id:
                continue

            chain_query = """
            MATCH (target:MaterialLot {id: $lot_id})
            OPTIONAL MATCH (target_sup:Supplier)-[:SUPPLIED_LOT]->(target)
            OPTIONAL MATCH (target)-[:CONSUMED_LOT*1..5]->(upstream:MaterialLot)
            OPTIONAL MATCH (upstream_sup:Supplier)-[:SUPPLIED_LOT]->(upstream)
            WITH target, target_sup,
                 collect(DISTINCT upstream {
                     .*,
                     supplier: upstream_sup {.*}
                 }) AS upstream_lots
            RETURN {
                target: target {.*, supplier: target_sup {.*}},
                upstream_lots: upstream_lots
            } AS chain
            """
            chain_records = await self.client.execute_read(chain_query, {"lot_id": lot_id})
            if chain_records and chain_records[0].get("chain"):
                lineage_chains.append(chain_records[0]["chain"])

        # 3. Analyze maintenance events for anomalies
        suspicious_maintenance: list[dict[str, Any]] = []
        for ev in station_data.get("maintenance_events", []):
            offset = float(ev.get("calibration_offset_mm", 0.0))
            tolerance = float(ev.get("tolerance_limit_mm", 0.010))
            if offset > tolerance:
                suspicious_maintenance.append({
                    "event_id": ev.get("id"),
                    "title": ev.get("title"),
                    "technician_name": ev.get("technician_name"),
                    "crew_name": ev.get("crew_name"),
                    "calibration_offset_mm": offset,
                    "tolerance_limit_mm": tolerance,
                    "exceeded_by_pct": round(((offset - tolerance) / tolerance) * 100, 1),
                    "notes": ev.get("notes"),
                })

        # 4. Analyze upstream lots for out-of-spec chemical / mechanical properties
        culprit_material_lots: list[dict[str, Any]] = []
        for chain in lineage_chains:
            for up_lot in chain.get("upstream_lots", []):
                prop_json = up_lot.get("properties_json") or "{}"
                try:
                    props = json.loads(prop_json) if isinstance(prop_json, str) else prop_json
                except Exception:
                    props = {}

                if props.get("out_of_spec") or props.get("silicon_content_pct", 0) > 1.35:
                    culprit_material_lots.append({
                        "lot_id": up_lot.get("id"),
                        "lot_number": up_lot.get("lot_number"),
                        "supplier": up_lot.get("supplier", {}),
                        "properties": props,
                        "material_type": up_lot.get("material_type"),
                    })

        # 5. Extract operator log warnings
        relevant_operator_logs: list[dict[str, Any]] = []
        for op_log in station_data.get("operator_logs", []):
            text = op_log.get("text", "").lower()
            if any(w in text for w in ["warm", "hum", "spindle", "feed rate", "crack"]):
                relevant_operator_logs.append(op_log)

        # 6. Synthesize Root Cause Hypothesis
        hypotheses: list[dict[str, Any]] = []
        if suspicious_maintenance and culprit_material_lots:
            hypotheses.append({
                "type": "compound_failure",
                "confidence": 0.96,
                "title": "Spindle Bearing Miscalibration Compounded by Out-of-Spec Alloy Lot",
                "primary_cause": suspicious_maintenance[0],
                "compounding_cause": culprit_material_lots[0],
                "operator_corroboration": relevant_operator_logs,
                "description": (
                    f"Spindle bearing calibration offset (+{suspicious_maintenance[0]['calibration_offset_mm']}mm) "
                    f"exceeded maximum tolerance (+{suspicious_maintenance[0]['tolerance_limit_mm']}mm). "
                    f"When out-of-spec hard alloy Lot #{culprit_material_lots[0]['lot_number']} "
                    f"(silicon {culprit_material_lots[0]['properties'].get('silicon_content_pct')}%) was milled, "
                    f"thermal runaway and cutter chatter induced catastrophic micro-fractures."
                ),
            })
        elif suspicious_maintenance:
            hypotheses.append({
                "type": "mechanical_miscalibration",
                "confidence": 0.82,
                "title": "Spindle Runout Miscalibration",
                "cause": suspicious_maintenance[0],
            })

        return {
            "machine_id": machine_id,
            "line_id": line_id,
            "station_data": station_data,
            "suspicious_maintenance": suspicious_maintenance,
            "culprit_lots": culprit_material_lots,
            "relevant_operator_logs": relevant_operator_logs,
            "hypotheses": hypotheses,
        }
