"""Ingestion monitor and control API router."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.core.security import get_current_user, require_role
from app.domain.enums import ApproverRole

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

# In-memory monitoring cache for demo
_last_ingestion_summary: dict[str, Any] = {
    "status": "ready",
    "last_run": None,
    "counts": {
        "plants": 0,
        "lines": 0,
        "machines": 0,
        "sensors": 0,
        "suppliers": 0,
        "material_lots": 0,
        "failure_modes": 0,
        "maintenance_events": 0,
        "operator_logs": 0,
        "telemetry_readings": 0,
        "quarantined_records": 0,
    },
    "quarantined_records": [],
}


@router.get("/status")
async def get_ingestion_status(
    _user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Get current ingestion pipeline metrics and health."""
    return _last_ingestion_summary


@router.get("/quarantine")
async def get_quarantined_records(
    _user: Any = Depends(require_role(ApproverRole.RELIABILITY_ENGINEER, ApproverRole.QUALITY_ENGINEER, ApproverRole.ADMIN)),
) -> list[dict[str, Any]]:
    """Retrieve all records rejected by SHACL validation."""
    return _last_ingestion_summary.get("quarantined_records", [])  # type: ignore[no-any-return]


@router.post("/trigger")
async def trigger_ingestion(
    _user: Any = Depends(require_role(ApproverRole.ADMIN, ApproverRole.RELIABILITY_ENGINEER)),
) -> dict[str, Any]:
    """Trigger synthetic generation and ingestion pipeline."""
    from app.core.config import get_settings
    from app.ingestion.pipeline import IngestionPipeline
    from app.simulator.generator import SyntheticDataGenerator

    settings = get_settings()
    generator = SyntheticDataGenerator(settings)
    data = generator.generate()

    pipeline = IngestionPipeline()
    result = await pipeline.ingest_synthetic_data(data)

    global _last_ingestion_summary
    _last_ingestion_summary = {
        "status": "completed",
        "last_run": data["metadata"]["generated_at"],
        "counts": result["counts"],
        "quarantined_records": result["quarantined_records"],
    }

    return result
