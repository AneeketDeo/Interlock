"""Health check endpoints.

/health/live — basic liveness (always 200 if the process is up).
/health/ready — readiness with connectivity checks for Google Cloud Spanner Graph,
Google BigQuery, Google Cloud Pub/Sub, and Vertex AI.
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
    """Readiness probe — all core GCP dependencies are reachable."""
    settings = get_settings()
    checks: dict[str, bool] = {}

    # 1. Google Cloud Spanner Graph check
    try:
        from app.graph.client import get_spanner_graph_client

        spanner = get_spanner_graph_client()
        checks["spanner_graph"] = await spanner.health_check()
    except Exception as exc:
        logger.warning("spanner_health_check_failed", error=str(exc))
        checks["spanner_graph"] = False

    # 2. Google Cloud Pub/Sub check
    try:
        from google.cloud import pubsub_v1

        subscriber = pubsub_v1.SubscriberClient()
        sub_path = subscriber.subscription_path(
            settings.gcp_project_id, settings.pubsub_subscription_id
        )
        checks["pubsub"] = bool(sub_path)
    except Exception:
        checks["pubsub"] = False

    # 3. Google BigQuery Historian check
    try:
        checks["bigquery"] = bool(
            settings.gcp_project_id and settings.bigquery_dataset and settings.bigquery_table
        )
    except Exception:
        checks["bigquery"] = False

    # 4. Google Vertex AI / ADK
    checks["vertex_ai"] = bool(settings.gcp_project_id and settings.use_vertex_ai)

    # Legacy checks (optional fallback)
    if getattr(settings, "neo4j_password", None) and settings.neo4j_password != "":
        try:
            from app.graph.client import get_neo4j_client

            neo4j = get_neo4j_client()
            checks["neo4j_aura"] = await neo4j.health_check()
        except Exception:
            checks["neo4j_aura"] = False

    all_healthy = all(checks.values())
    status_str = "ok" if all_healthy else "degraded"

    return HealthStatus(
        status=status_str,
        version=settings.app_version,
        environment=settings.app_env,
        checks=checks,
    )
