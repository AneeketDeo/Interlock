"""Deterministic, seeded synthetic manufacturing data generator.

Generates topology (Plant -> Line -> Machine -> Sensor),
multi-tier supply chain (Tier 3 -> Tier 2 -> Tier 1 -> Assembly),
maintenance records, operator shift notes, failure modes (PFMEA),
and 48 hours of realistic time-series telemetry with the golden anomaly.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import Settings, get_settings
from app.simulator.scenarios import (
    GoldenScenarioConfig,
    get_golden_scenario_timestamps,
)


class SyntheticDataGenerator:
    """Generates synthetic manufacturing and graph data with golden anomaly injection."""

    def __init__(self, settings: Settings | None = None, seed: int = 42) -> None:
        self.settings = settings or get_settings()
        self.seed = seed
        self.rng = random.Random(seed)
        self.cfg = GoldenScenarioConfig()

    def generate(self, base_time: datetime | None = None) -> dict[str, Any]:
        """Generate complete synthetic dataset."""
        if base_time is None:
            base_time = datetime(2026, 10, 10, 0, 0, 0, tzinfo=UTC)

        timestamps = get_golden_scenario_timestamps(base_time)

        plants = self._generate_plants()
        lines = self._generate_lines(plants)
        machines = self._generate_machines(lines)
        sensors = self._generate_sensors(machines)
        suppliers = self._generate_suppliers()
        material_lots = self._generate_material_lots(suppliers)
        failure_modes = self._generate_failure_modes()
        maintenance_events = self._generate_maintenance_events(machines, timestamps)
        operator_logs = self._generate_operator_logs(machines, timestamps)
        telemetry = self._generate_telemetry(sensors, timestamps)

        return {
            "plants": plants,
            "lines": lines,
            "machines": machines,
            "sensors": sensors,
            "suppliers": suppliers,
            "material_lots": material_lots,
            "failure_modes": failure_modes,
            "maintenance_events": maintenance_events,
            "operator_logs": operator_logs,
            "telemetry": telemetry,
            "metadata": {
                "generated_at": datetime.now(UTC).isoformat(),
                "seed": self.seed,
                "golden_scenario_id": self.cfg.SCENARIO_ID,
                "timestamps": {k: v.isoformat() for k, v in timestamps.items()},
            },
        }

    # ── Topology ────────────────────────────────────────────────────────

    def _generate_plants(self) -> list[dict[str, Any]]:
        return [
            {
                "id": self.cfg.PLANT_ID,
                "name": self.cfg.PLANT_NAME,
                "code": "STU-01",
                "location": "Stuttgart, Germany",
                "active": True,
            },
            {
                "id": "plant-munich-02",
                "name": "Munich Precision Systems 2",
                "code": "MUC-02",
                "location": "Munich, Germany",
                "active": True,
            },
        ]

    def _generate_lines(
        self, plants: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        primary_plant_id = plants[0]["id"]
        return [
            {
                "id": "line-01",
                "name": "Stamping & Blanking Line 1",
                "code": "LINE-01",
                "plant_id": primary_plant_id,
                "target_rate_uph": 120.0,
                "active": True,
            },
            {
                "id": "line-02",
                "name": "Component Machining Line 2",
                "code": "LINE-02",
                "plant_id": primary_plant_id,
                "target_rate_uph": 90.0,
                "active": True,
            },
            {
                "id": self.cfg.LINE_ID,
                "name": self.cfg.LINE_NAME,
                "code": "LINE-03",
                "plant_id": primary_plant_id,
                "target_rate_uph": 85.0,
                "active": True,
            },
        ]

    def _generate_machines(
        self, lines: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        machines: list[dict[str, Any]] = [
            # Line 1
            {
                "id": "station-01a",
                "name": "Station 1A (Coil Feeder)",
                "code": "STN-01A",
                "line_id": "line-01",
                "machine_type": "feeder",
                "model": "Siemens CoilFeed 400",
                "serial_number": "SN-CF-10029",
                "status": "operational",
            },
            {
                "id": "station-01b",
                "name": "Station 1B (Hydraulic Press)",
                "code": "STN-01B",
                "line_id": "line-01",
                "machine_type": "press",
                "model": "Schuler ServoPress 800",
                "serial_number": "SN-SP-38291",
                "status": "operational",
            },
            # Line 2
            {
                "id": "station-02a",
                "name": "Station 2A (Rough Boring)",
                "code": "STN-02A",
                "line_id": "line-02",
                "machine_type": "cnc_mill",
                "model": "Makino A51nx",
                "serial_number": "SN-MK-58291",
                "status": "operational",
            },
            {
                "id": "station-02b",
                "name": "Station 2B (Precision Honing)",
                "code": "STN-02B",
                "line_id": "line-02",
                "machine_type": "hone",
                "model": "Gehring Honing System 4",
                "serial_number": "SN-GH-29401",
                "status": "operational",
            },
            # Line 3 (Culprit Line)
            {
                "id": "station-03a",
                "name": "Station 3A (Blank Preparation & Wash)",
                "code": "STN-03A",
                "line_id": self.cfg.LINE_ID,
                "machine_type": "washer",
                "model": "Durr EcoClean 200",
                "serial_number": "SN-DC-92811",
                "status": "operational",
            },
            {
                "id": self.cfg.STATION_ID,
                "name": self.cfg.STATION_NAME,
                "code": "STN-03B",
                "line_id": self.cfg.LINE_ID,
                "machine_type": "cnc_mill",
                "model": "DMG Mori NHX 5000 5-Axis",
                "serial_number": "SN-DMG-44910",
                "status": "operational",
            },
            {
                "id": "station-03c",
                "name": "Station 3C (Automated Optical Inspection)",
                "code": "STN-03C",
                "line_id": self.cfg.LINE_ID,
                "machine_type": "aoi_inspection",
                "model": "Zeiss Metrotom 1500 CT",
                "serial_number": "SN-ZS-88129",
                "status": "operational",
            },
        ]
        return machines

    def _generate_sensors(
        self, machines: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        sensors: list[dict[str, Any]] = []

        # Culprit Station Sensors
        sensors.extend([
            {
                "id": self.cfg.SENSOR_VIB_ID,
                "name": "Spindle Bearing Vibration Sensor (RMS)",
                "machine_id": self.cfg.STATION_ID,
                "sensor_type": "vibration",
                "tag": "SPINDLE_VIB_RMS",
                "unit": "mm/s",
                "nominal_min": 0.5,
                "nominal_max": 1.5,
                "warning_threshold": 2.2,
                "critical_threshold": 3.0,
            },
            {
                "id": self.cfg.SENSOR_TEMP_ID,
                "name": "Spindle Bearing Thermal Probe",
                "machine_id": self.cfg.STATION_ID,
                "sensor_type": "temperature",
                "tag": "SPINDLE_TEMP_C",
                "unit": "°C",
                "nominal_min": 45.0,
                "nominal_max": 60.0,
                "warning_threshold": 65.0,
                "critical_threshold": 75.0,
            },
            {
                "id": self.cfg.SENSOR_SCRAP_ID,
                "name": "Station 3 Line Scrap Counter",
                "machine_id": self.cfg.STATION_ID,
                "sensor_type": "scrap_counter",
                "tag": "SCRAP_RATE_PCT",
                "unit": "%",
                "nominal_min": 0.5,
                "nominal_max": 2.0,
                "warning_threshold": 3.5,
                "critical_threshold": 6.0,
            },
            {
                "id": self.cfg.SENSOR_CURRENT_ID,
                "name": "Spindle Drive Motor Current",
                "machine_id": self.cfg.STATION_ID,
                "sensor_type": "current",
                "tag": "SPINDLE_MOTOR_AMP",
                "unit": "A",
                "nominal_min": 18.0,
                "nominal_max": 24.0,
                "warning_threshold": 28.0,
                "critical_threshold": 32.0,
            },
        ])

        # Baseline sensors for other stations
        for m in machines:
            if m["id"] == self.cfg.STATION_ID:
                continue
            sensors.append({
                "id": f"sensor-vib-{m['id']}",
                "name": f"{m['name']} Vibration Sensor",
                "machine_id": m["id"],
                "sensor_type": "vibration",
                "tag": "VIB_RMS",
                "unit": "mm/s",
                "nominal_min": 0.4,
                "nominal_max": 1.2,
                "warning_threshold": 2.0,
                "critical_threshold": 2.8,
            })
            sensors.append({
                "id": f"sensor-temp-{m['id']}",
                "name": f"{m['name']} Temperature Sensor",
                "machine_id": m["id"],
                "sensor_type": "temperature",
                "tag": "BEARING_TEMP_C",
                "unit": "°C",
                "nominal_min": 40.0,
                "nominal_max": 55.0,
                "warning_threshold": 62.0,
                "critical_threshold": 70.0,
            })

        return sensors

    # ── Supply Chain ────────────────────────────────────────────────────

    def _generate_suppliers(self) -> list[dict[str, Any]]:
        return [
            # Tier 3 (Raw Materials)
            {
                "id": self.cfg.SUPPLIER_T3_ID,
                "name": self.cfg.SUPPLIER_T3_NAME,
                "code": "SUP-T3-001",
                "tier": 3,
                "country": "Germany",
                "quality_rating": 84.5,
                "audit_status": "conditional",
            },
            {
                "id": "sup-tier3-002",
                "name": "Nordic Metals Corp",
                "code": "SUP-T3-002",
                "tier": 3,
                "country": "Sweden",
                "quality_rating": 98.2,
                "audit_status": "certified",
            },
            # Tier 2 (Component Fabricators / Stampers)
            {
                "id": self.cfg.SUPPLIER_T2_ID,
                "name": self.cfg.SUPPLIER_T2_NAME,
                "code": "SUP-T2-001",
                "tier": 2,
                "country": "Poland",
                "quality_rating": 91.0,
                "audit_status": "certified",
            },
            {
                "id": "sup-tier2-002",
                "name": "EuroForge Ltd",
                "code": "SUP-T2-002",
                "tier": 2,
                "country": "France",
                "quality_rating": 95.0,
                "audit_status": "certified",
            },
            # Tier 1 (Direct Subassembly Providers)
            {
                "id": self.cfg.SUPPLIER_T1_ID,
                "name": self.cfg.SUPPLIER_T1_NAME,
                "code": "SUP-T1-001",
                "tier": 1,
                "country": "Germany",
                "quality_rating": 94.0,
                "audit_status": "certified",
            },
            {
                "id": "sup-tier1-002",
                "name": "Delta Power Systems",
                "code": "SUP-T1-002",
                "tier": 1,
                "country": "Austria",
                "quality_rating": 97.5,
                "audit_status": "certified",
            },
        ]

    def _generate_material_lots(
        self, suppliers: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        lots: list[dict[str, Any]] = [
            # Culprit Tier-3 Lot (AlloyTech Global)
            {
                "id": self.cfg.LOT_T3_ID,
                "lot_number": self.cfg.LOT_T3_NUMBER,
                "supplier_id": self.cfg.SUPPLIER_T3_ID,
                "material_type": "AlSi10Mg_ingot",
                "quantity": 12000.0,
                "unit": "kg",
                "status": "quarantined",
                "consumed_in_lot_id": self.cfg.LOT_T2_ID,
                "properties": {
                    "silicon_content_pct": self.cfg.LOT_T3_SILICON_PCT,
                    "silicon_nominal_pct": 1.20,
                    "silicon_max_spec_pct": 1.35,
                    "hardness_brinell": 115.0,  # nominal 85
                    "out_of_spec": True,
                },
            },
            # Clean Tier-3 lots
            {
                "id": "lot-40919",
                "lot_number": "LOT-40919",
                "supplier_id": self.cfg.SUPPLIER_T3_ID,
                "material_type": "AlSi10Mg_ingot",
                "quantity": 10000.0,
                "unit": "kg",
                "status": "released",
                "consumed_in_lot_id": "lot-51801",
                "properties": {
                    "silicon_content_pct": 1.21,
                    "silicon_nominal_pct": 1.20,
                    "out_of_spec": False,
                },
            },
            {
                "id": "lot-40920",
                "lot_number": "LOT-40920",
                "supplier_id": "sup-tier3-002",
                "material_type": "AlSi10Mg_ingot",
                "quantity": 15000.0,
                "unit": "kg",
                "status": "released",
                "consumed_in_lot_id": "lot-51802",
                "properties": {
                    "silicon_content_pct": 1.19,
                    "silicon_nominal_pct": 1.20,
                    "out_of_spec": False,
                },
            },
            # Culprit Tier-2 Lot (Precision Stampings Co)
            {
                "id": self.cfg.LOT_T2_ID,
                "lot_number": self.cfg.LOT_T2_NUMBER,
                "supplier_id": self.cfg.SUPPLIER_T2_ID,
                "material_type": "powertrain_stamped_blank",
                "quantity": 2400.0,
                "unit": "pieces",
                "status": "quarantined",
                "parent_lot_ids": [self.cfg.LOT_T3_ID],
                "consumed_in_lot_id": self.cfg.LOT_T1_ID,
                "properties": {"stamping_pass": 1, "out_of_spec": True},
            },
            # Clean Tier-2 lots
            {
                "id": "lot-51801",
                "lot_number": "LOT-51801",
                "supplier_id": self.cfg.SUPPLIER_T2_ID,
                "material_type": "powertrain_stamped_blank",
                "quantity": 2000.0,
                "unit": "pieces",
                "status": "released",
                "parent_lot_ids": ["lot-40919"],
                "consumed_in_lot_id": "lot-62931",
                "properties": {"out_of_spec": False},
            },
            # Culprit Tier-1 Lot (Apex Subassemblies)
            {
                "id": self.cfg.LOT_T1_ID,
                "lot_number": self.cfg.LOT_T1_NUMBER,
                "supplier_id": self.cfg.SUPPLIER_T1_ID,
                "material_type": "cylinder_carrier_assembly",
                "quantity": 600.0,
                "unit": "assemblies",
                "status": "quarantined",
                "parent_lot_ids": [self.cfg.LOT_T2_ID],
                "assigned_to_machine": self.cfg.STATION_ID,
                "properties": {
                    "target_line": self.cfg.LINE_ID,
                    "affected_units_count": 420,
                    "out_of_spec": True,
                },
            },
            # Clean Tier-1 lots
            {
                "id": "lot-62931",
                "lot_number": "LOT-62931",
                "supplier_id": self.cfg.SUPPLIER_T1_ID,
                "material_type": "cylinder_carrier_assembly",
                "quantity": 500.0,
                "unit": "assemblies",
                "status": "released",
                "parent_lot_ids": ["lot-51801"],
                "assigned_to_machine": "station-02a",
                "properties": {"out_of_spec": False},
            },
        ]
        return lots

    # ── Maintenance & Logs ──────────────────────────────────────────────

    def _generate_maintenance_events(
        self,
        machines: list[dict[str, Any]],
        timestamps: dict[str, datetime],
    ) -> list[dict[str, Any]]:
        maint_time = timestamps["maintenance_event"]

        return [
            # Culprit Maintenance Event on Station 3B
            {
                "id": self.cfg.WORK_ORDER_ID,
                "machine_id": self.cfg.STATION_ID,
                "event_type": "bearing_replacement",
                "title": "Spindle Bearing Replacement & Re-alignment",
                "technician_id": self.cfg.TECHNICIAN_ID,
                "technician_name": self.cfg.TECHNICIAN_NAME,
                "crew_name": self.cfg.CREW_NAME,
                "shift": 2,
                "timestamp": maint_time.isoformat(),
                "duration_minutes": 115,
                "calibration_offset_mm": self.cfg.CALIBRATION_OFFSET_MM,
                "tolerance_limit_mm": 0.010,
                "notes": (
                    "Bearing replacement completed on high-speed milling spindle. "
                    f"Calibration runout offset set to +{self.cfg.CALIBRATION_OFFSET_MM}mm "
                    "due to gauge alignment drift. System passed initial spin test."
                ),
                "status": "completed",
            },
            # Routine maintenance on Station 2A
            {
                "id": "wo-8819",
                "machine_id": "station-02a",
                "event_type": "lubrication_flush",
                "title": "Routine Coolant & Lubrication Flush",
                "technician_id": "tech-anna-001",
                "technician_name": "Anna Schmidt",
                "crew_name": "Maintenance Crew A",
                "shift": 1,
                "timestamp": (maint_time - timedelta(hours=18)).isoformat(),
                "duration_minutes": 45,
                "calibration_offset_mm": 0.002,
                "tolerance_limit_mm": 0.010,
                "notes": "Coolant filtered, lube levels topped up.",
                "status": "completed",
            },
        ]

    def _generate_operator_logs(
        self,
        machines: list[dict[str, Any]],
        timestamps: dict[str, datetime],
    ) -> list[dict[str, Any]]:
        maint_time = timestamps["maintenance_event"]
        anomaly_start = timestamps["anomaly_start"]

        return [
            # Culprit Operator Log
            {
                "id": "log-shift2-001",
                "machine_id": self.cfg.STATION_ID,
                "operator_id": self.cfg.OPERATOR_ID,
                "operator_name": self.cfg.OPERATOR_NAME,
                "shift": 2,
                "timestamp": (maint_time + timedelta(hours=2)).isoformat(),
                "text": (
                    "Spindle felt warm after bearing swap, slight hum, "
                    "adjusted feed rate -5% to compensate."
                ),
                "tags": ["spindle", "warm", "bearing", "feed_rate_compensation"],
            },
            # Operator note during scrap spike
            {
                "id": "log-shift3-002",
                "machine_id": self.cfg.STATION_ID,
                "operator_id": "op-kurt-002",
                "operator_name": "Kurt Meyer",
                "shift": 3,
                "timestamp": (anomaly_start + timedelta(minutes=30)).isoformat(),
                "text": (
                    "Heavy chatter and surface micro-cracking observed on cylinder carriers. "
                    "Scrap bin filling rapidly. Notified line lead."
                ),
                "tags": ["chatter", "micro_cracks", "scrap_spike"],
            },
            # Clean shift log on Line 2
            {
                "id": "log-shift2-003",
                "machine_id": "station-02b",
                "operator_id": "op-clara-003",
                "operator_name": "Clara Weber",
                "shift": 2,
                "timestamp": (maint_time + timedelta(hours=1)).isoformat(),
                "text": "Nominal operations throughout shift. No anomalies.",
                "tags": ["nominal"],
            },
        ]

    # ── Failure Modes & PFMEA ───────────────────────────────────────────

    def _generate_failure_modes(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "FM-SPINDLE-THERMAL",
                "code": "FM-101",
                "name": "Spindle Bearing Thermal Runaway & Misalignment",
                "description": (
                    "Excessive spindle runout offset causes bearing friction, "
                    "high vibration, and thermal expansion leading to dimensional scrap."
                ),
                "severity": 9,
                "occurrence": 4,
                "detection": 3,
                "rpn": 108,
                "potential_causes": [
                    "Bearing installation misalignment",
                    "Calibration gauge error",
                    "Insufficient pre-load lubrication",
                ],
                "recommended_actions": [
                    "Emergency spindle interlock",
                    "Laser alignment and recalibration",
                    "Vibration threshold interlock trip",
                ],
            },
            {
                "id": "FM-ALLOY-BRITTLE",
                "code": "FM-204",
                "name": "Raw Material Silicon Excess Brittleness",
                "description": (
                    "Silicon content exceeding 1.35% makes aluminum alloy brittle, "
                    "inducing micro-fractures under high-speed milling cutter engagement."
                ),
                "severity": 8,
                "occurrence": 3,
                "detection": 4,
                "rpn": 96,
                "potential_causes": [
                    "Smelter batch stoichiometry error at Tier 3 supplier",
                    "Supplier spectrometer miscalibration",
                ],
                "recommended_actions": [
                    "Immediate warehouse lot quarantine",
                    "Supplier spectrometer re-audit",
                ],
            },
            {
                "id": "FM-COMPOUND-MICROFRACTURE",
                "code": "FM-309",
                "name": "Compound Runout & Brittle Alloy Induced Micro-Fractures",
                "description": (
                    "Interaction of out-of-spec hard alloy with misaligned spindle "
                    "causes severe tool vibration and catastrophic micro-fracture propagation."
                ),
                "severity": 9,
                "occurrence": 2,
                "detection": 2,
                "rpn": 36,
                "potential_causes": [
                    "Simultaneous out-of-spec alloy lot and spindle calibration drift"
                ],
                "recommended_actions": [
                    "Line soft-stop",
                    "Quarantine upstream and downstream lots",
                    "Spindle bearing inspection",
                ],
            },
        ]

    # ── Telemetry Series ────────────────────────────────────────────────

    def _generate_telemetry(
        self,
        sensors: list[dict[str, Any]],
        timestamps: dict[str, datetime],
    ) -> list[tuple[datetime, str, str, float, int]]:
        """Generate 48 hours of time-series readings with golden anomaly injection."""
        readings: list[tuple[datetime, str, str, float, int]] = []

        start_time = timestamps["simulation_start"]
        anomaly_start = timestamps["anomaly_start"]
        end_time = timestamps["simulation_end"]

        # Step by 5 minutes over 48 hours = 576 steps
        step_minutes = 5
        curr_time = start_time

        while curr_time <= end_time:
            is_anomaly = curr_time >= anomaly_start

            # Calculate anomaly progression fraction (0.0 to 1.0 ramp over 45 minutes)
            if is_anomaly:
                progress = min(
                    1.0,
                    (curr_time - anomaly_start).total_seconds()
                    / (self.cfg.ANOMALY_RAMP_MINUTES * 60),
                )
            else:
                progress = 0.0

            # 1. Culprit Station Sensors
            # Vibration
            vib_noise = self.rng.gauss(0, 0.08)
            if is_anomaly:
                vib_val = (
                    self.cfg.BASELINE_VIB_RMS
                    + (self.cfg.ANOMALY_VIB_RMS - self.cfg.BASELINE_VIB_RMS) * progress
                    + vib_noise
                )
            else:
                vib_val = max(0.4, self.cfg.BASELINE_VIB_RMS + vib_noise)
            readings.append((
                curr_time,
                self.cfg.SENSOR_VIB_ID,
                "SPINDLE_VIB_RMS",
                round(vib_val, 3),
                192,
            ))

            # Temperature
            temp_noise = self.rng.gauss(0, 0.4)
            if is_anomaly:
                temp_val = (
                    self.cfg.BASELINE_TEMP_C
                    + (self.cfg.ANOMALY_TEMP_C - self.cfg.BASELINE_TEMP_C) * progress
                    + temp_noise
                )
            else:
                temp_val = self.cfg.BASELINE_TEMP_C + temp_noise
            readings.append((
                curr_time,
                self.cfg.SENSOR_TEMP_ID,
                "SPINDLE_TEMP_C",
                round(temp_val, 2),
                192,
            ))

            # Scrap Rate
            scrap_noise = self.rng.gauss(0, 0.15)
            if is_anomaly:
                scrap_val = (
                    self.cfg.BASELINE_SCRAP_PCT
                    + (self.cfg.ANOMALY_SCRAP_PCT - self.cfg.BASELINE_SCRAP_PCT) * progress
                    + scrap_noise
                )
            else:
                scrap_val = max(0.2, self.cfg.BASELINE_SCRAP_PCT + scrap_noise)
            readings.append((
                curr_time,
                self.cfg.SENSOR_SCRAP_ID,
                "SCRAP_RATE_PCT",
                round(scrap_val, 2),
                192,
            ))

            # Spindle Motor Current
            curr_noise = self.rng.gauss(0, 0.3)
            curr_val = (
                21.0 + 9.5 * progress + curr_noise
                if is_anomaly
                else 21.0 + curr_noise
            )
            readings.append((
                curr_time,
                self.cfg.SENSOR_CURRENT_ID,
                "SPINDLE_MOTOR_AMP",
                round(curr_val, 2),
                192,
            ))

            # 2. Other stations nominal readings (sample a few to keep volume balanced)
            for s in sensors:
                if s["id"] in {
                    self.cfg.SENSOR_VIB_ID,
                    self.cfg.SENSOR_TEMP_ID,
                    self.cfg.SENSOR_SCRAP_ID,
                    self.cfg.SENSOR_CURRENT_ID,
                }:
                    continue
                # Baseline sensor reading
                if s["sensor_type"] == "vibration":
                    val = max(0.2, self.rng.gauss(0.8, 0.05))
                elif s["sensor_type"] == "temperature":
                    val = self.rng.gauss(48.0, 1.0)
                else:
                    val = 1.0
                readings.append((curr_time, s["id"], s["tag"], round(val, 2), 192))

            curr_time += timedelta(minutes=step_minutes)

        return readings
