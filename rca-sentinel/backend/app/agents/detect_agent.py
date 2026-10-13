"""DetectAgent — D2 anomaly confirmation specialist."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Template

from app.agents.base import GEMINI_MODEL, RcaSessionState, build_mcp_toolset
from app.core.logging import get_logger

logger = get_logger(__name__)

_PROMPT_TEMPLATE = Template(
    (Path(__file__).parent / "prompts" / "detect_agent.j2").read_text()
)


def build_detect_agent() -> object:
    """Build the DetectAgent (D2) LlmAgent instance."""
    from google.adk.agents import LlmAgent

    toolset = build_mcp_toolset()

    instruction = _PROMPT_TEMPLATE.render(
        line_id="{{ " + RcaSessionState.LINE_ID + " }}",
        machine_id="{{ " + RcaSessionState.MACHINE_ID + " }}",
        incident_id="{{ " + RcaSessionState.INCIDENT_ID + " }}",
    )

    return LlmAgent(
        name="DetectAgent",
        description=(
            "Confirms anomaly validity using live machine subgraph data "
            "and returns structured incident confirmation."
        ),
        instruction=instruction,
        model=GEMINI_MODEL,
        tools=[toolset],
        output_key=RcaSessionState.DETECT_RESULT,
    )
