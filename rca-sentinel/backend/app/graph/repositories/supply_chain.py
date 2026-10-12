"""Supply chain repository: Suppliers, MaterialLots, and multi-tier provenance."""

from __future__ import annotations

import json
from typing import Any

from app.graph.repositories.base import BaseGraphRepository


class SupplyChainRepository(BaseGraphRepository):
    """Manages Supplier, MaterialLot, BOM relationships, and lineage traversal."""

    async def upsert_suppliers(self, suppliers: list[dict[str, Any]]) -> int:
        query = """
        UNWIND $batch AS row
        MERGE (s:Supplier {id: row.id})
        SET s.name = row.name,
            s.code = row.code,
            s.tier = row.tier,
            s.country = row.country,
            s.quality_rating = row.quality_rating,
            s.audit_status = row.audit_status,
            s.updated_at = datetime()
        RETURN count(s)
        """
        return await self.batch_unwind_write(query, suppliers)

    async def upsert_material_lots(self, lots: list[dict[str, Any]]) -> int:
        # 1. Upsert lots with supplier link
        lot_rows: list[dict[str, Any]] = []
        parent_rows: list[dict[str, Any]] = []
        processed_rows: list[dict[str, Any]] = []

        for lot in lots:
            lot_rows.append({
                "id": lot["id"],
                "lot_number": lot["lot_number"],
                "supplier_id": lot["supplier_id"],
                "material_type": lot.get("material_type", ""),
                "quantity": lot.get("quantity", 0.0),
                "unit": lot.get("unit", ""),
                "status": lot.get("status", "released"),
                "properties_json": json.dumps(lot.get("properties", {})),
            })

            for parent_id in lot.get("parent_lot_ids", []):
                parent_rows.append({"child_id": lot["id"], "parent_id": parent_id})

            if lot.get("assigned_to_machine"):
                processed_rows.append({
                    "lot_id": lot["id"],
                    "machine_id": lot["assigned_to_machine"],
                })

        query_lots = """
        UNWIND $batch AS row
        MERGE (ml:MaterialLot {id: row.id})
        SET ml.lot_number = row.lot_number,
            ml.material_type = row.material_type,
            ml.quantity = row.quantity,
            ml.unit = row.unit,
            ml.status = row.status,
            ml.properties_json = row.properties_json,
            ml.updated_at = datetime()
        WITH ml, row
        MATCH (s:Supplier {id: row.supplier_id})
        MERGE (s)-[:SUPPLIED_LOT]->(ml)
        RETURN count(ml)
        """
        count = await self.batch_unwind_write(query_lots, lot_rows)

        # 2. Consumption / Provenance edges
        if parent_rows:
            query_parents = """
            UNWIND $batch AS row
            MATCH (child:MaterialLot {id: row.child_id})
            MATCH (parent:MaterialLot {id: row.parent_id})
            MERGE (child)-[:CONSUMED_LOT]->(parent)
            RETURN count(*)
            """
            await self.batch_unwind_write(query_parents, parent_rows)

        # 3. Machine processing edges
        if processed_rows:
            query_processed = """
            UNWIND $batch AS row
            MATCH (ml:MaterialLot {id: row.lot_id})
            MATCH (m:Machine {id: row.machine_id})
            MERGE (m)-[:PROCESSED_LOT]->(ml)
            RETURN count(*)
            """
            await self.batch_unwind_write(query_processed, processed_rows)

        return count

    async def get_lot_lineage(self, lot_id: str) -> dict[str, Any]:
        """Multi-hop backward traversal to trace all upstream lots and suppliers."""
        query = """
        MATCH (start:MaterialLot {id: $lot_id})
        OPTIONAL MATCH (sup:Supplier)-[:SUPPLIED_LOT]->(start)
        OPTIONAL MATCH path = (start)-[:CONSUMED_LOT*1..6]->(upstream:MaterialLot)
        OPTIONAL MATCH (upstream_sup:Supplier)-[:SUPPLIED_LOT]->(upstream)
        WITH start, sup,
             collect(DISTINCT upstream) AS upstream_lots,
             collect(DISTINCT upstream_sup) AS upstream_suppliers
        RETURN {
            target_lot: start {.*, supplier: sup {.*}},
            upstream_lots: [lot IN upstream_lots | lot {.*}],
            upstream_suppliers: [s IN upstream_suppliers | s {.*}]
        } AS lineage
        """
        records = await self.execute_read(query, {"lot_id": lot_id})
        return records[0]["lineage"] if records else {}

    async def get_lot(self, lot_id: str) -> dict[str, Any] | None:
        query = """
        MATCH (ml:MaterialLot {id: $lot_id})
        OPTIONAL MATCH (s:Supplier)-[:SUPPLIED_LOT]->(ml)
        OPTIONAL MATCH (m:Machine)-[:PROCESSED_LOT]->(ml)
        RETURN ml {
            .*,
            supplier: s {.*},
            processed_by_machine: m {.*}
        } AS lot
        """
        records = await self.execute_read(query, {"lot_id": lot_id})
        return records[0]["lot"] if records and records[0]["lot"] else None
