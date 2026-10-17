"""Shared agent infrastructure: ADK config, McpToolset factory, and session helpers."""

from __future__ import annotations

from typing import Any

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioServerParameters

import os

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

# ── Vertex AI Routing ────────────────────────────────────────────────
if getattr(settings, "use_vertex_ai", True):
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    if getattr(settings, "gcp_project_id", None):
        os.environ["GOOGLE_CLOUD_PROJECT"] = settings.gcp_project_id
    if getattr(settings, "gcp_location", None):
        os.environ["GOOGLE_CLOUD_LOCATION"] = settings.gcp_location

# ── Model constants ──────────────────────────────────────────────────

GEMINI_MODEL = getattr(settings, "gemini_model", "gemini-2.5-flash")

# ── McpToolset factory ───────────────────────────────────────────────


def build_mcp_toolset() -> McpToolset:
    """Construct a McpToolset that connects to the local FastMCP server via stdio."""
    cfg = get_settings()
    env = {
        "GCP_PROJECT_ID": getattr(cfg, "gcp_project_id", ""),
        "GCP_LOCATION": getattr(cfg, "gcp_location", "us-central1"),
        "SPANNER_INSTANCE_ID": getattr(cfg, "spanner_instance_id", ""),
        "SPANNER_DATABASE_ID": getattr(cfg, "spanner_database_id", ""),
        "SPANNER_GRAPH_NAME": getattr(cfg, "spanner_graph_name", "FactoryGraph"),
        "PUBSUB_TOPIC_ID": getattr(cfg, "pubsub_topic_id", ""),
        "BIGQUERY_DATASET": getattr(cfg, "bigquery_dataset", ""),
        "GOOGLE_GENAI_USE_VERTEXAI": "true" if getattr(cfg, "use_vertex_ai", True) else "false",
        "NEO4J_URI": getattr(cfg, "neo4j_uri", ""),
        "NEO4J_USERNAME": getattr(cfg, "neo4j_username", ""),
        "NEO4J_PASSWORD": getattr(cfg, "neo4j_password", ""),
        "REDIS_URL": getattr(cfg, "redis_url", ""),
    }
    return McpToolset(
        connection_params=StdioServerParameters(
            command="python",
            args=["-m", "app.mcp_server.server"],
            env=env,
        )
    )


# ── Shared output schema ─────────────────────────────────────────────


class RcaSessionState:
    """Keys used in the shared ADK session state across all agents in the pipeline."""

    INCIDENT_ID = "incident_id"
    LINE_ID = "line_id"
    MACHINE_ID = "machine_id"
    CULPRIT_LOT_ID = "culprit_lot_id"

    # Agent outputs written to session state
    DETECT_RESULT = "detect_result"
    DIAGNOSE_RESULT = "diagnose_result"
    CLASSIFY_RESULT = "classify_result"
    FORECAST_RESULT = "forecast_result"
    REMEDIATE_RESULT = "remediate_result"


# ── Minimal typed agent factory ──────────────────────────────────────


def make_llm_agent(
    name: str,
    description: str,
    instruction: str,
    output_key: str,
    tool_names: list[str] | None = None,
) -> LlmAgent:
    """Create a configured LlmAgent with the shared MCP toolset."""
    toolset = build_mcp_toolset()

    agent_kwargs: dict[str, Any] = {
        "name": name,
        "description": description,
        "instruction": instruction,
        "model": GEMINI_MODEL,
        "tools": [toolset],
        "output_key": output_key,
    }

    logger.info(
        "agent_created",
        name=name,
        model=GEMINI_MODEL,
        tool_filter=tool_names,
    )
    return LlmAgent(**agent_kwargs)
