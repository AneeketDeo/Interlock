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


class SpannerGraphClient:
    """Google Cloud Spanner Graph client with connection pooling and ISO GQL execution."""

    DEFAULT_PROJECT_ID = "project-a8fa4909-225e-4882-b45"
    DEFAULT_INSTANCE_ID = "rca"
    DEFAULT_DATABASE_ID = "rca-db"
    DEFAULT_GRAPH_NAME = "FactoryGraph"

    def __init__(
        self,
        project_id: str | None = None,
        instance_id: str | None = None,
        database_id: str | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self.project_id = (
            project_id
            or getattr(self._settings, "gcp_project_id", None)
            or self.DEFAULT_PROJECT_ID
        )
        self.instance_id = (
            instance_id
            or getattr(self._settings, "spanner_instance_id", None)
            or self.DEFAULT_INSTANCE_ID
        )
        self.database_id = (
            database_id
            or getattr(self._settings, "spanner_database_id", None)
            or self.DEFAULT_DATABASE_ID
        )
        self.graph_name = (
            getattr(self._settings, "spanner_graph_name", None)
            or self.DEFAULT_GRAPH_NAME
        )
        self._client: Any = None
        self._instance: Any = None
        self._database: Any = None

    def _ensure_connected_sync(self) -> None:
        """Synchronously initialize Cloud Spanner client, instance, and database handles."""
        if self._database is None:
            from google.cloud import spanner
            self._client = spanner.Client(project=self.project_id)
            self._instance = self._client.instance(self.instance_id)
            self._database = self._instance.database(self.database_id)
            logger.info(
                "spanner_graph_initialized",
                project=self.project_id,
                instance=self.instance_id,
                database=self.database_id,
                graph=self.graph_name,
            )

    async def connect(self) -> None:
        """Initialize Cloud Spanner client, instance, and database handles."""
        try:
            self._ensure_connected_sync()
        except Exception as exc:
            raise GraphConnectionError(
                f"Cannot connect to Cloud Spanner at {self.instance_id}/{self.database_id}: {exc}"
            ) from exc

    async def close(self) -> None:
        """Close Spanner client resources."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            self._instance = None
            logger.info("spanner_graph_disconnected")

    async def health_check(self) -> bool:
        """Verify Spanner database connectivity."""
        try:
            self._ensure_connected_sync()
            import asyncio
            loop = asyncio.get_running_loop()

            def _check() -> bool:
                with self._database.snapshot() as snapshot:
                    cursor = snapshot.execute_sql("SELECT 1")
                    list(cursor)
                return True

            return await loop.run_in_executor(None, _check)
        except Exception as exc:
            logger.warning("spanner_health_check_failed", error=str(exc))
            return False

    def execute_gql_sync(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        param_types_map: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Synchronously execute an ISO GQL query against Cloud Spanner database snapshot."""
        self._ensure_connected_sync()
        try:
            results: list[dict[str, Any]] = []
            with self._database.snapshot() as snapshot:
                cursor = snapshot.execute_sql(
                    query,
                    params=parameters,
                    param_types=param_types_map,
                )
                for row in cursor:
                    row_dict = {}
                    for field, val in zip(cursor.fields, row, strict=False):
                        row_dict[field.name] = val
                    results.append(row_dict)
            return results
        except Exception as exc:
            raise GraphQueryError(
                f"Cloud Spanner ISO GQL query failed: {exc}",
                details={"query_preview": query[:200]},
            ) from exc

    async def execute_gql(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        param_types_map: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously execute an ISO GQL query using database.snapshot().execute_sql()."""
        self._ensure_connected_sync()
        try:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(
                    None,
                    lambda: self.execute_gql_sync(query, parameters, param_types_map),
                )
            except RuntimeError:
                return self.execute_gql_sync(query, parameters, param_types_map)
        except Exception as exc:
            raise GraphQueryError(
                f"Cloud Spanner ISO GQL query failed: {exc}",
                details={"query_preview": query[:200]},
            ) from exc

    async def execute_read(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        param_types_map: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Compatible read interface executing ISO GQL or SQL against Spanner."""
        return await self.execute_gql(query, parameters, param_types_map)


# Module-level singletons
_neo4j_client: Neo4jClient | None = None
_spanner_graph_client: SpannerGraphClient | None = None


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


def get_spanner_graph_client() -> SpannerGraphClient:
    """Get or instantiate the Cloud Spanner Graph client singleton."""
    global _spanner_graph_client
    if _spanner_graph_client is None:
        _spanner_graph_client = SpannerGraphClient()
    return _spanner_graph_client


async def init_spanner_graph_client(settings: Settings | None = None) -> SpannerGraphClient:
    """Initialize and connect the Cloud Spanner Graph client singleton."""
    global _spanner_graph_client
    #_spanner_graph_client = SpannerGraphClient(settings)
    _spanner_graph_client = SpannerGraphClient(settings=settings)
    await _spanner_graph_client.connect()
    return _spanner_graph_client


async def close_spanner_graph_client() -> None:
    """Close the Cloud Spanner Graph client singleton."""
    global _spanner_graph_client
    if _spanner_graph_client:
        await _spanner_graph_client.close()
        _spanner_graph_client = None
