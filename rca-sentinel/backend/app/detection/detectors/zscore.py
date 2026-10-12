"""Rolling Z-score outlier detector."""

from __future__ import annotations

import math
from collections import deque
from datetime import UTC, datetime

from app.detection.base import AnomalySignal, BaseDetector


class RollingZScoreDetector(BaseDetector):
    """Detects statistical outliers using a rolling window Z-score: z = (x - mu) / sigma."""

    def __init__(
        self,
        name: str = "RollingZScore",
        window_size: int = 30,
        z_threshold: float = 3.0,
    ) -> None:
        super().__init__(name=name, threshold=z_threshold)
        self.window_size = window_size
        self.z_threshold = z_threshold
        self._window: deque[float] = deque(maxlen=window_size)

    def update(
        self,
        value: float,
        timestamp: datetime | None = None,
        sensor_id: str = "sensor",
        metric: str = "value",
    ) -> AnomalySignal | None:
        ts = timestamp or datetime.now(UTC)

        if len(self._window) < max(5, self.window_size // 2):
            self._window.append(value)
            return None

        # Calculate mean and standard deviation from current window
        mean = sum(self._window) / len(self._window)
        variance = sum((x - mean) ** 2 for x in self._window) / len(self._window)
        std_dev = math.sqrt(max(1e-6, variance))

        z_score = abs(value - mean) / std_dev
        self._window.append(value)

        if z_score >= self.z_threshold:
            score = min(1.0, z_score / (self.z_threshold * 2.0))
            threshold_val = mean + (self.z_threshold * std_dev if value > mean else -self.z_threshold * std_dev)
            return AnomalySignal(
                sensor_id=sensor_id,
                metric=metric,
                timestamp=ts,
                value=round(value, 3),
                baseline=round(mean, 3),
                threshold=round(threshold_val, 3),
                score=round(score, 3),
                detector_name=self.name,
                details={
                    "z_score": round(z_score, 2),
                    "window_mean": round(mean, 3),
                    "window_std": round(std_dev, 3),
                },
            )

        return None

    def reset(self) -> None:
        self._window.clear()
