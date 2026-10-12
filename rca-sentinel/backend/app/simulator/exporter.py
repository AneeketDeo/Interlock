"""Cypher and JSON exporter for synthetic manufacturing data.

Exports the generated manufacturing graph into parameterized Cypher statements
that can be directly executed against Neo4j Aura or written to disk.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CypherExporter:
    """Exports dataset to Cypher statements and JSON files."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    def to_cypher_statements(self) -> list[str]:
        """Convert in-memory data dict into executable Cypher statements."""
        statements: list[str] = []

        # 1. Plants
        for p in self.data.get("plants", []):
            statements.append(
                f"MERGE (p:Plant {{id: '{p['id']}'}}) "
                f"SET p.name = '{p['name']}', p.code = '{p.get('code', '')}', "
                f"p.location = '{p.get('location', '')}', p.active = {str(p.get('active', True)).lower()};"
            )

        # 2. Production Lines
        for line in self.data.get("lines", []):
            statements.append(
                f"MERGE (l:ProductionLine {{id: '{line['id']}'}}) "
                f"SET l.name = '{line['name']}', l.code = '{line.get('code', '')}', "
                f"l.target_rate_uph = {line.get('target_rate_uph', 0.0)}, l.active = {str(line.get('active', True)).lower()} "
                f"WITH l "
                f"MATCH (p:Plant {{id: '{line['plant_id']}'}}) "
                f"MERGE (p)-[:CONTAINS_LINE]->(l);"
            )

        # 3. Machines
        for m in self.data.get("machines", []):
            statements.append(
                f"MERGE (m:Machine {{id: '{m['id']}'}}) "
                f"SET m.name = '{m['name']}', m.code = '{m.get('code', '')}', "
                f"m.machine_type = '{m.get('machine_type', '')}', m.model = '{m.get('model', '')}', "
                f"m.serial_number = '{m.get('serial_number', '')}', m.status = '{m.get('status', 'operational')}' "
                f"WITH m "
                f"MATCH (l:ProductionLine {{id: '{m['line_id']}'}}) "
                f"MERGE (l)-[:CONTAINS_MACHINE]->(m);"
            )

        # 4. Sensors
        for s in self.data.get("sensors", []):
            statements.append(
                f"MERGE (sn:Sensor {{id: '{s['id']}'}}) "
                f"SET sn.name = '{s['name']}', sn.sensor_type = '{s.get('sensor_type', '')}', "
                f"sn.tag = '{s.get('tag', '')}', sn.unit = '{s.get('unit', '')}', "
                f"sn.warning_threshold = {s.get('warning_threshold', 0.0)}, "
                f"sn.critical_threshold = {s.get('critical_threshold', 0.0)} "
                f"WITH sn "
                f"MATCH (m:Machine {{id: '{s['machine_id']}'}}) "
                f"MERGE (m)-[:HAS_SENSOR]->(sn);"
            )

        # 5. Suppliers
        for sup in self.data.get("suppliers", []):
            statements.append(
                f"MERGE (s:Supplier {{id: '{sup['id']}'}}) "
                f"SET s.name = '{sup['name']}', s.code = '{sup.get('code', '')}', "
                f"s.tier = {sup.get('tier', 1)}, s.country = '{sup.get('country', '')}', "
                f"s.quality_rating = {sup.get('quality_rating', 100.0)}, "
                f"s.audit_status = '{sup.get('audit_status', 'certified')}';"
            )

        # 6. Material Lots & Supply Chain Links
        for lot in self.data.get("material_lots", []):
            prop_str = json.dumps(lot.get("properties", {}))
            escaped_props = prop_str.replace("'", "\\'")
            statements.append(
                f"MERGE (ml:MaterialLot {{id: '{lot['id']}'}}) "
                f"SET ml.lot_number = '{lot['lot_number']}', ml.material_type = '{lot.get('material_type', '')}', "
                f"ml.quantity = {lot.get('quantity', 0.0)}, ml.unit = '{lot.get('unit', '')}', "
                f"ml.status = '{lot.get('status', 'released')}', ml.properties_json = '{escaped_props}' "
                f"WITH ml "
                f"MATCH (sup:Supplier {{id: '{lot['supplier_id']}'}}) "
                f"MERGE (sup)-[:SUPPLIED_LOT]->(ml);"
            )
            # Consumption / Parent links
            for parent_id in lot.get("parent_lot_ids", []):
                statements.append(
                    f"MATCH (child:MaterialLot {{id: '{lot['id']}'}}), (parent:MaterialLot {{id: '{parent_id}'}}) "
                    f"MERGE (child)-[:CONSUMED_LOT]->(parent);"
                )
            if lot.get("assigned_to_machine"):
                statements.append(
                    f"MATCH (ml:MaterialLot {{id: '{lot['id']}'}}), (m:Machine {{id: '{lot['assigned_to_machine']}'}}) "
                    f"MERGE (m)-[:PROCESSED_LOT]->(ml);"
                )

        # 7. Failure Modes
        for fm in self.data.get("failure_modes", []):
            statements.append(
                f"MERGE (f:FailureMode {{id: '{fm['id']}'}}) "
                f"SET f.code = '{fm.get('code', '')}', f.name = '{fm['name']}', "
                f"f.description = '{fm.get('description', '')}', f.severity = {fm.get('severity', 5)}, "
                f"f.occurrence = {fm.get('occurrence', 3)}, f.detection = {fm.get('detection', 3)}, "
                f"f.rpn = {fm.get('rpn', 45)};"
            )

        # 8. Maintenance Events
        for me in self.data.get("maintenance_events", []):
            escaped_notes = me.get("notes", "").replace("'", "\\'")
            statements.append(
                f"MERGE (ev:MaintenanceEvent {{id: '{me['id']}'}}) "
                f"SET ev.event_type = '{me.get('event_type', '')}', ev.title = '{me.get('title', '')}', "
                f"ev.technician_name = '{me.get('technician_name', '')}', ev.crew_name = '{me.get('crew_name', '')}', "
                f"ev.shift = {me.get('shift', 1)}, ev.timestamp = datetime('{me['timestamp']}'), "
                f"ev.calibration_offset_mm = {me.get('calibration_offset_mm', 0.0)}, "
                f"ev.notes = '{escaped_notes}', ev.status = '{me.get('status', 'completed')}' "
                f"WITH ev "
                f"MATCH (m:Machine {{id: '{me['machine_id']}'}}) "
                f"MERGE (m)-[:HAS_MAINTENANCE_EVENT]->(ev);"
            )

        # 9. Operator Logs
        for op_log in self.data.get("operator_logs", []):
            escaped_text = op_log.get("text", "").replace("'", "\\'")
            statements.append(
                f"MERGE (ol:OperatorLog {{id: '{op_log['id']}'}}) "
                f"SET ol.operator_id = '{op_log.get('operator_id', '')}', ol.operator_name = '{op_log.get('operator_name', '')}', "
                f"ol.shift = {op_log.get('shift', 1)}, ol.timestamp = datetime('{op_log['timestamp']}'), "
                f"ol.text = '{escaped_text}' "
                f"WITH ol "
                f"MATCH (m:Machine {{id: '{op_log['machine_id']}'}}) "
                f"MERGE (m)-[:HAS_OPERATOR_LOG]->(ol);"
            )

        return statements

    def save_json(self, target_path: Path) -> None:
        """Save synthetic data (excluding large telemetry series) to JSON."""
        clean_data = {k: v for k, v in self.data.items() if k != "telemetry"}
        clean_data["telemetry_count"] = len(self.data.get("telemetry", []))
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(json.dumps(clean_data, indent=2, default=str), encoding="utf-8")
