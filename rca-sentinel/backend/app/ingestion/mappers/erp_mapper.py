"""ERP and inventory lot mapper.

Maps SAP/NetSuite ERP purchase orders, receiving inspection records,
and inventory genealogy into normalized Supplier and MaterialLot dicts.
"""

from __future__ import annotations

from typing import Any

from app.ingestion.entity_resolution import EntityResolver


class ErpMapper:
    """Transforms raw ERP payloads into MaterialLot and Supplier entities."""

    def __init__(self, resolver: EntityResolver | None = None) -> None:
        self.resolver = resolver or EntityResolver()

    def map_lot(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Convert raw ERP lot into domain MaterialLot dict."""
        raw_lot_num = str(raw.get("lot_number") or raw.get("batch_id") or raw.get("id", ""))
        lot_id = self.resolver.resolve_lot_id(raw_lot_num)

        raw_supplier = str(raw.get("supplier_id") or raw.get("vendor_id") or "")
        supplier_id = self.resolver.resolve_supplier_id(raw_supplier)

        props = raw.get("properties") or raw.get("lab_results") or {}

        return {
            "id": lot_id,
            "lot_number": raw_lot_num,
            "supplier_id": supplier_id,
            "material_type": raw.get("material_type") or raw.get("item_code", "raw_material"),
            "quantity": float(raw.get("quantity", 0.0)),
            "unit": raw.get("unit", "kg"),
            "status": raw.get("status", "released"),
            "parent_lot_ids": [
                self.resolver.resolve_lot_id(str(p))
                for p in raw.get("parent_lot_ids", [])
            ],
            "assigned_to_machine": (
                self.resolver.resolve_machine_id(str(raw["assigned_to_machine"]))
                if raw.get("assigned_to_machine")
                else None
            ),
            "properties": props,
        }

    def map_supplier(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Convert raw ERP vendor record into domain Supplier dict."""
        raw_name = str(raw.get("name") or raw.get("vendor_name", ""))
        sup_id = self.resolver.resolve_supplier_id(str(raw.get("id") or raw_name))

        return {
            "id": sup_id,
            "name": raw_name or sup_id,
            "code": raw.get("code") or raw.get("vendor_code", ""),
            "tier": int(raw.get("tier", 1)),
            "country": raw.get("country", "Unknown"),
            "quality_rating": float(raw.get("quality_rating", 100.0)),
            "audit_status": raw.get("audit_status", "certified"),
        }
