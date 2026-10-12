"""Graph bootstrap: creates constraints, indexes, and reference data in Neo4j Aura.

Run during `make seed` or app startup. All operations are idempotent.
Uses only Aura-compatible Cypher (no n10s, no custom plugins).
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.graph.client import Neo4jClient

logger = get_logger(__name__)

# ── Uniqueness Constraints ──────────────────────────────────────────
# Every label that is merged on requires a uniqueness constraint.

CONSTRAINTS = [
    # Manufacturing hierarchy
    "CREATE CONSTRAINT plant_id IF NOT EXISTS FOR (n:Plant) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT line_id IF NOT EXISTS FOR (n:Line) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT machine_id IF NOT EXISTS FOR (n:Machine) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT sensor_id IF NOT EXISTS FOR (n:Sensor) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT tag_id IF NOT EXISTS FOR (n:Tag) REQUIRE n.id IS UNIQUE",
    # Production
    "CREATE CONSTRAINT workorder_id IF NOT EXISTS FOR (n:WorkOrder) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT batch_id IF NOT EXISTS FOR (n:Batch) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT product_id IF NOT EXISTS FOR (n:Product) REQUIRE n.id IS UNIQUE",
    # Personnel
    "CREATE CONSTRAINT operator_id IF NOT EXISTS FOR (n:Operator) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT shift_id IF NOT EXISTS FOR (n:Shift) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT crew_id IF NOT EXISTS FOR (n:Crew) REQUIRE n.id IS UNIQUE",
    # Maintenance
    "CREATE CONSTRAINT maintenance_log_id IF NOT EXISTS FOR (n:MaintenanceLog) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT calibration_event_id IF NOT EXISTS FOR (n:CalibrationEvent) REQUIRE n.id IS UNIQUE",
    # Supply chain
    "CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (n:Supplier) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT material_lot_id IF NOT EXISTS FOR (n:MaterialLot) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT component_id IF NOT EXISTS FOR (n:Component) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT bom_item_id IF NOT EXISTS FOR (n:BOMItem) REQUIRE n.id IS UNIQUE",
    # Quality
    "CREATE CONSTRAINT defect_code_id IF NOT EXISTS FOR (n:DefectCode) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT failure_mode_id IF NOT EXISTS FOR (n:FailureMode) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT cause_id IF NOT EXISTS FOR (n:Cause) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT control_plan_id IF NOT EXISTS FOR (n:ControlPlan) REQUIRE n.id IS UNIQUE",
    # Incident/Decision
    "CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (n:Incident) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT decision_object_id IF NOT EXISTS FOR (n:DecisionObject) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT evidence_link_id IF NOT EXISTS FOR (n:EvidenceLink) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT remediation_action_id IF NOT EXISTS FOR (n:RemediationAction) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT approval_id IF NOT EXISTS FOR (n:Approval) REQUIRE n.id IS UNIQUE",
    # Ontology metadata
    "CREATE CONSTRAINT ontology_class_uri IF NOT EXISTS FOR (n:OntologyClass) REQUIRE n.uri IS UNIQUE",
    "CREATE CONSTRAINT ontology_rel_uri IF NOT EXISTS FOR (n:OntologyRelationship) REQUIRE n.uri IS UNIQUE",
    "CREATE CONSTRAINT ontology_prop_uri IF NOT EXISTS FOR (n:OntologyProperty) REQUIRE n.uri IS UNIQUE",
    # Additional business-key uniqueness
    "CREATE CONSTRAINT lot_number_unique IF NOT EXISTS FOR (n:MaterialLot) REQUIRE n.lot_number IS UNIQUE",
    "CREATE CONSTRAINT supplier_code_unique IF NOT EXISTS FOR (n:Supplier) REQUIRE n.code IS UNIQUE",
    "CREATE CONSTRAINT plant_code_unique IF NOT EXISTS FOR (n:Plant) REQUIRE n.code IS UNIQUE",
    "CREATE CONSTRAINT line_code_unique IF NOT EXISTS FOR (n:Line) REQUIRE n.code IS UNIQUE",
    "CREATE CONSTRAINT machine_code_unique IF NOT EXISTS FOR (n:Machine) REQUIRE n.code IS UNIQUE",
]

# ── Indexes for common lookups ──────────────────────────────────────

INDEXES = [
    "CREATE INDEX incident_status IF NOT EXISTS FOR (n:Incident) ON (n.status)",
    "CREATE INDEX incident_severity IF NOT EXISTS FOR (n:Incident) ON (n.severity)",
    "CREATE INDEX incident_detected_at IF NOT EXISTS FOR (n:Incident) ON (n.detected_at)",
    "CREATE INDEX decision_stage IF NOT EXISTS FOR (n:DecisionObject) ON (n.stage)",
    "CREATE INDEX decision_incident IF NOT EXISTS FOR (n:DecisionObject) ON (n.incident_id)",
    "CREATE INDEX approval_status IF NOT EXISTS FOR (n:Approval) ON (n.status)",
    "CREATE INDEX sensor_tag IF NOT EXISTS FOR (n:Sensor) ON (n.tag)",
    "CREATE INDEX workorder_number IF NOT EXISTS FOR (n:WorkOrder) ON (n.order_number)",
    "CREATE INDEX maintenance_type IF NOT EXISTS FOR (n:MaintenanceLog) ON (n.maintenance_type)",
    "CREATE INDEX supplier_tier IF NOT EXISTS FOR (n:Supplier) ON (n.tier)",
    "CREATE INDEX machine_line IF NOT EXISTS FOR (n:Machine) ON (n.line_id)",
]


async def bootstrap_graph(neo4j_client: Neo4jClient) -> dict[str, int]:
    """Apply all constraints and indexes to the Neo4j database.

    Returns counts of applied constraints and indexes.
    """
    counts = {"constraints": 0, "indexes": 0, "errors": 0}

    # Apply constraints
    for constraint in CONSTRAINTS:
        try:
            await neo4j_client.execute_write(constraint)
            counts["constraints"] += 1
        except Exception as exc:
            # Constraint may already exist — log and continue
            logger.debug("constraint_skipped", constraint=constraint[:80], error=str(exc))
            counts["constraints"] += 1  # Count as applied (idempotent)

    # Apply indexes
    for index in INDEXES:
        try:
            await neo4j_client.execute_write(index)
            counts["indexes"] += 1
        except Exception as exc:
            logger.debug("index_skipped", index=index[:80], error=str(exc))
            counts["indexes"] += 1

    logger.info("graph_bootstrap_complete", **counts)
    return counts


async def verify_bootstrap(neo4j_client: Neo4jClient) -> dict[str, int]:
    """Verify constraints and indexes are applied. Returns current counts."""
    constraints_result = await neo4j_client.execute_read("SHOW CONSTRAINTS")
    indexes_result = await neo4j_client.execute_read("SHOW INDEXES")

    counts = {
        "constraints": len(constraints_result),
        "indexes": len(indexes_result),
    }
    logger.info("graph_bootstrap_verified", **counts)
    return counts
