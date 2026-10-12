"""Stream consumer processing live telemetry and driving anomaly detection."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.detection.base import DetectorRegistry
from app.detection.detectors.cusum import CusumDetector
from app.detection.detectors.ewma import EwmaDetector
from app.detection.detectors.zscore import RollingZScoreDetector
from app.detection.filters import ConsecutiveSignalFilter, QualityCheckFilter
from app.detection.incident_creator import IncidentCreator

logger = get_logger(__name__)


class TelemetryStreamConsumer:
    """Consumes telemetry readings, passes them to detectors and filters, and triggers incidents."""

    def __init__(
        self,
        registry: DetectorRegistry | None = None,
        incident_creator: IncidentCreator | None = None,
        consecutive_filter: ConsecutiveSignalFilter | None = None,
    ) -> None:
        self.registry = registry or DetectorRegistry()
        self.incident_creator = incident_creator or IncidentCreator()
        self.filter = consecutive_filter or ConsecutiveSignalFilter(min_consecutive=3)
        self._setup_default_detectors()

    def _setup_default_detectors(self) -> None:
        """Register statistical control detectors for key manufacturing sensors."""
        # Station 3B Vibration
        self.registry.register(
            "sensor-vib-03b",
            CusumDetector(name="VIB_CUSUM", k_slack=0.4, h_threshold=3.5),
        )
        self.registry.register(
            "sensor-vib-03b",
            RollingZScoreDetector(name="VIB_ZScore", window_size=20, z_threshold=2.8),
        )

        # Station 3B Temperature
        self.registry.register(
            "sensor-temp-03b",
            EwmaDetector(name="TEMP_EWMA", lambda_param=0.25, l_sigma=3.0),
        )

        # Line 3 Scrap Counter
        self.registry.register(
            "sensor-scrap-03",
            CusumDetector(name="SCRAP_CUSUM", k_slack=0.5, h_threshold=3.5),
        )
        self.registry.register(
            "sensor-scrap-03",
            EwmaDetector(name="SCRAP_EWMA", lambda_param=0.3, l_sigma=3.0),
        )

    async def process_reading(
        self,
        sensor_id: str,
        tag: str,
        value: float,
        timestamp: datetime,
        quality: int = 192,
        line_id: str = "line-03",
    ) -> dict[str, Any] | None:
        """Process a single sensor reading through quality checks, detectors, and filters."""
        if not QualityCheckFilter.is_valid_quality(quality):
            logger.debug("reading_rejected_bad_quality", sensor_id=sensor_id, quality=quality)
            return None

        # 1. Evaluate detectors
        raw_signals = self.registry.process_reading(
            sensor_id=sensor_id,
            metric=tag,
            value=value,
            timestamp=timestamp,
        )

        if not raw_signals:
            return None

        # 2. Pass highest-scoring signal through consecutive filter
        best_signal = max(raw_signals, key=lambda s: s.score)
        confirmed_signal = self.filter.filter(best_signal)

        if not confirmed_signal:
            return None

        # 3. Create incident
        logger.info(
            "anomaly_confirmed_creating_incident",
            sensor_id=sensor_id,
            tag=tag,
            value=value,
            score=confirmed_signal.score,
        )
        return await self.incident_creator.create_from_anomaly(
            signal=confirmed_signal,
            line_id=line_id,
        )

    async def process_batch(
        self,
        readings: list[tuple[datetime, str, str, float, int]],
        line_id: str = "line-03",
    ) -> list[dict[str, Any]]:
        """Process a batch of readings in chronological order."""
        created_incidents: list[dict[str, Any]] = []
        for ts, sensor_id, tag, value, quality in readings:
            res = await self.process_reading(
                sensor_id=sensor_id,
                tag=tag,
                value=value,
                timestamp=ts,
                quality=quality,
                line_id=line_id,
            )
            if res:
                created_incidents.append(res)
        return created_incidents
