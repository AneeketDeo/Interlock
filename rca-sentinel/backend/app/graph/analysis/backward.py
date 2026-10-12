"""Backward analysis and commonality scoring across multi-silo manufacturing graph."""

from __future__ import annotations

import json
from typing import Any

from app.core.logging import get_logger
from app.graph.client import Neo4jClient, get_neo4j_client

logger = get_logger(__name__)


class BackwardAnalysisEngine:
    """Performs multi-hop backward reasoning from an anomaly to identify root causes."""

    def __init__(self, client: Neo4jClient | None = None) -> None:
        self._client = client

    @property
    def client(self) -> Neo4jClient:
        return self._client or get_neo4j_client()

    async def analyze_incident(
        self,
        line_id: str = "line-03",
        machine_id: str = "station-03b",
    ) -> dict[str, Any]:
        """Perform comprehensive backward traversal to diagnose root cause."""
        logger.info("backward_analysis_started", line_id=line_id, machine_id=machine_id)

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
