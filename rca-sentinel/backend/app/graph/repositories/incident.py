"""Incident and remediation repository: Incidents, DecisionObjects, Actions, Approvals."""

from __future__ import annotations

import json
from typing import Any, cast

from app.graph.repositories.base import BaseGraphRepository


class IncidentRepository(BaseGraphRepository):
    """Manages Incident nodes, 8D DecisionObjects, RemediationActions, and Approval records."""

    async def create_incident(self, incident: dict[str, Any]) -> dict[str, Any]:
        query = """
        MERGE (i:Incident {id: $id})
        SET i.title = $title,
            i.status = $status,
            i.severity = $severity,
            i.line_id = $line_id,
            i.detected_at = datetime($detected_at),
            i.anomaly_score = $anomaly_score,
            i.blast_radius_units = $blast_radius_units,
            i.financial_impact_usd = $financial_impact_usd,
            i.created_at = datetime(),
            i.updated_at = datetime()
        WITH i
        MATCH (l:ProductionLine {id: $line_id})
        MERGE (l)-[:HAS_INCIDENT]->(i)
        RETURN i {.*} AS incident
        """
        params = {
            "id": incident["id"],
            "title": incident["title"],
            "status": incident.get("status", "detected"),
            "severity": incident.get("severity", "high"),
            "line_id": incident["line_id"],
            "detected_at": incident["detected_at"],
            "anomaly_score": incident.get("anomaly_score", 0.95),
            "blast_radius_units": incident.get("blast_radius_units", 0),
            "financial_impact_usd": incident.get("financial_impact_usd", 0.0),
        }
        records = await self.execute_write(query, params)
        return cast(dict[str, Any], records[0]["incident"])

    async def link_incident_root_cause(
        self,
        incident_id: str,
        machine_id: str | None = None,
        lot_id: str | None = None,
        failure_mode_id: str | None = None,
        confidence: float = 0.92,
        reasoning: str = "",
    ) -> None:
        """Link an incident to identified root cause nodes."""
        if machine_id:
            query_m = """
            MATCH (i:Incident {id: $incident_id})
            MATCH (m:Machine {id: $machine_id})
            MERGE (i)-[r:SUSPECTED_ROOT_CAUSE]->(m)
            SET r.confidence = $confidence, r.reasoning = $reasoning, r.updated_at = datetime()
            """
            await self.execute_write(
                query_m,
                {
                    "incident_id": incident_id,
                    "machine_id": machine_id,
                    "confidence": confidence,
                    "reasoning": reasoning,
                },
            )

        if lot_id:
            query_l = """
            MATCH (i:Incident {id: $incident_id})
            MATCH (ml:MaterialLot {id: $lot_id})
            MERGE (i)-[r:SUSPECTED_ROOT_CAUSE]->(ml)
            SET r.confidence = $confidence, r.reasoning = $reasoning, r.updated_at = datetime()
            """
            await self.execute_write(
                query_l,
                {
                    "incident_id": incident_id,
                    "lot_id": lot_id,
                    "confidence": confidence,
                    "reasoning": reasoning,
                },
            )

        if failure_mode_id:
            query_f = """
            MATCH (i:Incident {id: $incident_id})
            MATCH (fm:FailureMode {id: $failure_mode_id})
            MERGE (i)-[r:CLASSIFIED_AS]->(fm)
            SET r.confidence = $confidence, r.updated_at = datetime()
            """
            await self.execute_write(
                query_f,
                {
                    "incident_id": incident_id,
                    "failure_mode_id": failure_mode_id,
                    "confidence": confidence,
                },
            )

    async def add_decision_object(
        self, incident_id: str, decision: dict[str, Any]
    ) -> dict[str, Any]:
        """Attach an 8D stage DecisionObject to an Incident."""
        query = """
        MATCH (i:Incident {id: $incident_id})
        MERGE (d:DecisionObject {id: $id})
        SET d.stage = $stage,
            d.agent_name = $agent_name,
            d.confidence = $confidence,
            d.status = $status,
            d.content_json = $content_json,
            d.reasoning = $reasoning,
            d.evidence_node_ids = $evidence_node_ids,
            d.created_at = datetime()
        MERGE (i)-[:HAS_DECISION]->(d)
        RETURN d {.*} AS decision
        """
        params = {
            "incident_id": incident_id,
            "id": decision["id"],
            "stage": decision["stage"],
            "agent_name": decision.get("agent_name", "agent"),
            "confidence": decision.get("confidence", 0.9),
            "status": decision.get("status", "proposed"),
            "content_json": json.dumps(decision.get("content", {})),
            "reasoning": decision.get("reasoning", ""),
            "evidence_node_ids": decision.get("evidence_node_ids", []),
        }
        records = await self.execute_write(query, params)
        return cast(dict[str, Any], records[0]["decision"])

    async def propose_action(
        self, incident_id: str, action: dict[str, Any]
    ) -> dict[str, Any]:
        """Propose a remediation action requiring human approval gate."""
        query = """
        MATCH (i:Incident {id: $incident_id})
        MERGE (a:RemediationAction {id: $id})
        SET a.action_type = $action_type,
            a.target_entity = $target_entity,
            a.target_entity_type = $target_entity_type,
            a.description = $description,
            a.status = $status,
            a.requires_human_approval = $requires_human_approval,
            a.created_at = datetime()
        MERGE (i)-[:HAS_ACTION]->(a)
        RETURN a {.*} AS action
        """
        params = {
            "incident_id": incident_id,
            "id": action["id"],
            "action_type": action["action_type"],
            "target_entity": action["target_entity"],
            "target_entity_type": action.get("target_entity_type", "Machine"),
            "description": action["description"],
            "status": action.get("status", "pending_approval"),
            "requires_human_approval": action.get("requires_human_approval", True),
        }
        records = await self.execute_write(query, params)
        return cast(dict[str, Any], records[0]["action"])

    async def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        """Get incident with decisions, actions, and root cause evidence."""
        query = """
        MATCH (i:Incident {id: $incident_id})
        OPTIONAL MATCH (i)-[:HAS_DECISION]->(d:DecisionObject)
        OPTIONAL MATCH (i)-[:HAS_ACTION]->(a:RemediationAction)
        OPTIONAL MATCH (i)-[r:SUSPECTED_ROOT_CAUSE]->(rc)
        RETURN i {
            .*,
            decisions: collect(DISTINCT d {.*}),
            actions: collect(DISTINCT a {.*}),
            root_causes: collect(DISTINCT {
                node_id: rc.id,
                labels: labels(rc),
                confidence: r.confidence,
                reasoning: r.reasoning
            })
        } AS incident
        """
        records = await self.execute_read(query, {"incident_id": incident_id})
        return records[0]["incident"] if records and records[0]["incident"] else None

    async def get_all_incidents(self) -> list[dict[str, Any]]:
        query = """
        MATCH (i:Incident)
        RETURN i {.*} AS incident
        ORDER BY i.detected_at DESC
        """
        records = await self.execute_read(query)
        return [r["incident"] for r in records]
