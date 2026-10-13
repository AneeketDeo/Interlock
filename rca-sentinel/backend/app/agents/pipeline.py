"""Root SequentialAgent pipeline — orchestrates the five-stage RCA Evidence Package."""

from __future__ import annotations

from typing import Any

from google.adk.agents import SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.base import RcaSessionState
from app.agents.callbacks import after_model_callback, before_agent_callback
from app.agents.classify_agent import build_classify_agent
from app.agents.detect_agent import build_detect_agent
from app.agents.diagnose_agent import build_diagnose_agent
from app.agents.forecast_agent import build_forecast_agent
from app.agents.remediate_agent import build_remediate_agent
from app.core.logging import get_logger

logger = get_logger(__name__)

APP_NAME = "rca-sentinel"


def build_rca_pipeline() -> SequentialAgent:
    """Assemble the five-agent SequentialAgent RCA pipeline."""
    detect = build_detect_agent()
    diagnose = build_diagnose_agent()
    classify = build_classify_agent()
    forecast = build_forecast_agent()
    remediate = build_remediate_agent()

    # Wire guardrail callbacks onto each sub-agent
    for agent in [detect, diagnose, classify, forecast, remediate]:
        agent.before_agent_callback = before_agent_callback  # type: ignore[attr-defined]
        agent.after_model_callback = after_model_callback  # type: ignore[attr-defined]

    pipeline = SequentialAgent(
        name="RcaSentinelPipeline",
        description=(
            "Five-stage RCA pipeline: Detect → Diagnose → Classify → Forecast → Remediate. "
            "Produces a complete RCA Evidence Package with mandatory human approval gating."
        ),
        sub_agents=[detect, diagnose, classify, forecast, remediate],
    )

    logger.info("rca_pipeline_assembled", stages=5)
    return pipeline


async def run_rca_pipeline(
    incident_id: str,
    line_id: str = "line-03",
    machine_id: str = "station-03b",
    culprit_lot_id: str = "lot-40921",
) -> dict[str, Any]:
    """Execute the full RCA pipeline for a given incident.

    Returns:
        Complete RCA Evidence Package dict with all five stage results.
    """
    pipeline = build_rca_pipeline()

    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id="system",
        state={
            RcaSessionState.INCIDENT_ID: incident_id,
            RcaSessionState.LINE_ID: line_id,
            RcaSessionState.MACHINE_ID: machine_id,
            RcaSessionState.CULPRIT_LOT_ID: culprit_lot_id,
        },
    )

    runner = Runner(
        agent=pipeline,
        app_name=APP_NAME,
        session_service=session_service,
    )

    logger.info(
        "rca_pipeline_run_started",
        incident_id=incident_id,
        line_id=line_id,
        machine_id=machine_id,
    )

    final_events: list[Any] = []
    async for event in runner.run_async(
        user_id="system",
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[
                types.Part(
                    text=(
                        f"Run full RCA pipeline for incident {incident_id} "
                        f"on line {line_id}, machine {machine_id}."
                    )
                )
            ],
        ),
    ):
        final_events.append(event)

    # Retrieve final session state
    completed_session = session_service.get_session(
        app_name=APP_NAME, user_id="system", session_id=session.id
    )

    state = completed_session.state if completed_session else {}

    evidence_package = {
        "incident_id": incident_id,
        "pipeline": "RcaSentinelPipeline",
        "stages": {
            "detect": state.get(RcaSessionState.DETECT_RESULT),
            "diagnose": state.get(RcaSessionState.DIAGNOSE_RESULT),
            "classify": state.get(RcaSessionState.CLASSIFY_RESULT),
            "forecast": state.get(RcaSessionState.FORECAST_RESULT),
            "remediate": state.get(RcaSessionState.REMEDIATE_RESULT),
        },
    }

    logger.info(
        "rca_pipeline_run_completed",
        incident_id=incident_id,
        stages_completed=sum(1 for v in evidence_package["stages"].values() if v),
    )

    return evidence_package
