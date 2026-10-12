"""Neo4j Aura async client with connection pooling, retry, and health check.

Connects to a hosted Neo4j Aura instance. No local Neo4j container.
Provides managed read/write transaction execution and startup connectivity check.
"""

from __future__ import annotations

from typing import Any

import neo4j
from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncManagedTransaction
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.core.config import Settings, get_settings
from app.core.errors import GraphConnectionError, GraphQueryError
from app.core.logging import get_logger

logger = get_logger(__name__)


class Neo4jClient:
    """Async Neo4j driver wrapper with pooling, retry, and health checks."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """Create the async driver and verify connectivity."""
        try:
            self._driver = AsyncGraphDatabase.driver(
                self._settings.neo4j_uri,
                auth=(self._settings.neo4j_username, self._settings.neo4j_password),
                max_connection_pool_size=self._settings.neo4j_max_connection_pool_size,
                connection_timeout=self._settings.neo4j_connection_timeout,
            )
            await self._driver.verify_connectivity()
            logger.info(
                "neo4j_connected",
                uri=self._settings.neo4j_uri,
                database=self._settings.neo4j_database,
            )
        except Exception as exc:
            raise GraphConnectionError(
                f"Cannot connect to Neo4j Aura at {self._settings.neo4j_uri}. "
                f"Check if the instance is running and credentials are correct. "
                f"Aura instances may be paused if idle. Error: {exc}"
            ) from exc

    async def close(self) -> None:
        """Close the driver and release all connections."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("neo4j_disconnected")

    @property
    def driver(self) -> AsyncDriver:
        if self._driver is None:
            raise GraphConnectionError("Neo4j driver not initialized. Call connect() first.")
        return self._driver

    async def health_check(self) -> bool:
        """Check connectivity to the Aura instance. Returns True if healthy."""
        try:
            await self.driver.verify_connectivity()
            return True
        except Exception as exc:
            logger.warning("neo4j_health_check_failed", error=str(exc))
            return False

    @retry(
        retry=retry_if_exception_type(neo4j.exceptions.TransientError),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.5, max=10),
        reraise=True,
    )
    async def execute_read(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Execute a read query with retry on transient errors."""
        try:
            async with self.driver.session(
                database=self._settings.neo4j_database,
            ) as session:

                async def _work(tx: AsyncManagedTransaction) -> list[dict[str, Any]]:
                    result = await tx.run(query, parameters or {})
                    records = await result.data()
                    return list(records)

                return await session.execute_read(_work)
        except neo4j.exceptions.TransientError:
            raise
        except neo4j.exceptions.Neo4jError as exc:
            raise GraphQueryError(
                f"Neo4j read query failed: {exc.message}",
                details={"query_preview": query[:200], "code": exc.code},
            ) from exc

    @retry(
        retry=retry_if_exception_type(neo4j.exceptions.TransientError),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.5, max=10),
        reraise=True,
    )
    async def execute_write(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Execute a write query with retry on transient errors."""
        try:
            async with self.driver.session(
                database=self._settings.neo4j_database,
            ) as session:

                async def _work(tx: AsyncManagedTransaction) -> list[dict[str, Any]]:
                    result = await tx.run(query, parameters or {})
                    records = await result.data()
                    return list(records)

                return await session.execute_write(_work)
        except neo4j.exceptions.TransientError:
            raise
        except neo4j.exceptions.Neo4jError as exc:
            raise GraphQueryError(
                f"Neo4j write query failed: {exc.message}",
                details={"query_preview": query[:200], "code": exc.code},
            ) from exc

    async def execute_write_batch(
        self,
        query: str,
        rows: list[dict[str, Any]],
        batch_size: int = 1000,
    ) -> int:
        """Execute a batched write using UNWIND. Returns total rows processed."""
        total = 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            await self.execute_write(query, {"rows": batch})
            total += len(batch)
            logger.debug("batch_write_progress", processed=total, total=len(rows))
        return total


# Module-level singleton (initialized during app lifespan)
_neo4j_client: Neo4jClient | None = None


def get_neo4j_client() -> Neo4jClient:
    """Get the module-level Neo4j client singleton."""
    if _neo4j_client is None:
        raise GraphConnectionError("Neo4j client not initialized.")
    return _neo4j_client


async def init_neo4j_client(settings: Settings | None = None) -> Neo4jClient:
    """Initialize and return the module-level Neo4j client."""
    global _neo4j_client
    _neo4j_client = Neo4jClient(settings)
    await _neo4j_client.connect()
    return _neo4j_client


async def close_neo4j_client() -> None:
    """Close the module-level Neo4j client."""
    global _neo4j_client
    if _neo4j_client:
        await _neo4j_client.close()
        _neo4j_client = None
