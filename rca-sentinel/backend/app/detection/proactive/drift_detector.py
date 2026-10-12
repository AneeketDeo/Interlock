"""Proactive drift and tool wear prediction stub (Phase 2 feature flag).

Active only when settings.proactive_detection_enabled is True.
Provides predictive maintenance early warning before catastrophic scrap events.
"""

from __future__ import annotations

from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProactiveDriftDetector:
    """Predictive drift detector stub for tool wear and bearing degradation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def is_enabled(self) -> bool:
        return self.settings.proactive_detection_enabled

    def predict_drift(
        self, sensor_id: str, readings: list[float]
    ) -> dict[str, Any] | None:
        """Evaluate readings for subtle linear drift indicating tool wear."""
        if not self.is_enabled:
            return None

        if len(readings) < 10:
            return None

        # Simple linear slope check
        n = len(readings)
        x_mean = (n - 1) / 2.0
        y_mean = sum(readings) / n
        slope = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(readings)) / max(
            1e-6, sum((i - x_mean) ** 2 for i in range(n))
        )

        if slope > 0.05:
            return {
                "sensor_id": sensor_id,
                "warning": "predicted_tool_wear_drift",
                "slope": round(slope, 4),
                "predicted_time_to_threshold_hours": round(max(1.0, 10.0 / (slope * 60)), 1),
            }

        return None
