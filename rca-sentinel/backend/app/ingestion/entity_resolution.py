"""Entity resolution service for cross-silo manufacturing data.

Reconciles disparate external identifiers:
- ERP lot numbers ("LOT-40921") -> canonical lot IDs ("lot-40921")
- MES machine codes ("STN-03B", "DMG-5000") -> canonical machine IDs ("station-03b")
- CMMS work order numbers ("WO#8821") -> canonical event IDs ("wo-8821")
- Supplier vendor codes ("AL-TECH-01") -> canonical supplier IDs ("sup-tier3-001")
"""

from __future__ import annotations

import re
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class EntityResolver:
    """Normalizes and reconciles identifiers across ERP, MES, CMMS, and supplier silos."""

    def __init__(self) -> None:
        # Alias lookup caches
        self._machine_aliases: dict[str, str] = {
            "stn-03b": "station-03b",
            "station-3b": "station-03b",
            "station-b": "station-03b",
            "dmg-nhx-5000": "station-03b",
            "cnc-milling-station-b": "station-03b",
        }
        self._supplier_aliases: dict[str, str] = {
            "alloytech": "sup-tier3-001",
            "alloytech-global": "sup-tier3-001",
            "al-tech-01": "sup-tier3-001",
            "precision-stampings": "sup-tier2-001",
            "precision-stampings-co": "sup-tier2-001",
            "apex-subassemblies": "sup-tier1-001",
        }

    def normalize_id(self, raw_id: str) -> str:
        """Strip whitespace, lowercase, and replace punctuation with dashes."""
        cleaned = raw_id.strip().lower()
        cleaned = re.sub(r"[#/\s_]+", "-", cleaned)
        return cleaned.strip("-")

    def resolve_machine_id(self, raw_id: str) -> str:
        """Resolve a machine identifier to canonical ID."""
        normalized = self.normalize_id(raw_id)
        return self._machine_aliases.get(normalized, normalized)

    def resolve_supplier_id(self, raw_id: str) -> str:
        """Resolve a supplier identifier or vendor name to canonical ID."""
        normalized = self.normalize_id(raw_id)
        return self._supplier_aliases.get(normalized, normalized)

    def resolve_lot_id(self, raw_lot_number: str) -> str:
        """Resolve a lot number to canonical lot ID."""
        cleaned = self.normalize_id(raw_lot_number)
        if not cleaned.startswith("lot-"):
            cleaned = f"lot-{cleaned}"
        return cleaned

    def resolve_work_order_id(self, raw_wo: str) -> str:
        """Resolve a work order code to canonical event ID."""
        cleaned = self.normalize_id(raw_wo)
        if not cleaned.startswith("wo-"):
            cleaned = f"wo-{cleaned}"
        return cleaned

    def reconcile_lot_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Normalize lot record fields in place or return copy."""
        resolved = dict(record)
        if "lot_number" in resolved:
            resolved["id"] = self.resolve_lot_id(resolved["lot_number"])
        if "supplier_id" in resolved:
            resolved["supplier_id"] = self.resolve_supplier_id(resolved["supplier_id"])
        if resolved.get("assigned_to_machine"):
            resolved["assigned_to_machine"] = self.resolve_machine_id(
                resolved["assigned_to_machine"]
            )
        return resolved
