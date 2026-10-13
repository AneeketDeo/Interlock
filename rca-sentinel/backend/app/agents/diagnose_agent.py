"""DiagnoseAgent — D4 root cause diagnosis specialist."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Template

from app.agents.base import GEMINI_MODEL, RcaSessionState, build_mcp_toolset
from app.core.logging import get_logger

logger = get_logger(__name__)

_PROMPT_TEMPLATE = Template(
    (Path(__file__).parent / "prompts" / "diagnose_agent.j2").read_text()
)


def build_diagnose_agent() -> object:
    """Build the DiagnoseAgent (D4) LlmAgent instance."""
    from google.adk.agents import LlmAgent

    toolset = build_mcp_toolset()

    instruction = _PROMPT_TEMPLATE.render(
        line_id="{{ " + RcaSessionState.LINE_ID + " }}",
        machine_id="{{ " + RcaSessionState.MACHINE_ID + " }}",
        detect_result="{{ " + RcaSessionState.DETECT_RESULT + " }}",
    )

    return LlmAgent(
        name="DiagnoseAgent",
        description=(
            "Performs multi-hop backward traversal to identify primary and compounding "
            "root causes — culprit material lots and maintenance miscalibrations."
        ),
        instruction=instruction,
        model=GEMINI_MODEL,
        tools=[toolset],
        output_key=RcaSessionState.DIAGNOSE_RESULT,
    )
