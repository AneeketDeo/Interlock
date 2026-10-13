"""Shared agent infrastructure: ADK config, McpToolset factory, and session helpers."""

from __future__ import annotations

from typing import Any

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioServerParameters

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Model constants ──────────────────────────────────────────────────

GEMINI_MODEL = "gemini-2.5-flash"

# ── McpToolset factory ───────────────────────────────────────────────


def build_mcp_toolset() -> McpToolset:
    """Construct a McpToolset that connects to the local FastMCP server via stdio."""
    settings = get_settings()
    return McpToolset(
        connection_params=StdioServerParameters(
            command="python",
            args=["-m", "app.mcp_server.server"],
            env={
                "NEO4J_URI": settings.NEO4J_URI,
                "NEO4J_USER": settings.NEO4J_USER,
                "NEO4J_PASSWORD": settings.NEO4J_PASSWORD.get_secret_value(),
                "REDIS_URL": settings.REDIS_URL,
            },
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
