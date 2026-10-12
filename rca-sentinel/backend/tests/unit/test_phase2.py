"""Tests for Phase 2: Synthetic Data Generation, Mappers, Entity Resolution, and Ingestion Pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.ingestion.entity_resolution import EntityResolver
from app.ingestion.mappers.cmms_mapper import CmmsMapper
from app.ingestion.mappers.erp_mapper import ErpMapper
from app.ingestion.mappers.operator_log_mapper import OperatorLogMapper
from app.ingestion.mappers.plc_mapper import PlcMapper
from app.ingestion.pipeline import IngestionPipeline
from app.simulator.exporter import CypherExporter
from app.simulator.generator import SyntheticDataGenerator
from app.simulator.scenarios import (
    GoldenScenarioConfig,
    GoldenScenarioGroundTruth,
    get_golden_scenario_timestamps,
)

# ── Scenario & Generator Tests ──────────────────────────────────────


class TestGoldenScenario:
    def test_timestamps_deterministic(self) -> None:
        base = datetime(2026, 10, 10, 0, 0, 0, tzinfo=UTC)
        ts1 = get_golden_scenario_timestamps(base)
        ts2 = get_golden_scenario_timestamps(base)
        assert ts1["anomaly_start"] == ts2["anomaly_start"]
        assert ts1["maintenance_event"] < ts1["anomaly_start"]
        assert ts1["anomaly_start"] < ts1["anomaly_peak"]

    def test_ground_truth_spec(self) -> None:
        gt = GoldenScenarioGroundTruth()
        assert len(gt.root_cause_components) == 2
        assert "lot-40921" in gt.culprit_lot_ids
        assert gt.culprit_supplier_id == "sup-tier3-001"
        assert gt.culprit_machine_id == "station-03b"
        assert gt.expected_severity == "critical"
        assert gt.expected_blast_radius_units == 420
        assert gt.expected_financial_impact_usd > 100000


class TestSyntheticGenerator:
    def test_generator_determinism(self) -> None:
        gen1 = SyntheticDataGenerator(seed=123)
        gen2 = SyntheticDataGenerator(seed=123)
        d1 = gen1.generate()
        d2 = gen2.generate()

        assert len(d1["plants"]) == len(d2["plants"])
        assert len(d1["machines"]) == len(d2["machines"])
        assert len(d1["material_lots"]) == len(d2["material_lots"])
        assert len(d1["telemetry"]) == len(d2["telemetry"])
        # Check identical readings
        assert d1["telemetry"][0] == d2["telemetry"][0]
        assert d1["telemetry"][100] == d2["telemetry"][100]

    def test_golden_scenario_elements_present(self) -> None:
        gen = SyntheticDataGenerator(seed=42)
        data = gen.generate()
        cfg = GoldenScenarioConfig()

        # Station 3B exists
        station_ids = [m["id"] for m in data["machines"]]
        assert cfg.STATION_ID in station_ids

        # Culprit Lot 40921 exists and is out of spec
        culprit_lot = next(
            (lot for lot in data["material_lots"] if lot["id"] == cfg.LOT_T3_ID),
            None,
        )
        assert culprit_lot is not None
        assert culprit_lot["properties"]["out_of_spec"] is True
        assert culprit_lot["properties"]["silicon_content_pct"] > 1.35

        # Lineage exists: Lot 40921 -> Lot 51804 -> Lot 62933
        tier2_lot = next(
            (lot for lot in data["material_lots"] if lot["id"] == cfg.LOT_T2_ID),
            None,
        )
        assert tier2_lot is not None
        assert cfg.LOT_T3_ID in tier2_lot["parent_lot_ids"]

        tier1_lot = next(
            (lot for lot in data["material_lots"] if lot["id"] == cfg.LOT_T1_ID),
            None,
        )
        assert tier1_lot is not None
        assert cfg.LOT_T2_ID in tier1_lot["parent_lot_ids"]

        # Maintenance WO-8821 with +0.035mm offset exists
        wo = next(
            (ev for ev in data["maintenance_events"] if ev["id"] == cfg.WORK_ORDER_ID),
            None,
        )
        assert wo is not None
        assert wo["calibration_offset_mm"] == 0.035
        assert wo["machine_id"] == cfg.STATION_ID

        # Operator shift note exists
        op_log = next(
            (log for log in data["operator_logs"] if "slight hum" in log["text"]),
            None,
        )
        assert op_log is not None
        assert op_log["machine_id"] == cfg.STATION_ID

    def test_telemetry_anomaly_behavior(self) -> None:
        gen = SyntheticDataGenerator(seed=42)
        data = gen.generate()
        cfg = GoldenScenarioConfig()

        # Baseline readings (first hour) vs anomaly peak (last hour)
        scrap_readings = [
            r for r in data["telemetry"] if r[1] == cfg.SENSOR_SCRAP_ID
        ]
        assert len(scrap_readings) > 0

        baseline_scrap = [r[3] for r in scrap_readings[:12]]
        avg_baseline = sum(baseline_scrap) / len(baseline_scrap)
        assert 0.8 <= avg_baseline <= 1.8

        peak_scrap = [r[3] for r in scrap_readings[-12:]]
        avg_peak = sum(peak_scrap) / len(peak_scrap)
        assert avg_peak >= 12.0  # Should surge to ~13.4%


# ── Exporter Tests ──────────────────────────────────────────────────


class TestCypherExporter:
    def test_cypher_export(self, tmp_path: Path) -> None:
        gen = SyntheticDataGenerator(seed=42)
        data = gen.generate()
        exporter = CypherExporter(data)

        statements = exporter.to_cypher_statements()
        assert len(statements) > 15
        assert any("MERGE (p:Plant" in stmt for stmt in statements)
        assert any("MERGE (ml:MaterialLot" in stmt for stmt in statements)
        assert any("CONSUMED_LOT" in stmt for stmt in statements)

        # JSON export
        json_target = tmp_path / "synthetic_fixture.json"
        exporter.save_json(json_target)
        assert json_target.exists()
        assert json_target.stat().st_size > 500


# ── Entity Resolver Tests ───────────────────────────────────────────


class TestEntityResolver:
    def test_normalize_id(self) -> None:
        resolver = EntityResolver()
        assert resolver.normalize_id("  LOT#40921  ") == "lot-40921"
        assert resolver.normalize_id("STN / 03B") == "stn-03b"

    def test_resolve_machine_id(self) -> None:
        resolver = EntityResolver()
        assert resolver.resolve_machine_id("STN-03B") == "station-03b"
        assert resolver.resolve_machine_id("station-3b") == "station-03b"
        assert resolver.resolve_machine_id("dmg-nhx-5000") == "station-03b"
        assert resolver.resolve_machine_id("station-01a") == "station-01a"

    def test_resolve_supplier_id(self) -> None:
        resolver = EntityResolver()
        assert resolver.resolve_supplier_id("AlloyTech Global") == "sup-tier3-001"
        assert resolver.resolve_supplier_id("al-tech-01") == "sup-tier3-001"
        assert resolver.resolve_supplier_id("Precision Stampings Co") == "sup-tier2-001"

    def test_reconcile_lot_record(self) -> None:
        resolver = EntityResolver()
        rec = {
            "lot_number": "40921",
            "supplier_id": "AlloyTech Global",
            "assigned_to_machine": "dmg-nhx-5000",
        }
        reconciled = resolver.reconcile_lot_record(rec)
        assert reconciled["id"] == "lot-40921"
        assert reconciled["supplier_id"] == "sup-tier3-001"
        assert reconciled["assigned_to_machine"] == "station-03b"


# ── Ingestion Mappers Tests ─────────────────────────────────────────


class TestMappers:
    def test_plc_mapper(self) -> None:
        raw = {
            "timestamp": "2026-10-10T12:00:00Z",
            "sensor_id": "sensor-vib-03b",
            "tag": "SPINDLE_VIB_RMS",
            "value": 4.12,
            "quality": 192,
        }
        ts, sid, tag, val, q = PlcMapper.map_reading(raw)
        assert sid == "sensor-vib-03b"
        assert tag == "SPINDLE_VIB_RMS"
        assert val == 4.12
        assert q == 192
        assert ts.tzinfo is not None

    def test_erp_mapper(self) -> None:
        mapper = ErpMapper()
        raw_lot = {
            "batch_id": "40921",
            "vendor_id": "AlloyTech Global",
            "item_code": "alloy_ingot",
            "quantity": 5000.0,
            "parent_lot_ids": ["raw-01"],
            "assigned_to_machine": "stn-03b",
        }
        lot = mapper.map_lot(raw_lot)
        assert lot["id"] == "lot-40921"
        assert lot["supplier_id"] == "sup-tier3-001"
        assert lot["assigned_to_machine"] == "station-03b"
        assert lot["parent_lot_ids"] == ["lot-raw-01"]

    def test_cmms_mapper(self) -> None:
        mapper = CmmsMapper()
        raw_wo = {
            "work_order_id": "8821",
            "asset_id": "stn-03b",
            "event_type": "bearing_swap",
            "calibration_offset_mm": 0.035,
            "notes": "Spindle bearing replaced",
        }
        event = mapper.map_maintenance_event(raw_wo)
        assert event["id"] == "wo-8821"
        assert event["machine_id"] == "station-03b"
        assert event["calibration_offset_mm"] == 0.035

    def test_operator_log_mapper_tag_extraction(self) -> None:
        mapper = OperatorLogMapper()
        raw_log = {
            "station": "stn-03b",
            "operator_name": "Oscar Operator",
            "text": "Spindle felt warm after bearing swap, slight hum, adjusted feed rate -5%.",
        }
        log = mapper.map_log(raw_log)
        assert log["machine_id"] == "station-03b"
        assert "spindle" in log["tags"]
        assert "bearing" in log["tags"]
        assert "temperature" in log["tags"]
        assert "vibration" in log["tags"]


# ── Ingestion Pipeline Tests ────────────────────────────────────────


class TestIngestionPipeline:
    @pytest.mark.asyncio
    async def test_pipeline_quarantine_bad_records(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pipeline = IngestionPipeline()
        # Mock repositories to avoid needing live Aura
        monkeypatch.setattr(pipeline.topology_repo, "upsert_plants", AsyncMock(return_value=1))
        monkeypatch.setattr(pipeline.topology_repo, "upsert_lines", AsyncMock(return_value=1))
        monkeypatch.setattr(pipeline.topology_repo, "upsert_machines", AsyncMock(return_value=1))
        monkeypatch.setattr(pipeline.topology_repo, "upsert_sensors", AsyncMock(return_value=1))
        monkeypatch.setattr(pipeline.supply_repo, "upsert_suppliers", AsyncMock(return_value=1))
        monkeypatch.setattr(pipeline.supply_repo, "upsert_material_lots", AsyncMock(return_value=1))
        monkeypatch.setattr(pipeline.failure_repo, "upsert_failure_modes", AsyncMock(return_value=1))
        monkeypatch.setattr(pipeline.maint_repo, "upsert_maintenance_events", AsyncMock(return_value=1))
        monkeypatch.setattr(pipeline.maint_repo, "upsert_operator_logs", AsyncMock(return_value=1))

        data = {
            "plants": [{"id": "p1", "name": "Plant 1", "active": True}],
            "suppliers": [
                {"id": "sup-valid", "name": "GoodCo", "tier": 2},
                {"id": "sup-bad", "name": "BadCo", "tier": 5},  # Invalid tier 5
            ],
            "material_lots": [
                {
                    "id": "lot-1",
                    "lot_number": "001",
                    "supplier_id": "sup-valid",
                    "material_type": "steel",
                    "quantity": 100.0,
                },
                {
                    "id": "lot-2",
                    # missing lot_number
                    "supplier_id": "sup-valid",
                    "material_type": "steel",
                    "quantity": 100.0,
                },
            ],
        }

        result = await pipeline.ingest_synthetic_data(data)
        assert result["status"] == "success"
        assert result["quarantined_count"] == 2
        quarantine_types = [q["entity_type"] for q in result["quarantined_records"]]
        assert "Supplier" in quarantine_types
        assert "MaterialLot" in quarantine_types
