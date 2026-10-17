"""Unit tests for GCP Pub/Sub & BigQuery ObservationWindow streaming pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.ingestion.gcp_pipeline import (
    GcpTelemetryHistorianWorker,
    PubSubTelemetryPublisher,
    map_to_observation_window,
    normalize_timestamp,
)

EXPECTED_KEYS = {
    "obs_id",
    "sensor_id",
    "machine_id",
    "window_start",
    "window_end",
    "mean_value",
    "min_value",
    "max_value",
    "std_dev",
    "sample_count",
    "quality",
    "is_anomalous",
}


def test_map_to_observation_window_strict_keys():
    """Verify mapped payload contains strictly the 12 ObservationWindow keys and no extras."""
    incoming = {
        "obs_id": "obs-001",
        "sensor_id": "sensor-spindle-vibe",
        "machine_id": "station-03b",
        "window_start": "2026-10-17T12:00:00Z",
        "window_end": "2026-10-17T12:01:00Z",
        "mean_value": 4.52,
        "min_value": 3.8,
        "max_value": 5.2,
        "std_dev": 0.41,
        "sample_count": 60,
        "quality": "GOOD",
        "is_anomalous": True,
        # Extraneous fields that must be dropped
        "temperature": 85.2,
        "vibration": 4.5,
        "tag": "vibration_spindle_x",
        "line_id": "line-03",
        "metadata": {"foo": "bar"},
    }

    result = map_to_observation_window(incoming)

    assert set(result.keys()) == EXPECTED_KEYS
    assert result["obs_id"] == "obs-001"
    assert result["sensor_id"] == "sensor-spindle-vibe"
    assert result["machine_id"] == "station-03b"
    assert isinstance(result["window_start"], str)
    assert isinstance(result["window_end"], str)
    assert isinstance(result["mean_value"], float)
    assert result["mean_value"] == 4.52
    assert isinstance(result["min_value"], float)
    assert isinstance(result["max_value"], float)
    assert isinstance(result["std_dev"], float)
    assert isinstance(result["sample_count"], int)
    assert result["sample_count"] == 60
    assert isinstance(result["quality"], str)
    assert result["quality"] == "GOOD"
    assert isinstance(result["is_anomalous"], bool)
    assert result["is_anomalous"] is True


def test_map_to_observation_window_defaults():
    """Verify fallback and default generation adheres strictly to schema."""
    incoming = {
        "sensor_id": "sensor-clamp-p",
        "machine_id": "station-03b",
        "value": 12.5,
    }

    result = map_to_observation_window(incoming)

    assert set(result.keys()) == EXPECTED_KEYS
    assert result["sensor_id"] == "sensor-clamp-p"
    assert result["machine_id"] == "station-03b"
    assert result["mean_value"] == 12.5
    assert result["min_value"] == 12.5
    assert result["max_value"] == 12.5
    assert result["std_dev"] == 0.0
    assert result["sample_count"] == 1
    assert result["quality"] == "GOOD"
    assert result["is_anomalous"] is False
    assert result["obs_id"].startswith("obs-sensor-clamp-p-")


@pytest.mark.asyncio
async def test_worker_buffering_and_bigquery_flush():
    """Verify GcpTelemetryHistorianWorker buffers and flushes exact schema into BigQuery."""
    with patch("app.ingestion.gcp_pipeline.pubsub_v1.SubscriberClient"), \
         patch("app.ingestion.gcp_pipeline.bigquery.Client") as mock_bq_cls:

        mock_bq_client = MagicMock()
        mock_bq_client.insert_rows_json.return_value = []
        mock_bq_cls.return_value = mock_bq_client

        worker = GcpTelemetryHistorianWorker(
            project_id="test-proj",
            subscription_id="test-sub",
            dataset_id="rca_historian",
            table_id="ObservationWindow",
        )

        assert worker.table_ref == "test-proj.rca_historian.ObservationWindow"

        # Simulate pubsub callback
        mock_msg = MagicMock()
        mock_msg.data = b'{"sensor_id": "s1", "machine_id": "m1", "value": 10.0, "quality": "GOOD"}'
        worker._message_callback(mock_msg)

        assert len(worker._batch_queue) == 1
        buffered_row = worker._batch_queue[0]
        assert set(buffered_row.keys()) == EXPECTED_KEYS
        mock_msg.ack.assert_called_once()

        # Flush
        await worker._flush_to_bigquery()

        mock_bq_client.insert_rows_json.assert_called_once_with(
            "test-proj.rca_historian.ObservationWindow",
            [buffered_row],
        )
        assert len(worker._batch_queue) == 0
