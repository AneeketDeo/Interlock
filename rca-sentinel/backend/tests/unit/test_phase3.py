"""Tests for Phase 3: Statistical Detectors, Filters, Severity, and Incident Creation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from app.detection.base import AnomalySignal
from app.detection.detectors.cusum import CusumDetector
from app.detection.detectors.ewma import EwmaDetector
from app.detection.detectors.zscore import RollingZScoreDetector
from app.detection.filters import ConsecutiveSignalFilter, QualityCheckFilter
from app.detection.incident_creator import IncidentCreator
from app.detection.proactive.drift_detector import ProactiveDriftDetector
from app.detection.severity import SeverityCalculator
from app.detection.stream_consumer import TelemetryStreamConsumer
from app.domain.enums import Severity
from app.simulator.generator import SyntheticDataGenerator
from app.simulator.scenarios import GoldenScenarioConfig

# ── Detector Tests ──────────────────────────────────────────────────


class TestDetectors:
    def test_ewma_detects_mean_shift(self) -> None:
        det = EwmaDetector(lambda_param=0.2, l_sigma=3.0, warmup_samples=15)
        now = datetime(2026, 10, 10, 12, 0, 0, tzinfo=UTC)

        # Baseline noise around 10.0
        for i in range(25):
            sig = det.update(10.0 + (i % 3) * 0.1, timestamp=now + timedelta(minutes=i))
            assert sig is None

        # Abrupt shift to 18.0
        anomaly_detected = False
        for i in range(25, 35):
            sig = det.update(18.0, timestamp=now + timedelta(minutes=i))
            if sig:
                anomaly_detected = True
                assert sig.value == 18.0
                assert sig.baseline < 12.0
                break

        assert anomaly_detected

    def test_cusum_detects_step_change(self) -> None:
        det = CusumDetector(k_slack=0.5, h_threshold=4.0, warmup_samples=15)
        now = datetime(2026, 10, 10, 12, 0, 0, tzinfo=UTC)

        # Baseline noise
        for i in range(20):
            sig = det.update(1.0 + (i % 2) * 0.05, timestamp=now + timedelta(minutes=i))
            assert sig is None

        # Persistent step change
        signals = []
        for i in range(20, 30):
            sig = det.update(3.5, timestamp=now + timedelta(minutes=i))
            if sig:
                signals.append(sig)

        assert len(signals) > 0
        assert signals[0].value == 3.5

    def test_rolling_zscore_detects_outlier(self) -> None:
        det = RollingZScoreDetector(window_size=20, z_threshold=3.0)
        now = datetime(2026, 10, 10, 12, 0, 0, tzinfo=UTC)

        # Stable values
        for i in range(25):
            sig = det.update(5.0 + (i % 3) * 0.05, timestamp=now + timedelta(minutes=i))
            assert sig is None

        # Massive 8x outlier
        sig = det.update(15.0, timestamp=now + timedelta(minutes=26))
        assert sig is not None
        assert sig.value == 15.0
        assert sig.score > 0.5


# ── Filter Tests ────────────────────────────────────────────────────


class TestFilters:
    def test_quality_check_filter(self) -> None:
        assert QualityCheckFilter.is_valid_quality(192) is True  # OPC-UA Good
        assert QualityCheckFilter.is_valid_quality(200) is True
        assert QualityCheckFilter.is_valid_quality(64) is False  # Uncertain
        assert QualityCheckFilter.is_valid_quality(0) is False  # Bad

    def test_consecutive_signal_filter(self) -> None:
        filt = ConsecutiveSignalFilter(min_consecutive=3, max_gap_seconds=300.0)
        now = datetime(2026, 10, 10, 12, 0, 0, tzinfo=UTC)

        sig1 = AnomalySignal("s1", "SCRAP", now, 10.0, 1.2, 5.0, 0.8, "EWMA")
        sig2 = AnomalySignal("s1", "SCRAP", now + timedelta(seconds=60), 11.0, 1.2, 5.0, 0.85, "EWMA")
        sig3 = AnomalySignal("s1", "SCRAP", now + timedelta(seconds=120), 12.0, 1.2, 5.0, 0.9, "EWMA")

        assert filt.filter(sig1) is None
        assert filt.filter(sig2) is None
        confirmed = filt.filter(sig3)
        assert confirmed is not None
        assert confirmed.sensor_id == "s1"
        assert confirmed.details["consecutive_count"] == 3


# ── Severity Tests ──────────────────────────────────────────────────


class TestSeverityCalculator:
    def test_scrap_spike_severity(self) -> None:
        sev_critical = SeverityCalculator.compute_severity("SCRAP_RATE_PCT", 13.4, 1.2)
        assert sev_critical == Severity.CRITICAL

        sev_high = SeverityCalculator.compute_severity("SCRAP_RATE_PCT", 7.0, 1.2)
        assert sev_high == Severity.HIGH

        sev_low = SeverityCalculator.compute_severity("SCRAP_RATE_PCT", 1.8, 1.2)
        assert sev_low == Severity.LOW

    def test_vibration_spike_severity(self) -> None:
        sev = SeverityCalculator.compute_severity("SPINDLE_VIB_RMS", 4.15, 1.05)
        assert sev == Severity.CRITICAL

    def test_financial_impact_estimation(self) -> None:
        impact = SeverityCalculator.estimate_financial_impact(
            Severity.CRITICAL, affected_units=420, estimated_downtime_hours=2.0
        )
        assert impact > 150000.0


# ── Incident Creation & Stream Consumer Tests ───────────────────────


class TestIncidentCreator:
    @pytest.mark.asyncio
    async def test_create_incident_and_decision(self, monkeypatch: pytest.MonkeyPatch) -> None:
        creator = IncidentCreator()
        mock_create_inc = AsyncMock(return_value={"id": "INC-TEST-001", "status": "detected"})
        mock_add_dec = AsyncMock(return_value={"id": "DEC-TEST-001", "stage": "D2"})
        monkeypatch.setattr(creator.incident_repo, "create_incident", mock_create_inc)
        monkeypatch.setattr(creator.incident_repo, "add_decision_object", mock_add_dec)

        now = datetime(2026, 10, 10, 12, 0, 0, tzinfo=UTC)
        signal = AnomalySignal("sensor-scrap-03", "SCRAP_RATE_PCT", now, 13.4, 1.2, 5.0, 0.95, "CUSUM_CONFIRMED")

        result = await creator.create_from_anomaly(signal, line_id="line-03")
        assert "incident" in result
        assert "decision" in result
        mock_create_inc.assert_called_once()
        mock_add_dec.assert_called_once()


class TestTelemetryStreamConsumerGoldenScenario:
    @pytest.mark.asyncio
    async def test_golden_scenario_detection_flow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Simulate golden scenario: baseline produces 0 incidents, anomaly produces incident."""
        consumer = TelemetryStreamConsumer()
        mock_inc_creator = AsyncMock(return_value={"incident": {"id": "INC-GOLDEN-01"}, "decision": {"id": "DEC-01"}})
        monkeypatch.setattr(consumer.incident_creator, "create_from_anomaly", mock_inc_creator)

        gen = SyntheticDataGenerator(seed=42)
        data = gen.generate()
        cfg = GoldenScenarioConfig()

        # Extract scrap sensor readings (ordered chronologically)
        scrap_readings = [
            r for r in data["telemetry"] if r[1] == cfg.SENSOR_SCRAP_ID
        ]
        assert len(scrap_readings) > 100

        # Feed the readings into consumer
        created = await consumer.process_batch(scrap_readings, line_id=cfg.LINE_ID)

        # Anomaly should be triggered and incident created!
        assert len(created) > 0
        mock_inc_creator.assert_called()


class TestProactiveDriftDetector:
    def test_drift_when_disabled(self) -> None:
        detector = ProactiveDriftDetector()
        # Default settings has proactive_detection_enabled = False
        res = detector.predict_drift("s1", [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8])
        assert res is None
