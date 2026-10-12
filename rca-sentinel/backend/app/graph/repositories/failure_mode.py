"""Failure mode repository: FailureMode and PFMEA graph nodes."""

from __future__ import annotations

from typing import Any

from app.graph.repositories.base import BaseGraphRepository


class FailureModeRepository(BaseGraphRepository):
    """Manages FailureMode taxonomy, PFMEA RPN calculations, and machine failure links."""

    async def upsert_failure_modes(
        self, modes: list[dict[str, Any]]
    ) -> int:
        query = """
        UNWIND $batch AS row
        MERGE (fm:FailureMode {id: row.id})
        SET fm.code = row.code,
            fm.name = row.name,
            fm.description = row.description,
            fm.severity = row.severity,
            fm.occurrence = row.occurrence,
            fm.detection = row.detection,
            fm.rpn = row.severity * row.occurrence * row.detection,
            fm.potential_causes = row.potential_causes,
            fm.recommended_actions = row.recommended_actions,
            fm.updated_at = datetime()
        RETURN count(fm)
        """
        return await self.batch_unwind_write(query, modes)

    async def link_machine_failure_mode(
        self, machine_id: str, failure_mode_id: str
    ) -> None:
        query = """
        MATCH (m:Machine {id: $machine_id})
        MATCH (fm:FailureMode {id: $failure_mode_id})
        MERGE (m)-[:EXHIBITS_FAILURE_MODE]->(fm)
        """
        await self.execute_write(
            query,
            {"machine_id": machine_id, "failure_mode_id": failure_mode_id},
        )

    async def get_all_failure_modes(self) -> list[dict[str, Any]]:
        query = """
        MATCH (fm:FailureMode)
        RETURN fm {.*} AS mode
        ORDER BY fm.rpn DESC
        """
        records = await self.execute_read(query)
        return [r["mode"] for r in records]

    async def get_failure_mode(self, mode_id: str) -> dict[str, Any] | None:
        query = """
        MATCH (fm:FailureMode {id: $mode_id})
        RETURN fm {.*} AS mode
        """
        records = await self.execute_read(query, {"mode_id": mode_id})
        return records[0]["mode"] if records and records[0]["mode"] else None
