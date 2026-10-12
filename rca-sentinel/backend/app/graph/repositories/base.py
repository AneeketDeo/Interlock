"""Base graph repository with parameterized Cypher batch helpers.

All Cypher queries MUST use parameterized inputs ($params) to prevent injection
and leverage Aura query plan caching.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.graph.client import Neo4jClient, get_neo4j_client

logger = get_logger(__name__)


class BaseGraphRepository:
    """Base repository providing parameterized Cypher query primitives."""

    def __init__(self, client: Neo4jClient | None = None) -> None:
        self._client = client

    @property
    def client(self) -> Neo4jClient:
        if self._client is not None:
            return self._client
        return get_neo4j_client()

    async def execute_read(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Run a parameterized read transaction."""
        return await self.client.execute_read(query, parameters or {})

    async def execute_write(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Run a parameterized write transaction."""
        return await self.client.execute_write(query, parameters or {})

    async def batch_unwind_write(
        self,
        query: str,
        items: list[dict[str, Any]],
        batch_size: int = 500,
    ) -> int:
        """Execute a parameterized UNWIND write query in batches."""
        if not items:
            return 0

        total_inserted = 0
        for i in range(0, len(items), batch_size):
            chunk = items[i : i + batch_size]
            await self.client.execute_write(query, {"batch": chunk})
            total_inserted += len(chunk)

        return total_inserted
