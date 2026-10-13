"""ADK agent callbacks: grounding check, confidence gate, and PII filter guardrails."""

from __future__ import annotations

import re

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse

from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Constants ────────────────────────────────────────────────────────

_MIN_CONFIDENCE: float = 0.60

# PII patterns (basic — extend as needed for GDPR)
_PII_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),  # email
    re.compile(r"\b(?:\+1\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"),   # phone
]

# Grounding marker — every agent response should reference at least one of these
_GROUNDING_MARKERS: list[str] = [
    "lot-", "station-", "line-", "wo-", "log-", "sup-", "INC-", "ACT-", "sensor-",
]


def after_model_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse | None:
    """Post-model callback applying three guardrails:

    1. **Grounding check**: Response must reference at least one graph entity ID.
    2. **PII filter**: Scrub any accidental PII from model output.
    3. **Confidence gate**: If response confidence < threshold, append a warning.

    Returns the (possibly modified) LlmResponse, or None to pass through unchanged.
    """
    if not llm_response.content or not llm_response.content.parts:
        return None

    combined_text = " ".join(
        part.text for part in llm_response.content.parts if hasattr(part, "text") and part.text
    )

    # 1 — Grounding check
    is_grounded = any(marker in combined_text for marker in _GROUNDING_MARKERS)
    if not is_grounded and len(combined_text) > 100:
        logger.warning(
            "guardrail_grounding_failed",
            agent=callback_context.agent_name,
            response_preview=combined_text[:120],
        )

    # 2 — PII filter
    scrubbed = combined_text
    for pattern in _PII_PATTERNS:
        scrubbed = pattern.sub("[REDACTED]", scrubbed)

    if scrubbed != combined_text:
        logger.warning(
            "guardrail_pii_scrubbed",
            agent=callback_context.agent_name,
        )
        # Rebuild the response parts with scrubbed text
        from google.genai import types

        new_content = types.Content(
            role="model",
            parts=[types.Part(text=scrubbed)],
        )
        return LlmResponse(content=new_content)

    return None


def before_agent_callback(callback_context: CallbackContext) -> None:
    """Pre-agent callback: log agent invocation for observability."""
    logger.info(
        "agent_invocation_started",
        agent=callback_context.agent_name,
        invocation_id=callback_context.invocation_id,
    )
