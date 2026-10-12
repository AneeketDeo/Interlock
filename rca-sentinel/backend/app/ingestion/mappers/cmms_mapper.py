"""CMMS maintenance work order mapper.

Maps Maximo / SAP PM / Fiix CMMS maintenance records and technician logs
into normalized MaintenanceEvent domain dicts.
"""

from __future__ import annotations

from typing import Any

from app.ingestion.entity_resolution import EntityResolver


class CmmsMapper:
    """Transforms raw CMMS work orders into MaintenanceEvent entities."""

    def __init__(self, resolver: EntityResolver | None = None) -> None:
        self.resolver = resolver or EntityResolver()

    def map_maintenance_event(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Convert a raw CMMS work order into a MaintenanceEvent dict."""
        raw_wo = str(raw.get("id") or raw.get("work_order_id", ""))
        wo_id = self.resolver.resolve_work_order_id(raw_wo)

        raw_machine = str(raw.get("machine_id") or raw.get("asset_id", ""))
        machine_id = self.resolver.resolve_machine_id(raw_machine)

        return {
            "id": wo_id,
            "machine_id": machine_id,
            "event_type": raw.get("event_type") or raw.get("type", "preventive"),
            "title": raw.get("title") or raw.get("summary", "Maintenance Work Order"),
            "technician_id": raw.get("technician_id", "tech-unknown"),
            "technician_name": raw.get("technician_name", "Technician"),
            "crew_name": raw.get("crew_name", "Maintenance Crew"),
            "shift": int(raw.get("shift", 1)),
            "timestamp": raw.get("timestamp") or raw.get("completed_at", ""),
            "duration_minutes": int(raw.get("duration_minutes", 60)),
            "calibration_offset_mm": float(raw.get("calibration_offset_mm", 0.0)),
            "tolerance_limit_mm": float(raw.get("tolerance_limit_mm", 0.010)),
            "notes": str(raw.get("notes") or raw.get("description", "")),
            "status": raw.get("status", "completed"),
        }
