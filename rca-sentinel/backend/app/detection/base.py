"""Detector abstractions and registry for reactive telemetry monitoring."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class AnomalySignal:
    """Represents an anomaly signal emitted by a detector."""

    sensor_id: str
    metric: str
    timestamp: datetime
    value: float
    baseline: float
    threshold: float
    score: float  # Normalized anomaly confidence (0.0 to 1.0)
    detector_name: str
    details: dict[str, Any] = field(default_factory=dict)


class BaseDetector(ABC):
    """Abstract base class for all statistical and rule-based detectors."""

    def __init__(self, name: str, threshold: float = 3.0) -> None:
        self.name = name
        self.threshold = threshold

    @abstractmethod
    def update(
        self,
        value: float,
        timestamp: datetime | None = None,
        sensor_id: str = "sensor",
        metric: str = "value",
    ) -> AnomalySignal | None:
        """Process a single reading and return AnomalySignal if triggered."""

    @abstractmethod
    def reset(self) -> None:
        """Reset internal state/history."""


class DetectorRegistry:
    """Registry managing active detectors per sensor and tag."""

    def __init__(self) -> None:
        self._detectors: dict[str, list[BaseDetector]] = {}

    def register(self, sensor_id: str, detector: BaseDetector) -> None:
        """Attach a detector to a sensor."""
        if sensor_id not in self._detectors:
            self._detectors[sensor_id] = []
        self._detectors[sensor_id].append(detector)

    def get_detectors(self, sensor_id: str) -> list[BaseDetector]:
        """Retrieve all detectors registered for a sensor."""
        return self._detectors.get(sensor_id, [])

    def process_reading(
        self,
        sensor_id: str,
        metric: str,
        value: float,
        timestamp: datetime | None = None,
    ) -> list[AnomalySignal]:
        """Run all registered detectors for a sensor reading."""
        ts = timestamp or datetime.now(UTC)
        signals: list[AnomalySignal] = []
        for det in self.get_detectors(sensor_id):
            sig = det.update(value, timestamp=ts, sensor_id=sensor_id, metric=metric)
            if sig:
                signals.append(sig)
        return signals

    def reset_all(self) -> None:
        """Reset all registered detectors."""
        for detector_list in self._detectors.values():
            for d in detector_list:
                d.reset()
