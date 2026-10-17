"""FastMCP server exposing manufacturing ontology, diagnostic reasoning, and remediation tools."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from app.core.config import get_settings
from app.mcp_server.action_tools import (
    propose_cmms_work_order,
    propose_equipment_interlock,
    propose_erp_quarantine,
)
from app.mcp_server.graph_tools import (
    get_machine_subgraph,
    get_maintenance_history,
    get_operator_logs,
    trace_lot_provenance,
)
from app.mcp_server.impact_tools import (
    calculate_blast_radius,
    diagnose_root_cause,
    forecast_financial_impact,
)
from app.mcp_server.resources import (
    get_active_incidents,
    get_failure_mode_catalog,
    get_ontology_summary,
)

settings = get_settings()

mcp = FastMCP(
    "RCA-Sentinel-MCP",
    instructions=(
        "Native Google Cloud MCP server for RCA-Sentinel. Powered by Google Cloud Spanner "
        "Property Graph (FactoryGraph) with ISO GQL multi-hop graph traversal tools: "
        "get_machine_subgraph, trace_lot_provenance, and diagnose_root_cause."
    ),
)

# ── Register Tools ──────────────────────────────────────────────────

mcp.tool()(get_machine_subgraph)
mcp.tool()(trace_lot_provenance)
mcp.tool()(get_maintenance_history)
mcp.tool()(get_operator_logs)

mcp.tool()(diagnose_root_cause)
mcp.tool()(calculate_blast_radius)
mcp.tool()(forecast_financial_impact)

mcp.tool()(propose_equipment_interlock)
mcp.tool()(propose_erp_quarantine)
mcp.tool()(propose_cmms_work_order)

# ── Register Resources ──────────────────────────────────────────────


@mcp.resource("manufacturing://ontology")
async def resource_ontology() -> dict[str, Any]:
    """Manufacturing OWL ontology class and relation summary."""
    return await get_ontology_summary()


@mcp.resource("manufacturing://incidents")
async def resource_incidents() -> list[dict[str, Any]]:
    """List of all active incidents."""
    return await get_active_incidents()


@mcp.resource("manufacturing://pfmea")
async def resource_pfmea() -> list[dict[str, Any]]:
    """PFMEA Failure Mode catalog and RPN ratings."""
    return await get_failure_mode_catalog()


if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
    )
