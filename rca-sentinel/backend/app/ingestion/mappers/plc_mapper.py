"""PLC / OPC-UA telemetry mapper.

Maps raw industrial sensor messages (MQTT/OPC-UA/Kafka payloads) to normalized
telemetry tuples: (timestamp, sensor_id, tag, value, quality).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class PlcMapper:
    """Transforms raw PLC/OPC-UA telemetry packets into normalized readings."""

    @staticmethod
    def map_reading(raw: dict[str, Any]) -> tuple[datetime, str, str, float, int]:
        """Convert a raw sensor packet into a normalized tuple."""
        raw_ts = raw.get("timestamp") or raw.get("time")
        if isinstance(raw_ts, datetime):
            ts = raw_ts
        elif isinstance(raw_ts, str):
            ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
        elif isinstance(raw_ts, (int, float)):
            ts = datetime.fromtimestamp(raw_ts, tz=UTC)
        else:
            ts = datetime.now(UTC)

        sensor_id = str(raw.get("sensor_id") or raw.get("node_id") or "unknown-sensor")
        tag = str(raw.get("tag") or raw.get("metric") or "VALUE")
        value = float(raw.get("value", 0.0))
        quality = int(raw.get("quality", 192))  # 192 = OPC-UA Good

        return (ts, sensor_id, tag, value, quality)

    @staticmethod
    def map_batch(
        raw_list: list[dict[str, Any]],
    ) -> list[tuple[datetime, str, str, float, int]]:
        """Convert a batch of raw packets."""
        return [PlcMapper.map_reading(r) for r in raw_list]
