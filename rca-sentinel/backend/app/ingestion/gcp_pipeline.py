"""Google Cloud Pub/Sub and BigQuery Streaming Ingestion Pipeline."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from typing import Any

from google.cloud import bigquery
from google.cloud import pubsub_v1

from app.core.config import get_settings
from app.core.logging import get_logger
from app.detection.stream_consumer import TelemetryStreamConsumer

logger = get_logger(__name__)


class PubSubTelemetryPublisher:
    """Publishes simulated PLC sensor telemetry to Google Cloud Pub/Sub."""

    def __init__(self, project_id: str | None = None, topic_id: str | None = None) -> None:
        settings = get_settings()
        self.project_id = project_id or settings.gcp_project_id
        self.topic_id = topic_id or settings.pubsub_topic_id
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(self.project_id, self.topic_id)

    async def publish_reading(
        self,
        sensor_id: str,
        machine_id: str,
        line_id: str,
        tag: str,
        value: float,
        quality: int = 192,
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Publish a sensor reading to Pub/Sub asynchronously."""
        ts = timestamp or datetime.now(timezone.utc)
        payload = {
            "timestamp": ts.isoformat(),
            "sensor_id": sensor_id,
            "machine_id": machine_id,
            "line_id": line_id,
            "tag": tag,
            "value": float(value),
            "quality": int(quality),
            "metadata": metadata or {},
        }
        data = json.dumps(payload).encode("utf-8")
        loop = asyncio.get_running_loop()

        def _publish() -> str:
            future = self.publisher.publish(
                self.topic_path,
                data=data,
                sensor_id=sensor_id,
                machine_id=machine_id,
                line_id=line_id,
            )
            return future.result(timeout=5.0)

        msg_id = await loop.run_in_executor(None, _publish)
        logger.debug("pubsub_reading_published", msg_id=msg_id, sensor_id=sensor_id, tag=tag)
        return msg_id


class GcpTelemetryHistorianWorker:
    """Subscribes to Pub/Sub, detects anomalies in real-time, and batches into BigQuery."""

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
        self.dataset_id = dataset_id or settings.bigquery_dataset
        self.table_id = table_id or settings.bigquery_table

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
        """Batch streams buffered telemetry rows into BigQuery."""
        async with self._batch_lock:
            if not self._batch_queue:
                return
            rows_to_insert = self._batch_queue.copy()
            self._batch_queue.clear()

        if self._loop is None:
            return

        errors = await self._loop.run_in_executor(
            None,
            lambda: self.bq_client.insert_rows_json(self.table_ref, rows_to_insert),
        )
        if errors:
            logger.error("bigquery_insert_errors", errors=errors)
        else:
            logger.debug("bigquery_batch_flushed", count=len(rows_to_insert))

    def _message_callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
        try:
            payload = json.loads(message.data.decode("utf-8"))
            raw_ts = payload.get("timestamp")
            ts = (
                datetime.fromisoformat(raw_ts)
                if raw_ts
                else datetime.now(timezone.utc)
            )

            # 1. Process via Statistical Anomaly Detectors
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.detector_consumer.process_reading(
                        sensor_id=payload.get("sensor_id", ""),
                        tag=payload.get("tag", ""),
                        value=float(payload.get("value", 0.0)),
                        timestamp=ts,
                        quality=int(payload.get("quality", 192)),
                        line_id=payload.get("line_id", "line-03"),
                    ),
                    self._loop,
                )

            # 2. Buffer for BigQuery Historian table
            bq_row = {
                "timestamp": ts.isoformat(),
                "sensor_id": payload.get("sensor_id", ""),
                "machine_id": payload.get("machine_id", ""),
                "line_id": payload.get("line_id", ""),
                "tag": payload.get("tag", ""),
                "value": float(payload.get("value", 0.0)),
                "quality": int(payload.get("quality", 192)),
                "metadata": payload.get("metadata", {}),
            }
            self._batch_queue.append(bq_row)
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
