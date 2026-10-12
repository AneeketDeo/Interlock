"""TimescaleDB async client using asyncpg.

Manages the connection pool, schema creation (hypertables for telemetry),
and provides typed query helpers. Raw telemetry lives here; only summaries
go into the knowledge graph.
"""

from __future__ import annotations

import contextlib
from datetime import datetime
from typing import Any

import asyncpg

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Schema DDL ──────────────────────────────────────────────────────

SCHEMA_DDL = """
-- Telemetry readings hypertable
CREATE TABLE IF NOT EXISTS telemetry_readings (
    time        TIMESTAMPTZ NOT NULL,
    sensor_id   TEXT        NOT NULL,
    tag         TEXT        NOT NULL,
    value       DOUBLE PRECISION NOT NULL,
    quality     INTEGER     DEFAULT 192
);

SELECT create_hypertable('telemetry_readings', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_telemetry_sensor_time
    ON telemetry_readings (sensor_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_telemetry_tag_time
    ON telemetry_readings (tag, time DESC);

-- Scrap/yield aggregated metrics
CREATE TABLE IF NOT EXISTS production_metrics (
    time              TIMESTAMPTZ NOT NULL,
    line_id           TEXT        NOT NULL,
    work_order_id     TEXT        NOT NULL,
    quantity_produced INTEGER     DEFAULT 0,
    quantity_scrapped INTEGER     DEFAULT 0,
    scrap_rate        DOUBLE PRECISION DEFAULT 0.0,
    fpy               DOUBLE PRECISION DEFAULT 1.0,
    oee               DOUBLE PRECISION DEFAULT 0.0
);

SELECT create_hypertable('production_metrics', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_production_line_time
    ON production_metrics (line_id, time DESC);

-- Ingestion quarantine table
CREATE TABLE IF NOT EXISTS quarantine (
    id              SERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    source_system   TEXT NOT NULL,
    record_type     TEXT NOT NULL,
    raw_data        JSONB NOT NULL,
    rejection_reason TEXT NOT NULL,
    pipeline_run_id  TEXT NOT NULL,
    resolved        BOOLEAN DEFAULT FALSE
);

-- Ingestion run history
CREATE TABLE IF NOT EXISTS ingestion_runs (
    id              TEXT PRIMARY KEY,
    started_at      TIMESTAMPTZ NOT NULL,
    completed_at    TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'running',
    source_system   TEXT NOT NULL,
    records_total   INTEGER DEFAULT 0,
    records_ingested INTEGER DEFAULT 0,
    records_rejected INTEGER DEFAULT 0,
    error_message   TEXT
);

-- Audit log (append-only)
CREATE TABLE IF NOT EXISTS audit_log (
    id              SERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    user_id         TEXT,
    user_role       TEXT,
    action          TEXT NOT NULL,
    resource_type   TEXT NOT NULL,
    resource_id     TEXT NOT NULL,
    details         JSONB,
    evidence_hash   TEXT,
    justification   TEXT
);

-- User accounts
CREATE TABLE IF NOT EXISTS user_accounts (
    id              TEXT PRIMARY KEY,
    username        TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role            TEXT NOT NULL,
    full_name       TEXT DEFAULT '',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
"""


class TimescaleClient:
    """Async TimescaleDB client with connection pool."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Create the connection pool and ensure schema exists."""
        self._pool = await asyncpg.create_pool(
            self._settings.timescale_dsn,
            min_size=2,
            max_size=20,
        )
        await self._ensure_schema()
        logger.info("timescaledb_connected", dsn=self._settings.timescale_dsn.split("@")[1])

    async def _ensure_schema(self) -> None:
        """Create tables and hypertables if they don't exist."""
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            # Enable TimescaleDB extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
            # Execute schema DDL statement by statement
            for statement in SCHEMA_DDL.split(";"):
                stmt = statement.strip()
                if stmt:
                    with contextlib.suppress(asyncpg.DuplicateObjectError):
                        await conn.execute(stmt + ";")

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("timescaledb_disconnected")

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("TimescaleDB pool not initialized. Call connect() first.")
        return self._pool

    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as exc:
            logger.warning("timescaledb_health_check_failed", error=str(exc))
            return False

    # ── Telemetry operations ────────────────────────────────────────

    async def insert_telemetry_batch(
        self, readings: list[tuple[datetime, str, str, float, int]]
    ) -> int:
        """Insert a batch of telemetry readings. Returns count inserted."""
        async with self.pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO telemetry_readings (time, sensor_id, tag, value, quality)
                VALUES ($1, $2, $3, $4, $5)
                """,
                readings,
            )
        return len(readings)

    async def get_telemetry_window(
        self,
        sensor_id: str,
        start: datetime,
        end: datetime,
        limit: int = 10000,
    ) -> list[dict[str, Any]]:
        """Get telemetry readings for a sensor in a time window."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT time, sensor_id, tag, value, quality
                FROM telemetry_readings
                WHERE sensor_id = $1 AND time >= $2 AND time <= $3
                ORDER BY time ASC
                LIMIT $4
                """,
                sensor_id, start, end, limit,
            )
        return [dict(r) for r in rows]

    # ── Production metrics ──────────────────────────────────────────

    async def insert_production_metrics(
        self, metrics: list[tuple[datetime, str, str, int, int, float, float, float]]
    ) -> int:
        """Insert production metric records."""
        async with self.pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO production_metrics
                    (time, line_id, work_order_id, quantity_produced,
                     quantity_scrapped, scrap_rate, fpy, oee)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                metrics,
            )
        return len(metrics)

    async def get_scrap_rate_series(
        self,
        line_id: str,
        start: datetime,
        end: datetime,
        bucket: str = "1 hour",
    ) -> list[dict[str, Any]]:
        """Get aggregated scrap rate time series."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT time_bucket($1::interval, time) AS bucket,
                       AVG(scrap_rate) AS avg_scrap_rate,
                       SUM(quantity_scrapped) AS total_scrapped,
                       SUM(quantity_produced) AS total_produced
                FROM production_metrics
                WHERE line_id = $2 AND time >= $3 AND time <= $4
                GROUP BY bucket
                ORDER BY bucket ASC
                """,
                bucket, line_id, start, end,
            )
        return [dict(r) for r in rows]

    # ── Quarantine ──────────────────────────────────────────────────

    async def quarantine_record(
        self,
        source_system: str,
        record_type: str,
        raw_data: dict[str, Any],
        rejection_reason: str,
        pipeline_run_id: str,
    ) -> None:
        """Insert a rejected record into quarantine."""
        import json

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO quarantine
                    (source_system, record_type, raw_data, rejection_reason, pipeline_run_id)
                VALUES ($1, $2, $3::jsonb, $4, $5)
                """,
                source_system, record_type, json.dumps(raw_data, default=str),
                rejection_reason, pipeline_run_id,
            )

    # ── Audit log ───────────────────────────────────────────────────

    async def append_audit_log(
        self,
        user_id: str | None,
        user_role: str | None,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any] | None = None,
        evidence_hash: str = "",
        justification: str = "",
    ) -> None:
        """Append an entry to the immutable audit log."""
        import json

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_log
                    (user_id, user_role, action, resource_type,
                     resource_id, details, evidence_hash, justification)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8)
                """,
                user_id, user_role, action, resource_type,
                resource_id,
                json.dumps(details or {}, default=str),
                evidence_hash, justification,
            )

    # ── Ingestion runs ──────────────────────────────────────────────

    async def create_ingestion_run(
        self,
        run_id: str,
        source_system: str,
    ) -> None:
        """Record the start of an ingestion run."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ingestion_runs (id, started_at, status, source_system)
                VALUES ($1, NOW(), 'running', $2)
                ON CONFLICT (id) DO NOTHING
                """,
                run_id, source_system,
            )

    async def complete_ingestion_run(
        self,
        run_id: str,
        status: str,
        records_total: int,
        records_ingested: int,
        records_rejected: int,
        error_message: str = "",
    ) -> None:
        """Record the completion of an ingestion run."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE ingestion_runs
                SET completed_at = NOW(), status = $2,
                    records_total = $3, records_ingested = $4,
                    records_rejected = $5, error_message = $6
                WHERE id = $1
                """,
                run_id, status, records_total, records_ingested,
                records_rejected, error_message,
            )


# Module-level singleton
_timescale_client: TimescaleClient | None = None


def get_timescale_client() -> TimescaleClient:
    """Get the module-level TimescaleDB client singleton."""
    if _timescale_client is None:
        raise RuntimeError("TimescaleDB client not initialized.")
    return _timescale_client


async def init_timescale_client(settings: Settings | None = None) -> TimescaleClient:
    """Initialize and return the module-level TimescaleDB client."""
    global _timescale_client
    _timescale_client = TimescaleClient(settings)
    await _timescale_client.connect()
    return _timescale_client


async def close_timescale_client() -> None:
    """Close the module-level TimescaleDB client."""
    global _timescale_client
    if _timescale_client:
        await _timescale_client.close()
        _timescale_client = None
