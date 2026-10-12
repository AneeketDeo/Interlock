"""Multi-hop Cypher traversal queries for root cause analysis."""

from __future__ import annotations

from typing import Any

from app.graph.cache import cached_graph_query
from app.graph.client import Neo4jClient, get_neo4j_client


class GraphTraversalQueries:
    """Traverses manufacturing ontology graphs to discover multi-hop causal chains."""

    def __init__(self, client: Neo4jClient | None = None) -> None:
        self._client = client

    @property
    def client(self) -> Neo4jClient:
        return self._client or get_neo4j_client()

    @cached_graph_query(ttl_seconds=30)
    async def trace_lot_provenance(self, lot_id: str) -> dict[str, Any]:
        """Multi-hop backward traversal: traces MaterialLot upstream through suppliers."""
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
