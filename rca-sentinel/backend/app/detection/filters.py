"""False-positive filters for industrial telemetry anomaly detection."""

from __future__ import annotations

from collections import deque

from app.detection.base import AnomalySignal


class ConsecutiveSignalFilter:
    """Requires N consecutive anomaly detections from the same sensor to confirm an incident."""

    def __init__(self, min_consecutive: int = 3, max_gap_seconds: float = 600.0) -> None:
        self.min_consecutive = min_consecutive
        self.max_gap_seconds = max_gap_seconds
        self._history: dict[str, deque[AnomalySignal]] = {}

    def filter(self, signal: AnomalySignal) -> AnomalySignal | None:
        """Return the confirmed signal if min_consecutive met; else None."""
        sensor_id = signal.sensor_id
        if sensor_id not in self._history:
            self._history[sensor_id] = deque(maxlen=self.min_consecutive)

        q = self._history[sensor_id]

        # Check gap between last signal and this one
        if q:
            last_sig = q[-1]
            gap = (signal.timestamp - last_sig.timestamp).total_seconds()
            if gap > self.max_gap_seconds:
                q.clear()  # Stale, reset consecutive count

        q.append(signal)

        if len(q) >= self.min_consecutive:
            # Confirmed incident trigger
            avg_score = sum(s.score for s in q) / len(q)
            confirmed = AnomalySignal(
                sensor_id=signal.sensor_id,
                metric=signal.metric,
                timestamp=signal.timestamp,
                value=signal.value,
                baseline=signal.baseline,
                threshold=signal.threshold,
                score=round(avg_score, 3),
                detector_name=f"{signal.detector_name}_CONFIRMED",
                details={
                    **signal.details,
                    "consecutive_count": len(q),
                    "first_detected_at": q[0].timestamp.isoformat(),
                },
            )
            return confirmed

        return None

    def reset_sensor(self, sensor_id: str) -> None:
        if sensor_id in self._history:
            self._history[sensor_id].clear()

    def reset_all(self) -> None:
        self._history.clear()


class QualityCheckFilter:
    """Rejects signals if sensor quality code indicates bad or uncertain status (<192)."""

    @staticmethod
    def is_valid_quality(quality_code: int) -> bool:
        # OPC-UA: 192 (0xC0) = Good
        return quality_code >= 192
