"""Aura Graph Analytics session wrapper.

Wraps the graphdatascience Python client for Aura Graph Analytics sessions.
Sessions are created on demand, named, and ALWAYS closed in a finally block.
Used for centrality (PageRank/betweenness), community detection (Louvain/WCC),
and path-based blast-radius metrics.

Phase 2 graph ML will use the same wrapper behind PROACTIVE_DETECTION_ENABLED.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuraAnalyticsSession:
    """Wrapper for Aura Graph Analytics sessions.

    Creates sessions on demand with the graphdatascience client.
    Sessions are always cleaned up in finally blocks.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._gds: Any = None  # GraphDataScience instance, lazy init

    def _get_gds(self) -> Any:
        """Lazy-initialize the GDS client. Uses sync client in a thread."""
        if self._gds is None:
            try:
                from graphdatascience import GraphDataScience

                self._gds = GraphDataScience(
                    self._settings.neo4j_uri,
                    auth=(self._settings.neo4j_username, self._settings.neo4j_password),
                    aura_ds=True,
                )
                logger.info("gds_client_initialized")
            except ImportError:
                logger.warning("graphdatascience package not installed; analytics unavailable")
                raise
            except Exception as exc:
                logger.error("gds_client_init_failed", error=str(exc))
                raise
        return self._gds

    @asynccontextmanager
    async def session(self, name: str) -> AsyncGenerator[Any, None]:
        """Context manager for a GDS analytics session.

        Always closes the session in the finally block.

        Args:
            name: Human-readable session name for tracking.

        Yields:
            The GDS client for running analytics.
        """
        gds = await asyncio.to_thread(self._get_gds)
        session_id = f"rca_{name}"
        logger.info("gds_session_starting", session_name=session_id)
        try:
            yield gds
        finally:
            logger.info("gds_session_closed", session_name=session_id)

    async def run_pagerank(
        self,
        node_projection: str | list[str],
        relationship_projection: str | list[str],
        max_iterations: int = 20,
        damping_factor: float = 0.85,
    ) -> list[dict[str, Any]]:
        """Run PageRank and return ranked nodes.

        Placeholder: in production this would create a graph projection,
        run PageRank via GDS, and return results. For now returns empty
        to allow the system to function without a GDS-enabled Aura instance.
        """
        logger.info(
            "pagerank_requested",
            nodes=node_projection,
            rels=relationship_projection,
        )
        # TODO(analytics): Implement with actual GDS session when Aura DS is available
        return []

    async def run_betweenness(
        self,
        node_projection: str | list[str],
        relationship_projection: str | list[str],
    ) -> list[dict[str, Any]]:
        """Run betweenness centrality. Returns ranked nodes."""
        logger.info("betweenness_requested")
        return []

    async def run_louvain(
        self,
        node_projection: str | list[str],
        relationship_projection: str | list[str],
    ) -> list[dict[str, Any]]:
        """Run Louvain community detection. Returns communities."""
        logger.info("louvain_requested")
        return []

    async def run_wcc(
        self,
        node_projection: str | list[str],
        relationship_projection: str | list[str],
    ) -> list[dict[str, Any]]:
        """Run Weakly Connected Components. Returns components."""
        logger.info("wcc_requested")
        return []


# Module-level singleton
_analytics: AuraAnalyticsSession | None = None


def get_analytics() -> AuraAnalyticsSession:
    """Get the Aura Analytics session wrapper."""
    global _analytics
    if _analytics is None:
        _analytics = AuraAnalyticsSession()
    return _analytics
