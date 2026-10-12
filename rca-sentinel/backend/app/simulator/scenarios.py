"""Golden scenario definition and injection parameters.

The Golden Scenario models a real-world multi-silo manufacturing disaster:
1. Tier-3 Supplier ("AlloyTech Global") delivers raw alloy ingot Lot #40921
   with out-of-spec silicon (1.8% vs 1.2% nominal, exceeding 1.35% max limit).
2. The alloy is stamped into blanks by Tier-2 "Precision Stampings Co" (Lot #51804),
   assembled into powertrain carriers by Tier-1 "Apex Subassemblies" (Lot #62933),
   and fed into Plant 1, Line 3, Station B (CNC Milling & Thermal Treatment).
3. Station B underwent bearing replacement during Shift 2 by Crew B (WO-8821),
   but calibration offset was left at +0.035mm (exceeding tolerance +0.010mm).
4. Operator Oscar Operator notes in shift log:
   "Spindle felt warm after bearing swap, slight hum, adjusted feed rate -5% to compensate."
5. When out-of-spec alloy enters Station B:
   - Spindle bearing vibration spikes 3.8x (to 4.2 mm/s vs 1.1 mm/s baseline)
   - Spindle temperature jumps to 87.4°C (threshold 65°C)
   - Scrap rate surges from 1.2% to 13.4% (+12.2% spike) within 45 minutes
   - Micro-fractures propagate through 420 machined cylinder units.

Ground Truth Root Cause:
- Primary: Spindle miscalibration (+0.035mm offset) on Station B
- Compounding: Out-of-spec Tier-3 raw alloy Lot #40921 (1.8% silicon)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any


@dataclass(frozen=True)
class GoldenScenarioConfig:
    """Config constants for the golden scenario."""

    # Scenario IDs
    SCENARIO_ID: str = "SCENARIO-GOLDEN-40921"
    PLANT_ID: str = "plant-stuttgart-01"
    PLANT_NAME: str = "Stuttgart Powertrain Plant 1"
    LINE_ID: str = "line-03"
    LINE_NAME: str = "Powertrain Assembly Line 3"
    STATION_ID: str = "station-03b"
    STATION_NAME: str = "Station B (CNC Milling & Thermal Treatment)"

    # Sensors on Station B
    SENSOR_VIB_ID: str = "sensor-vib-03b"
    SENSOR_TEMP_ID: str = "sensor-temp-03b"
    SENSOR_SCRAP_ID: str = "sensor-scrap-03"
    SENSOR_CURRENT_ID: str = "sensor-curr-03b"

    # Supply Chain Chain
    SUPPLIER_T3_ID: str = "sup-tier3-001"
    SUPPLIER_T3_NAME: str = "AlloyTech Global"
    LOT_T3_ID: str = "lot-40921"
    LOT_T3_NUMBER: str = "LOT-40921"
    LOT_T3_SILICON_PCT: float = 1.82  # Nominal 1.2%, limit 1.35%

    SUPPLIER_T2_ID: str = "sup-tier2-001"
    SUPPLIER_T2_NAME: str = "Precision Stampings Co"
    LOT_T2_ID: str = "lot-51804"
    LOT_T2_NUMBER: str = "LOT-51804"

    SUPPLIER_T1_ID: str = "sup-tier1-001"
    SUPPLIER_T1_NAME: str = "Apex Subassemblies"
    LOT_T1_ID: str = "lot-62933"
    LOT_T1_NUMBER: str = "LOT-62933"

    # Maintenance & Crew
    WORK_ORDER_ID: str = "wo-8821"
    OPERATOR_ID: str = "op-oscar-001"
    OPERATOR_NAME: str = "Oscar Operator"
    TECHNICIAN_ID: str = "tech-marcus-002"
    TECHNICIAN_NAME: str = "Marcus Vance"
    CREW_NAME: str = "Maintenance Crew B"
    CALIBRATION_OFFSET_MM: float = 0.035  # Max tolerance +0.010mm

    # Telemetry Thresholds & Values
    BASELINE_SCRAP_PCT: float = 1.2
    ANOMALY_SCRAP_PCT: float = 13.4
    BASELINE_VIB_RMS: float = 1.05
    ANOMALY_VIB_RMS: float = 4.15
    BASELINE_TEMP_C: float = 54.2
    ANOMALY_TEMP_C: float = 87.4
    MAX_TEMP_THRESHOLD_C: float = 65.0

    # Timing (relative to base timestamp)
    SIMULATION_DURATION_HOURS: int = 48
    ANOMALY_START_HOUR: int = 42
    ANOMALY_RAMP_MINUTES: int = 45


@dataclass
class GoldenScenarioGroundTruth:
    """Expected diagnostic outputs from AI reasoning agents."""

    root_cause_components: list[str] = field(
        default_factory=lambda: [
            "Station B Spindle Bearing Miscalibration (+0.035mm offset)",
            "Tier-3 AlloyTech Global Lot #40921 Silicon Out-of-Spec (1.82% vs 1.2%)",
        ]
    )
    culprit_lot_ids: list[str] = field(
        default_factory=lambda: ["lot-40921", "lot-51804", "lot-62933"]
    )
    culprit_supplier_id: str = "sup-tier3-001"
    culprit_machine_id: str = "station-03b"
    culprit_work_order_id: str = "wo-8821"
    culprit_operator_log: str = (
        "Spindle felt warm after bearing swap, slight hum, adjusted feed rate -5% to compensate."
    )
    expected_failure_mode: str = "FM-SPINDLE-THERMAL"
    expected_severity: str = "critical"
    expected_blast_radius_units: int = 420
    expected_financial_impact_usd: float = 186500.00
    expected_remediation_actions: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {
                "type": "interlock_equipment",
                "target_entity": "station-03b",
                "description": "Emergency soft stop / interlock on Station B CNC Milling",
                "requires_human_approval": True,
            },
            {
                "type": "erp_quarantine",
                "target_entity": "lot-40921",
                "description": "Quarantine Lot #40921 across warehouses and re-route Line 3 orders",
                "requires_human_approval": True,
            },
            {
                "type": "cmms_work_order",
                "target_entity": "station-03b",
                "description": "Urgent recalibration and spindle bearing inspection on Station B",
                "requires_human_approval": True,
            },
        ]
    )


def get_golden_scenario_timestamps(
    base_time: datetime | None = None,
) -> dict[str, datetime]:
    """Calculate deterministic timestamps for the golden scenario events."""
    if base_time is None:
        base_time = datetime(2026, 10, 10, 0, 0, 0, tzinfo=UTC)

    cfg = GoldenScenarioConfig()
    maint_time = base_time + timedelta(hours=36)  # Maintenance during shift 2
    lot_entry_time = base_time + timedelta(hours=cfg.ANOMALY_START_HOUR)
    spike_peak_time = lot_entry_time + timedelta(minutes=cfg.ANOMALY_RAMP_MINUTES)
    end_time = base_time + timedelta(hours=cfg.SIMULATION_DURATION_HOURS)

    return {
        "simulation_start": base_time,
        "maintenance_event": maint_time,
        "lot_entry": lot_entry_time,
        "anomaly_start": lot_entry_time,
        "anomaly_peak": spike_peak_time,
        "simulation_end": end_time,
    }
