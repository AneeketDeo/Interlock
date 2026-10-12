"""Exponentially Weighted Moving Average (EWMA) control chart detector.

EWMA smooths out noise while responding promptly to persistent mean shifts:
Z_t = lambda * X_t + (1 - lambda) * Z_{t-1}
Control limits: mu0 +/- L * sigma * sqrt(lambda / (2 - lambda))
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

from app.detection.base import AnomalySignal, BaseDetector


class EwmaDetector(BaseDetector):
    """Detects shifts in process mean using an EWMA filter."""

    def __init__(
        self,
        name: str = "EWMA",
        lambda_param: float = 0.2,
        l_sigma: float = 3.0,
        warmup_samples: int = 20,
    ) -> None:
        super().__init__(name=name, threshold=l_sigma)
        self.lambda_param = lambda_param
        self.l_sigma = l_sigma
        self.warmup_samples = warmup_samples

        self._ewma: float | None = None
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

        # Warmup phase: calculate running mean and variance
        if self._count <= self.warmup_samples:
            self._mean = sum(self._history) / len(self._history)
            variance = sum((x - self._mean) ** 2 for x in self._history) / max(1, len(self._history) - 1)
            self._variance = max(1e-6, variance)
            self._ewma = self._mean
            return None

        std_dev = math.sqrt(self._variance)
        assert self._ewma is not None

        # Update EWMA
        self._ewma = self.lambda_param * value + (1.0 - self.lambda_param) * self._ewma

        # Control limit threshold
        factor = math.sqrt(self.lambda_param / (2.0 - self.lambda_param))
        sigma_limit = self.l_sigma * std_dev * factor
        upper_limit = self._mean + sigma_limit
        lower_limit = self._mean - sigma_limit

        deviation = abs(self._ewma - self._mean)
        if self._ewma > upper_limit or self._ewma < lower_limit:
            score = min(1.0, deviation / max(1e-6, sigma_limit * 1.5))
            return AnomalySignal(
                sensor_id=sensor_id,
                metric=metric,
                timestamp=ts,
                value=round(value, 3),
                baseline=round(self._mean, 3),
                threshold=round(upper_limit if self._ewma > upper_limit else lower_limit, 3),
                score=round(score, 3),
                detector_name=self.name,
                details={
                    "ewma_value": round(self._ewma, 3),
                    "sigma_limit": round(sigma_limit, 3),
                    "upper_limit": round(upper_limit, 3),
                    "lower_limit": round(lower_limit, 3),
                },
            )

        return None

    def reset(self) -> None:
        self._ewma = None
        self._mean = 0.0
        self._variance = 0.0
        self._count = 0
        self._history.clear()
