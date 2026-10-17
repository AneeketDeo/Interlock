"""Google Cloud Pub/Sub and BigQuery Streaming Ingestion Pipeline.

Strictly aligned with the ObservationWindow schema in Google BigQuery (dataset: rca_historian, table: ObservationWindow).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from typing import Any
import uuid

from google.cloud import bigquery
from google.cloud import pubsub_v1

from app.core.config import get_settings
from app.core.logging import get_logger
from app.detection.stream_consumer import TelemetryStreamConsumer

logger = get_logger(__name__)


def normalize_timestamp(val: Any) -> str:
    """Normalize any timestamp representation into an ISO 8601 UTC string for BigQuery TIMESTAMP."""
    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=timezone.utc)
        return val.isoformat()
    if isinstance(val, str) and val:
        try:
            dt = datetime.fromisoformat(val)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            return val
    return datetime.now(timezone.utc).isoformat()


def map_to_observation_window(payload: dict[str, Any]) -> dict[str, Any]:
    """Map incoming payload strictly to the ObservationWindow BigQuery schema.

    Schema:
      - obs_id (STRING)
      - sensor_id (STRING)
      - machine_id (STRING)
      - window_start (TIMESTAMP)
      - window_end (TIMESTAMP)
      - mean_value (FLOAT)
      - min_value (FLOAT)
      - max_value (FLOAT)
      - std_dev (FLOAT)
      - sample_count (INTEGER)
      - quality (STRING)
      - is_anomalous (BOOLEAN)
    """
    sensor_id = str(payload.get("sensor_id", ""))
    machine_id = str(payload.get("machine_id", ""))

    obs_id = str(payload.get("obs_id") or f"obs-{sensor_id or 'unknown'}-{uuid.uuid4().hex[:12]}")

    ws_raw = payload.get("window_start") or payload.get("timestamp")
    we_raw = payload.get("window_end") or payload.get("timestamp")
    window_start = normalize_timestamp(ws_raw)
    window_end = normalize_timestamp(we_raw)

    raw_val = payload.get("value", 0.0)
    mean_val = float(payload.get("mean_value", payload.get("mean", raw_val)))
    min_val = float(payload.get("min_value", payload.get("min", mean_val)))
    max_val = float(payload.get("max_value", payload.get("max", mean_val)))
    std_val = float(payload.get("std_dev", payload.get("std", 0.0)))
    sample_count = int(payload.get("sample_count", 1))

    raw_quality = payload.get("quality")
    if isinstance(raw_quality, int):
        quality = "GOOD" if raw_quality >= 192 else ("UNCERTAIN" if raw_quality >= 64 else "BAD")
    elif isinstance(raw_quality, str) and raw_quality:
        quality = raw_quality
    else:
        quality = "GOOD"

    is_anomalous = bool(payload.get("is_anomalous", False))

    return {
        "obs_id": obs_id,
        "sensor_id": sensor_id,
        "machine_id": machine_id,
        "window_start": window_start,
        "window_end": window_end,
        "mean_value": mean_val,
        "min_value": min_val,
        "max_value": max_val,
        "std_dev": std_val,
        "sample_count": sample_count,
        "quality": quality,
        "is_anomalous": is_anomalous,
    }


class PubSubTelemetryPublisher:
    """Publishes telemetry observation windows to Google Cloud Pub/Sub."""

    def __init__(self, project_id: str | None = None, topic_id: str | None = None) -> None:
        settings = get_settings()
        self.project_id = project_id or settings.gcp_project_id
        self.topic_id = topic_id or settings.pubsub_topic_id
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(self.project_id, self.topic_id)

    async def publish_observation_window(
        self,
        obs_id: str,
        sensor_id: str,
        machine_id: str,
        window_start: datetime | str,
        window_end: datetime | str,
        mean_value: float,
        min_value: float,
        max_value: float,
        std_dev: float,
        sample_count: int,
        quality: str = "GOOD",
        is_anomalous: bool = False,
    ) -> str:
        """Publish a strictly-typed ObservationWindow directly to Pub/Sub."""
        payload = {
            "obs_id": obs_id,
            "sensor_id": sensor_id,
            "machine_id": machine_id,
            "window_start": normalize_timestamp(window_start),
            "window_end": normalize_timestamp(window_end),
            "mean_value": float(mean_value),
            "min_value": float(min_value),
            "max_value": float(max_value),
            "std_dev": float(std_dev),
            "sample_count": int(sample_count),
            "quality": str(quality),
            "is_anomalous": bool(is_anomalous),
        }
        data = json.dumps(payload).encode("utf-8")
        loop = asyncio.get_running_loop()

        def _publish() -> str:
            future = self.publisher.publish(
                self.topic_path,
                data=data,
                sensor_id=sensor_id,
                machine_id=machine_id,
            )
            return future.result(timeout=5.0)

        msg_id = await loop.run_in_executor(None, _publish)
        logger.debug("pubsub_window_published", msg_id=msg_id, obs_id=obs_id, sensor_id=sensor_id)
        return msg_id

    async def publish_reading(
        self,
        sensor_id: str,
        machine_id: str,
        line_id: str = "line-03",
        tag: str = "",
        value: float = 0.0,
        quality: int | str = 192,
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Publish a single reading mapped into the standard ObservationWindow format."""
        ts = timestamp or datetime.now(timezone.utc)
        ts_str = normalize_timestamp(ts)
        quality_str = "GOOD" if (quality == 192 or quality == "GOOD") else str(quality)
        obs_id = f"obs-{sensor_id}-{int(ts.timestamp() * 1000)}"

        return await self.publish_observation_window(
            obs_id=obs_id,
            sensor_id=sensor_id,
            machine_id=machine_id,
            window_start=ts_str,
            window_end=ts_str,
            mean_value=float(value),
            min_value=float(value),
            max_value=float(value),
            std_dev=0.0,
            sample_count=1,
            quality=quality_str,
            is_anomalous=False,
        )


class GcpTelemetryHistorianWorker:
    """Subscribes to Pub/Sub, detects anomalies in real-time, and batches into BigQuery ObservationWindow."""

    def __init__(
        self,
        project_id: str | None = None,
        subscription_id: str | None = None,
        dataset_id: str | None = None,
        table_id: str | None = None,
    ) -> None:
        settings = get_settings()
        self.project_id = project_id or settings.gcp_project_id
        self.subscription_id = subscription_id or settings.pubsub_subscription_id
        self.dataset_id = dataset_id or settings.bigquery_dataset or "rca_historian"
        self.table_id = table_id or settings.bigquery_table or "ObservationWindow"

        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = self.subscriber.subscription_path(
            self.project_id, self.subscription_id
        )
        self.bq_client = bigquery.Client(project=self.project_id)
        self.table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"

        self.detector_consumer = TelemetryStreamConsumer()
        self._batch_queue: list[dict[str, Any]] = []
        self._batch_lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    async def _flush_to_bigquery(self) -> None:
        """Batch streams buffered ObservationWindow rows into BigQuery."""
        async with self._batch_lock:
            if not self._batch_queue:
                return
            rows_to_insert = self._batch_queue.copy()
            self._batch_queue.clear()

        errors = await asyncio.to_thread(
            self.bq_client.insert_rows_json,
            self.table_ref,
            rows_to_insert,
        )
        if errors:
            logger.error("bigquery_insert_errors", table=self.table_ref, errors=errors)
        else:
            logger.debug(
                "bigquery_batch_flushed",
                table=self.table_ref,
                count=len(rows_to_insert),
            )

    def _message_callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
        try:
            payload = json.loads(message.data.decode("utf-8"))
            row = map_to_observation_window(payload)

            # Evaluate real-time statistical anomaly detectors
            if self._loop and self._loop.is_running():
                try:
                    dt = datetime.fromisoformat(row["window_start"])
                except Exception:
                    dt = datetime.now(timezone.utc)

                q_code = 192 if row["quality"] == "GOOD" else (0 if row["quality"] == "BAD" else 64)
                asyncio.run_coroutine_threadsafe(
                    self.detector_consumer.process_reading(
                        sensor_id=row["sensor_id"],
                        tag=str(payload.get("tag", payload.get("sensor_type", row["sensor_id"]))),
                        value=row["mean_value"],
                        timestamp=dt,
                        quality=q_code,
                        line_id=str(payload.get("line_id", "line-03")),
                    ),
                    self._loop,
                )

            # Buffer strictly formatted ObservationWindow row for BigQuery micro-batch insert
            self._batch_queue.append(row)
            message.ack()
        except Exception as exc:
            logger.error("pubsub_message_error", error=str(exc))
            message.nack()

    async def run(self) -> None:
        """Run the Pub/Sub subscriber stream and periodic BigQuery batch flusher."""
        self._loop = asyncio.get_running_loop()
        flow_control = pubsub_v1.types.FlowControl(max_messages=200)
        future = self.subscriber.subscribe(
            self.subscription_path,
            callback=self._message_callback,
            flow_control=flow_control,
        )
        logger.info(
            "gcp_telemetry_historian_started",
            subscription=self.subscription_path,
            bigquery_table=self.table_ref,
        )

        try:
            while True:
                await asyncio.sleep(2.0)
                await self._flush_to_bigquery()
        except asyncio.CancelledError:
            future.cancel()
            await self._flush_to_bigquery()
