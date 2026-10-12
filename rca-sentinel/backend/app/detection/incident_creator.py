"""Incident and 8D DecisionObject creator upon confirmed anomaly signals."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.logging import get_logger
from app.core.redis import get_redis_client
from app.detection.base import AnomalySignal
from app.detection.severity import SeverityCalculator
from app.domain.enums import DecisionStage, IncidentStatus
from app.graph.repositories.incident import IncidentRepository

logger = get_logger(__name__)


class IncidentCreator:
    """Transforms confirmed anomaly signals into Incident and 8D DecisionObject(D2) entities."""

    def __init__(self, incident_repo: IncidentRepository | None = None) -> None:
        self.incident_repo = incident_repo or IncidentRepository()

    async def create_from_anomaly(
        self,
        signal: AnomalySignal,
        line_id: str = "line-03",
        plant_id: str = "plant-stuttgart-01",
    ) -> dict[str, Any]:
        """Create an Incident and initial 8D DecisionObject(D2) for an anomaly signal."""
        # Calculate severity and estimated financial impact
        severity = SeverityCalculator.compute_severity(
            metric=signal.metric,
            value=signal.value,
            baseline=signal.baseline,
            details=signal.details,
        )
        blast_units = 420 if severity.value == "critical" else 100
        financial_est = SeverityCalculator.estimate_financial_impact(
            severity=severity,
            affected_units=blast_units,
        )

        ts_str = signal.timestamp.strftime("%Y%m%d-%H%M")
        short_id = uuid.uuid4().hex[:6]
        incident_id = f"INC-{ts_str}-{short_id}"

        title = (
            f"Sudden {signal.metric} Anomaly on {line_id}: "
            f"{signal.value} vs baseline {signal.baseline}"
        )

        incident_payload = {
            "id": incident_id,
            "title": title,
            "status": IncidentStatus.DETECTED.value,
            "severity": severity.value,
            "line_id": line_id,
            "detected_at": signal.timestamp.isoformat(),
            "anomaly_score": signal.score,
            "blast_radius_units": blast_units,
            "financial_impact_usd": financial_est,
        }

        # 1. Create Incident in Neo4j
        created_incident = await self.incident_repo.create_incident(incident_payload)
        logger.info(
            "incident_created",
            incident_id=incident_id,
            severity=severity.value,
            metric=signal.metric,
        )

        # 2. Create 8D DecisionObject (Stage D2: Problem Description)
        decision_id = f"DEC-{incident_id}-D2"
        decision_payload = {
            "id": decision_id,
            "stage": DecisionStage.DETECT.value,
            "agent_name": "DetectAgent",
            "confidence": signal.score,
            "status": "confirmed",
            "content": {
                "metric": signal.metric,
                "sensor_id": signal.sensor_id,
                "detected_value": signal.value,
                "baseline_value": signal.baseline,
                "threshold": signal.threshold,
                "deviation_pct": round(((signal.value - signal.baseline) / max(0.1, signal.baseline)) * 100, 1),
                "detector_name": signal.detector_name,
                "first_detected_at": signal.details.get("first_detected_at", signal.timestamp.isoformat()),
                "severity": severity.value,
            },
            "reasoning": (
                f"Statistical control limit violation detected by {signal.detector_name}. "
                f"Metric {signal.metric} surged to {signal.value} (baseline {signal.baseline}). "
                f"Confirmed across {signal.details.get('consecutive_count', 3)} consecutive time intervals."
            ),
            "evidence_node_ids": [signal.sensor_id],
        }

        created_decision = await self.incident_repo.add_decision_object(
            incident_id=incident_id, decision=decision_payload
        )

        # 3. Publish to Redis Stream and Pub/Sub
        try:
            redis = get_redis_client()
            event_payload = {
                "event": "incident_created",
                "incident_id": incident_id,
                "severity": severity.value,
                "metric": signal.metric,
                "detected_at": signal.timestamp.isoformat(),
            }
            await redis.publish("incidents:events", event_payload)
            await redis.stream_add("incidents", {k: str(v) for k, v in event_payload.items()})
        except Exception:
            logger.debug("redis_incident_broadcast_skipped")

        return {
            "incident": created_incident,
            "decision": created_decision,
        }
