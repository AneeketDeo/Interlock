"""ForecastAgent — blast radius and financial impact forecasting specialist."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Template

from app.agents.base import GEMINI_MODEL, RcaSessionState, build_mcp_toolset
from app.core.logging import get_logger

logger = get_logger(__name__)

_PROMPT_TEMPLATE = Template(
    (Path(__file__).parent / "prompts" / "forecast_agent.j2").read_text()
)


def build_forecast_agent() -> object:
    """Build the ForecastAgent LlmAgent instance."""
    from google.adk.agents import LlmAgent

    toolset = build_mcp_toolset()

    instruction = _PROMPT_TEMPLATE.render(
        diagnose_result="{{ " + RcaSessionState.DIAGNOSE_RESULT + " }}",
        classify_result="{{ " + RcaSessionState.CLASSIFY_RESULT + " }}",
        culprit_lot_id="{{ " + RcaSessionState.CULPRIT_LOT_ID + " }}",
        machine_id="{{ " + RcaSessionState.MACHINE_ID + " }}",
    )

    return LlmAgent(
        name="ForecastAgent",
        description=(
            "Computes forward blast radius from the culprit lot/machine and models "
            "itemized financial exposure including supplier chargeback recovery."
        ),
        instruction=instruction,
        model=GEMINI_MODEL,
        tools=[toolset],
        output_key=RcaSessionState.FORECAST_RESULT,
    )
