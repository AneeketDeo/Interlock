"""ClassifyAgent — PFMEA failure mode classification specialist."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Template

from app.agents.base import GEMINI_MODEL, RcaSessionState, build_mcp_toolset
from app.core.logging import get_logger

logger = get_logger(__name__)

_PROMPT_TEMPLATE = Template(
    (Path(__file__).parent / "prompts" / "classify_agent.j2").read_text()
)


def build_classify_agent() -> object:
    """Build the ClassifyAgent (PFMEA) LlmAgent instance."""
    from google.adk.agents import LlmAgent

    toolset = build_mcp_toolset()

    instruction = _PROMPT_TEMPLATE.render(
        diagnose_result="{{ " + RcaSessionState.DIAGNOSE_RESULT + " }}",
    )

    return LlmAgent(
        name="ClassifyAgent",
        description=(
            "Maps diagnosed failures to PFMEA ontology classes, assigns ISO 22400 "
            "classification codes, and computes Severity x Occurrence x Detection RPN scores."
        ),
        instruction=instruction,
        model=GEMINI_MODEL,
        tools=[toolset],
        output_key=RcaSessionState.CLASSIFY_RESULT,
    )
