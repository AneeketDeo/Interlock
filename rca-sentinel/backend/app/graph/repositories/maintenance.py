"""Maintenance repository: MaintenanceEvent and OperatorLog nodes."""

from __future__ import annotations

from typing import Any

from app.graph.repositories.base import BaseGraphRepository


class MaintenanceRepository(BaseGraphRepository):
    """Manages maintenance work orders, technician events, and operator shift notes."""

    async def upsert_maintenance_events(
        self, events: list[dict[str, Any]]
    ) -> int:
        query = """
        UNWIND $batch AS row
        MERGE (ev:MaintenanceEvent {id: row.id})
        SET ev.event_type = row.event_type,
            ev.title = row.title,
            ev.technician_id = row.technician_id,
            ev.technician_name = row.technician_name,
            ev.crew_name = row.crew_name,
            ev.shift = row.shift,
            ev.timestamp = datetime(row.timestamp),
            ev.duration_minutes = row.duration_minutes,
            ev.calibration_offset_mm = row.calibration_offset_mm,
            ev.tolerance_limit_mm = row.tolerance_limit_mm,
            ev.notes = row.notes,
            ev.status = row.status,
            ev.updated_at = datetime()
        WITH ev, row
        MATCH (m:Machine {id: row.machine_id})
        MERGE (m)-[:HAS_MAINTENANCE_EVENT]->(ev)
        RETURN count(ev)
        """
        return await self.batch_unwind_write(query, events)

    async def upsert_operator_logs(self, logs: list[dict[str, Any]]) -> int:
        query = """
        UNWIND $batch AS row
        MERGE (ol:OperatorLog {id: row.id})
        SET ol.operator_id = row.operator_id,
            ol.operator_name = row.operator_name,
            ol.shift = row.shift,
            ol.timestamp = datetime(row.timestamp),
            ol.text = row.text,
            ol.tags = row.tags,
            ol.updated_at = datetime()
        WITH ol, row
        MATCH (m:Machine {id: row.machine_id})
        MERGE (m)-[:HAS_OPERATOR_LOG]->(ol)
        RETURN count(ol)
        """
        return await self.batch_unwind_write(query, logs)

    async def get_machine_maintenance_history(
        self, machine_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        query = """
        MATCH (m:Machine {id: $machine_id})-[:HAS_MAINTENANCE_EVENT]->(ev:MaintenanceEvent)
        RETURN ev {.*} AS event
        ORDER BY ev.timestamp DESC
        LIMIT $limit
        """
        records = await self.execute_read(
            query, {"machine_id": machine_id, "limit": limit}
        )
        return [r["event"] for r in records]

    async def get_machine_operator_logs(
        self, machine_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        query = """
        MATCH (m:Machine {id: $machine_id})-[:HAS_OPERATOR_LOG]->(ol:OperatorLog)
        RETURN ol {.*} AS log
        ORDER BY ol.timestamp DESC
        LIMIT $limit
        """
        records = await self.execute_read(
            query, {"machine_id": machine_id, "limit": limit}
        )
        return [r["log"] for r in records]
