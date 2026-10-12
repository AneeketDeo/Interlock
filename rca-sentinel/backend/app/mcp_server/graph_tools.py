"""Graph MCP tools for querying manufacturing ontology topology and provenance."""

from __future__ import annotations

from typing import Any

from app.graph.queries.traversal import GraphTraversalQueries

_traversal = GraphTraversalQueries()


async def get_machine_subgraph(machine_id: str) -> dict[str, Any]:
    """Retrieve the full 2-hop graph neighborhood for a machine.

    Args:
        machine_id: Canonical machine ID (e.g. 'station-03b').

    Returns:
        Dict containing machine node, connected production line, sensors,
        recent maintenance events, operator logs, and processed material lots.
    """
    return await _traversal.get_machine_subgraph(machine_id)


async def trace_lot_provenance(lot_id: str) -> dict[str, Any]:
    """Perform recursive multi-hop backward traversal to trace raw material provenance.

    Args:
        lot_id: Canonical material lot ID (e.g. 'lot-62933', 'lot-40921').

    Returns:
        Dict containing target lot, complete upstream supply chain hops,
        and associated supplier profiles.
    """
    return await _traversal.trace_lot_provenance(lot_id)


async def get_maintenance_history(
    machine_id: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Retrieve recent maintenance work orders and calibration offsets for a machine.

    Args:
        machine_id: Canonical machine ID (e.g. 'station-03b').
        limit: Max events to return.

    Returns:
        List of maintenance events with technician notes and calibration runout measurements.
    """
    return await _traversal.find_recent_maintenance(machine_id, limit=limit)


async def get_operator_logs(
    machine_id: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Retrieve shift logs and free-text operator observations for a machine.

    Args:
        machine_id: Canonical machine ID (e.g. 'station-03b').
        limit: Max log entries to return.

    Returns:
        List of operator logs with text content, shift numbers, and extracted keywords.
    """
    return await _traversal.find_operator_logs(machine_id, limit=limit)
