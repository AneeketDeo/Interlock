"""MCP resources and prompts providing domain context to AI reasoning agents."""

from __future__ import annotations

from typing import Any

from app.graph.repositories.failure_mode import FailureModeRepository
from app.graph.repositories.incident import IncidentRepository

_incident_repo = IncidentRepository()
_failure_repo = FailureModeRepository()


async def get_ontology_summary() -> dict[str, Any]:
    """MCP Resource: manufacturing://ontology/summary."""
    return {
        "classes": [
            "Plant",
            "ProductionLine",
            "Machine",
            "Sensor",
            "Supplier",
            "MaterialLot",
            "MaintenanceEvent",
            "OperatorLog",
            "FailureMode",
            "Incident",
            "DecisionObject",
            "RemediationAction",
        ],
        "relationships": [
            "CONTAINS_LINE",
            "CONTAINS_MACHINE",
            "HAS_SENSOR",
            "SUPPLIED_LOT",
            "CONSUMED_LOT",
            "PROCESSED_LOT",
            "HAS_MAINTENANCE_EVENT",
            "HAS_OPERATOR_LOG",
            "EXHIBITS_FAILURE_MODE",
            "HAS_INCIDENT",
            "HAS_DECISION",
            "HAS_ACTION",
            "SUSPECTED_ROOT_CAUSE",
        ],
        "version": "1.0.0",
        "standard": "ISO 22400 / W3C PROV-O",
    }


async def get_active_incidents() -> list[dict[str, Any]]:
    """MCP Resource: manufacturing://incidents/active."""
    return await _incident_repo.get_all_incidents()


async def get_failure_mode_catalog() -> list[dict[str, Any]]:
    """MCP Resource: manufacturing://pfmea/catalog."""
    return await _failure_repo.get_all_failure_modes()
