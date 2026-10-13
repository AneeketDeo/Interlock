"""RemediateAgent — D3 containment + D5 corrective action proposal specialist."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Template

from app.agents.base import GEMINI_MODEL, RcaSessionState, build_mcp_toolset
from app.core.logging import get_logger

logger = get_logger(__name__)

_PROMPT_TEMPLATE = Template(
    (Path(__file__).parent / "prompts" / "remediate_agent.j2").read_text()
)


def build_remediate_agent() -> object:
    """Build the RemediateAgent (D3+D5) LlmAgent instance."""
    from google.adk.agents import LlmAgent

    toolset = build_mcp_toolset()

    instruction = _PROMPT_TEMPLATE.render(
        diagnose_result="{{ " + RcaSessionState.DIAGNOSE_RESULT + " }}",
        classify_result="{{ " + RcaSessionState.CLASSIFY_RESULT + " }}",
        forecast_result="{{ " + RcaSessionState.FORECAST_RESULT + " }}",
        incident_id="{{ " + RcaSessionState.INCIDENT_ID + " }}",
        machine_id="{{ " + RcaSessionState.MACHINE_ID + " }}",
        culprit_lot_id="{{ " + RcaSessionState.CULPRIT_LOT_ID + " }}",
    )

    return LlmAgent(
        name="RemediateAgent",
        description=(
            "Proposes equipment interlocks, ERP quarantines, and CMMS work orders — "
            "all as pending_approval actions requiring mandatory human sign-off."
        ),
        instruction=instruction,
        model=GEMINI_MODEL,
        tools=[toolset],
        output_key=RcaSessionState.REMEDIATE_RESULT,
    )
