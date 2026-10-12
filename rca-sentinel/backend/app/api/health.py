"""Health check endpoints.

/health/live — basic liveness (always 200 if the process is up).
/health/ready — readiness with connectivity checks for Neo4j Aura,
Redis, and TimescaleDB. Returns a clear error if Aura is unreachable
or paused.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.models import HealthStatus

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health/live", response_model=HealthStatus)
async def liveness() -> HealthStatus:
    """Liveness probe — the process is running."""
    settings = get_settings()
    return HealthStatus(
        status="ok",
        version=settings.app_version,
        environment=settings.app_env,
    )


@router.get("/health/ready", response_model=HealthStatus)
async def readiness() -> HealthStatus:
    """Readiness probe — all dependencies are reachable."""
    settings = get_settings()
    checks: dict[str, bool] = {}

    # Neo4j Aura check
    try:
        from app.graph.client import get_neo4j_client

        neo4j = get_neo4j_client()
        checks["neo4j_aura"] = await neo4j.health_check()
    except Exception:
        checks["neo4j_aura"] = False

    # Redis check
    try:
        from app.core.redis import get_redis_client

        redis = get_redis_client()
        checks["redis"] = await redis.health_check()
    except Exception:
        checks["redis"] = False

    # TimescaleDB check
    try:
        from app.core.database import get_timescale_client

        ts = get_timescale_client()
        checks["timescaledb"] = await ts.health_check()
    except Exception:
        checks["timescaledb"] = False

    all_healthy = all(checks.values())
    status_str = "ok" if all_healthy else "degraded"

    if not checks.get("neo4j_aura"):
        logger.warning(
            "neo4j_aura_unreachable",
            message="Neo4j Aura instance may be paused or unreachable. "
            "Check NEO4J_URI and ensure the instance is running.",
        )

    return HealthStatus(
        status=status_str,
        version=settings.app_version,
        environment=settings.app_env,
        checks=checks,
    )
