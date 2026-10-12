"""Topology repository: Plants, ProductionLines, Machines, and Sensors."""

from __future__ import annotations

from typing import Any

from app.graph.repositories.base import BaseGraphRepository


class TopologyRepository(BaseGraphRepository):
    """Manages plant, line, machine, and sensor nodes and structural relationships."""

    async def upsert_plants(self, plants: list[dict[str, Any]]) -> int:
        query = """
        UNWIND $batch AS row
        MERGE (p:Plant {id: row.id})
        SET p.name = row.name,
            p.code = row.code,
            p.location = row.location,
            p.active = row.active,
            p.updated_at = datetime()
        RETURN count(p)
        """
        return await self.batch_unwind_write(query, plants)

    async def upsert_lines(self, lines: list[dict[str, Any]]) -> int:
        query = """
        UNWIND $batch AS row
        MERGE (l:ProductionLine {id: row.id})
        SET l.name = row.name,
            l.code = row.code,
            l.target_rate_uph = row.target_rate_uph,
            l.active = row.active,
            l.updated_at = datetime()
        WITH l, row
        MATCH (p:Plant {id: row.plant_id})
        MERGE (p)-[:CONTAINS_LINE]->(l)
        RETURN count(l)
        """
        return await self.batch_unwind_write(query, lines)

    async def upsert_machines(self, machines: list[dict[str, Any]]) -> int:
        query = """
        UNWIND $batch AS row
        MERGE (m:Machine {id: row.id})
        SET m.name = row.name,
            m.code = row.code,
            m.machine_type = row.machine_type,
            m.model = row.model,
            m.serial_number = row.serial_number,
            m.status = row.status,
            m.updated_at = datetime()
        WITH m, row
        MATCH (l:ProductionLine {id: row.line_id})
        MERGE (l)-[:CONTAINS_MACHINE]->(m)
        RETURN count(m)
        """
        return await self.batch_unwind_write(query, machines)

    async def upsert_sensors(self, sensors: list[dict[str, Any]]) -> int:
        query = """
        UNWIND $batch AS row
        MERGE (s:Sensor {id: row.id})
        SET s.name = row.name,
            s.sensor_type = row.sensor_type,
            s.tag = row.tag,
            s.unit = row.unit,
            s.warning_threshold = row.warning_threshold,
            s.critical_threshold = row.critical_threshold,
            s.updated_at = datetime()
        WITH s, row
        MATCH (m:Machine {id: row.machine_id})
        MERGE (m)-[:HAS_SENSOR]->(s)
        RETURN count(s)
        """
        return await self.batch_unwind_write(query, sensors)

    async def get_machine(self, machine_id: str) -> dict[str, Any] | None:
        query = """
        MATCH (m:Machine {id: $machine_id})
        OPTIONAL MATCH (l:ProductionLine)-[:CONTAINS_MACHINE]->(m)
        OPTIONAL MATCH (p:Plant)-[:CONTAINS_LINE]->(l)
        OPTIONAL MATCH (m)-[:HAS_SENSOR]->(s:Sensor)
        RETURN m {
            .*,
            line_id: l.id,
            line_name: l.name,
            plant_id: p.id,
            plant_name: p.name,
            sensors: collect(s {.*})
        } AS machine
        """
        records = await self.execute_read(query, {"machine_id": machine_id})
        return records[0]["machine"] if records and records[0]["machine"] else None

    async def get_all_machines(self) -> list[dict[str, Any]]:
        query = """
        MATCH (m:Machine)
        OPTIONAL MATCH (l:ProductionLine)-[:CONTAINS_MACHINE]->(m)
        RETURN m {
            .*,
            line_id: l.id,
            line_name: l.name
        } AS machine
        ORDER BY m.name
        """
        records = await self.execute_read(query)
        return [r["machine"] for r in records]
