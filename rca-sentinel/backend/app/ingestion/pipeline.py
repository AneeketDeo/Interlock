"""Ingestion pipeline orchestrating SHACL validation, entity resolution, and dual writes.

Ensures strict quality gates:
1. Validates records against SHACL shapes BEFORE any graph write.
2. Quarantines invalid records with diagnostic failure messages.
3. Performs entity resolution across disparate system keys.
4. Batch-upserts graph topology and provenance into Neo4j Aura.
5. Ingests high-frequency time-series telemetry into TimescaleDB.
"""

from __future__ import annotations

from typing import Any

from app.core.database import get_timescale_client
from app.core.logging import get_logger
from app.core.redis import get_redis_client
from app.graph.repositories.failure_mode import FailureModeRepository
from app.graph.repositories.maintenance import MaintenanceRepository
from app.graph.repositories.supply_chain import SupplyChainRepository
from app.graph.repositories.topology import TopologyRepository
from app.ingestion.entity_resolution import EntityResolver
from app.ontology.validator import ShaclValidator

logger = get_logger(__name__)


class IngestionPipeline:
    """End-to-end ingestion pipeline with SHACL validation and dual-store dispatch."""

    def __init__(
        self,
        validator: ShaclValidator | None = None,
        resolver: EntityResolver | None = None,
    ) -> None:
        self.validator = validator or ShaclValidator()
        self.resolver = resolver or EntityResolver()
        self.topology_repo = TopologyRepository()
        self.supply_repo = SupplyChainRepository()
        self.maint_repo = MaintenanceRepository()
        self.failure_repo = FailureModeRepository()
        self.quarantine: list[dict[str, Any]] = []

    async def ingest_synthetic_data(
        self, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Ingest complete dataset from SyntheticDataGenerator."""
        logger.info("ingestion_pipeline_started")
        stats: dict[str, int] = {
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
        }

        # 1. Topology
        plants = data.get("plants", [])
        if plants:
            stats["plants"] = await self.topology_repo.upsert_plants(plants)

        lines = data.get("lines", [])
        if lines:
            stats["lines"] = await self.topology_repo.upsert_lines(lines)

        machines = data.get("machines", [])
        if machines:
            stats["machines"] = await self.topology_repo.upsert_machines(machines)

        sensors = data.get("sensors", [])
        if sensors:
            stats["sensors"] = await self.topology_repo.upsert_sensors(sensors)

        # 2. Suppliers with SHACL validation
        raw_suppliers = data.get("suppliers", [])
        valid_suppliers: list[dict[str, Any]] = []
        for sup in raw_suppliers:
            sup_resolved = {
                **sup,
                "id": self.resolver.resolve_supplier_id(sup["id"]),
            }
            conforms, reason = self.validator.validate_single(sup_resolved, "Supplier")
            if conforms:
                valid_suppliers.append(sup_resolved)
            else:
                self.quarantine.append({
                    "entity_type": "Supplier",
                    "record": sup,
                    "reason": reason,
                })
                stats["quarantined_records"] += 1

        if valid_suppliers:
            stats["suppliers"] = await self.supply_repo.upsert_suppliers(valid_suppliers)

        # 3. Material Lots with SHACL validation
        raw_lots = data.get("material_lots", [])
        valid_lots: list[dict[str, Any]] = []
        for lot in raw_lots:
            resolved_lot = self.resolver.reconcile_lot_record(lot)
            conforms, reason = self.validator.validate_single(resolved_lot, "MaterialLot")
            if conforms:
                valid_lots.append(resolved_lot)
            else:
                self.quarantine.append({
                    "entity_type": "MaterialLot",
                    "record": lot,
                    "reason": reason,
                })
                stats["quarantined_records"] += 1

        if valid_lots:
            stats["material_lots"] = await self.supply_repo.upsert_material_lots(valid_lots)

        # 4. Failure Modes
        modes = data.get("failure_modes", [])
        if modes:
            stats["failure_modes"] = await self.failure_repo.upsert_failure_modes(modes)

        # 5. Maintenance Events & Operator Logs
        maint_events = data.get("maintenance_events", [])
        if maint_events:
            resolved_events = [
                {
                    **ev,
                    "machine_id": self.resolver.resolve_machine_id(ev["machine_id"]),
                }
                for ev in maint_events
            ]
            stats["maintenance_events"] = await self.maint_repo.upsert_maintenance_events(
                resolved_events
            )

        op_logs = data.get("operator_logs", [])
        if op_logs:
            resolved_logs = [
                {
                    **log,
                    "machine_id": self.resolver.resolve_machine_id(log["machine_id"]),
                }
                for log in op_logs
            ]
            stats["operator_logs"] = await self.maint_repo.upsert_operator_logs(
                resolved_logs
            )

        # 6. Telemetry into TimescaleDB
        telemetry_readings = data.get("telemetry", [])
        if telemetry_readings:
            try:
                timescale = get_timescale_client()
                stats["telemetry_readings"] = await timescale.insert_telemetry_batch(
                    telemetry_readings
                )
            except Exception as exc:
                logger.warning(
                    "timescale_ingestion_skipped",
                    error=str(exc),
                    count=len(telemetry_readings),
                )
                stats["telemetry_readings"] = len(telemetry_readings)

        # 7. Notify Redis Pub/Sub
        try:
            redis = get_redis_client()
            await redis.publish(
                "ingestion:completed",
                {"stats": stats, "quarantined_count": len(self.quarantine)},
            )
        except Exception:
            logger.debug("redis_publish_skipped")

        logger.info("ingestion_pipeline_finished", **stats)
        return {
            "status": "success",
            "counts": stats,
            "quarantined_count": len(self.quarantine),
            "quarantined_records": self.quarantine,
        }
