"""Cumulative Sum (CUSUM) control chart detector.

Detects small persistent shifts and abrupt steps:
S_high[t] = max(0, S_high[t-1] + (x_t - mu - k))
S_low[t]  = max(0, S_low[t-1] - (x_t - mu + k))
Alarm when S_high[t] > h or S_low[t] > h.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

from app.detection.base import AnomalySignal, BaseDetector


class CusumDetector(BaseDetector):
    """Cumulative Sum (CUSUM) change-point detector."""

    def __init__(
        self,
        name: str = "CUSUM",
        k_slack: float = 0.5,  # Slack parameter (multiples of sigma)
        h_threshold: float = 4.0,  # Decision interval threshold
        warmup_samples: int = 20,
    ) -> None:
        super().__init__(name=name, threshold=h_threshold)
        self.k_slack = k_slack
        self.h_threshold = h_threshold
        self.warmup_samples = warmup_samples

        self._s_high: float = 0.0
        self._s_low: float = 0.0
        self._mean: float = 0.0
        self._variance: float = 0.0
        self._count: int = 0
        self._history: list[float] = []

    def update(
        self,
        value: float,
        timestamp: datetime | None = None,
        sensor_id: str = "sensor",
        metric: str = "value",
    ) -> AnomalySignal | None:
        ts = timestamp or datetime.now(UTC)
        self._count += 1
        self._history.append(value)

        # Warmup phase
        if self._count <= self.warmup_samples:
            self._mean = sum(self._history) / len(self._history)
            variance = sum((x - self._mean) ** 2 for x in self._history) / max(1, len(self._history) - 1)
            self._variance = max(1e-6, variance)
            return None

        std_dev = math.sqrt(self._variance)
        slack = self.k_slack * std_dev
        threshold_val = self.h_threshold * std_dev

        # Update high and low CUSUM statistics
        self._s_high = max(0.0, self._s_high + (value - self._mean - slack))
        self._s_low = max(0.0, self._s_low - (value - self._mean + slack))

        if self._s_high > threshold_val or self._s_low > threshold_val:
            stat = max(self._s_high, self._s_low)
            score = min(1.0, stat / (threshold_val * 2.0))
            return AnomalySignal(
                sensor_id=sensor_id,
                metric=metric,
                timestamp=ts,
                value=round(value, 3),
                baseline=round(self._mean, 3),
                threshold=round(self._mean + threshold_val if self._s_high > threshold_val else self._mean - threshold_val, 3),
                score=round(score, 3),
                detector_name=self.name,
                details={
                    "s_high": round(self._s_high, 3),
                    "s_low": round(self._s_low, 3),
                    "threshold_val": round(threshold_val, 3),
                },
            )

        return None

    def reset(self) -> None:
        self._s_high = 0.0
        self._s_low = 0.0
        self._mean = 0.0
        self._variance = 0.0
        self._count = 0
        self._history.clear()
