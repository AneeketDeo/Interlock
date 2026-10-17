#!/usr/bin/env python3
"""Spanner Graph schema + loader for the RCA knowledge graph.

Commands
  ddl     write schema_tables.sql, schema_graph.sql, queries.gql   (no GCP needed)
  check   validate the CSVs against the schema offline             (no GCP needed)
  create  create the database, tables and property graph
  load    load the CSVs with batched mutations (idempotent: insert_or_update)
  verify  run the GQL queries and compare with ground_truth.json

Env/flags: --project, --instance, --database (or SPANNER_PROJECT / SPANNER_INSTANCE / SPANNER_DATABASE)
Requires for create/load/verify:  pip install google-cloud-spanner
"""
import argparse, csv, json, os, re, sys
from datetime import datetime, timezone

TYPES = {"s": "STRING(MAX)", "k": "STRING(128)", "i": "INT64", "f": "FLOAT64", "b": "BOOL", "t": "TIMESTAMP"}
GRAPH = "FactoryGraph"

# (table, csv file or None, columns, primary key)
# column token: [csv_name>]db_name[:type]  type: s string (default), i int, f float, b bool, t timestamp
NODES = [
    ("Site", "site", "site_id name city country", "site_id"),
    ("Area", "area", "area_id site_id name", "area_id"),
    ("Line", "line", "line_id name area_id product_code", "line_id"),
    ("Machine", "machine", "machine_id line_id name machine_type install_year:i", "machine_id"),
    ("Component", "component", "component_id machine_id name", "component_id"),
    ("Sensor", "sensor", "sensor_id machine_id component_id sensor_type unit sampling_hz:i", "sensor_id"),
    ("Tag", "tag", "tag_id tag_name sensor_id protocol node_id", "tag_id"),
    ("ObservationWindow", "observation_window",
     "obs_id sensor_id machine_id window_start:t window_end:t mean>mean_value:f min>min_value:f max>max_value:f "
     "std>std_dev:f sample_count:i quality is_anomalous:b", "obs_id"),
    ("Alarm", "alarm", "alarm_id sensor_id machine_id raised_at:t severity rule value:f threshold:f acknowledged_by", "alarm_id"),
    ("Anomaly", "anomaly", "anomaly_id sensor_id machine_id start>start_time:t end>end_time:t windows:i peak_residual:f anomaly_type", "anomaly_id"),
    ("Product", "product", "product_code name line_id", "product_code"),
    ("RecipeStep", "recipe_step", "recipe_step_id line_id seq:i name temp_setpoint_c:f", "recipe_step_id"),
    ("WorkOrder", "work_order",
     "work_order_id machine_id line_id shift_id operator_id product_code lot_id batch_id planned_start:t planned_end:t "
     "units_planned:i units_produced:i units_good:i units_scrap:i units_rework:i scrap_rate:f status", "work_order_id"),
    ("Batch", "batch", "batch_id work_order_id product_code lot_id qty:i status machine_id", "batch_id"),
    ("Inspection", "inspection",
     "inspection_id work_order_id machine_id inspected_units:i scrap_units:i rework_units:i dominant_defect_code first_pass_yield:f", "inspection_id"),
    ("DefectCode", "defect_code", "defect_code description", "defect_code"),
    ("Employee", "employee", "employee_id name role crew_id", "employee_id"),
    ("Crew", "crew", "crew_id name", "crew_id"),
    ("Shift", "shift", "shift_id shift_name start>start_time:t end>end_time:t crew_id status", "shift_id"),
    ("Handover", "handover",
     "handover_id from_shift_id to_shift_id from_crew_id to_crew_id handover_time:t duration_min:i checklist_complete:b rushed:b notes", "handover_id"),
    ("TrainingRecord", "training_record", "training_id employee_id machine_type issued:t expires:t status", "training_id"),
    ("MaintenanceOrder", "maintenance_order",
     "order_id machine_id order_type plan_id crew_id technician_id scheduled_start:t actual_start:t actual_end:t status spare_part_id", "order_id"),
    ("Calibration", "calibration",
     "calibration_id order_id machine_id started_at:t ended_at:t steps_required:i steps_completed:i skipped_step duration_min:i "
     "handover_id recorded_result verification_signed_off:b", "calibration_id"),
    ("PmPlan", "pm_plan", "plan_id name interval_days:i", "plan_id"),
    ("SparePart", "spare_part", "spare_part_id name stock_qty:i", "spare_part_id"),
    ("Supplier", "supplier", "supplier_id name tier:i iatf_certified:b shares_batch_data:b", "supplier_id"),
    ("Material", "material", "material_id name spec_hardness_hrc spec_carbon_pct spec_mn_pct", "material_id"),
    ("Bom", "bom", "bom_id product_code material_id kg_per_unit:f", "bom_id"),
    ("MaterialLot", "material_lot", "lot_id material_id qty_kg:i received_at:t po_id mill_cert_id status", "lot_id"),
    ("MillCertificate", "mill_certificate",
     "mill_cert_id lot_id heat_number issued_by_supplier_id hardness_hrc:f carbon_pct:f manganese_pct:f within_spec:b edge_flag document_ref", "mill_cert_id"),
    ("PurchaseOrder", "purchase_order", "po_id supplier_id material_id qty_kg:i ordered_at:t received_at:t", "po_id"),
    ("FailureMode", "failure_mode", "failure_mode_id category description severity:i occurrence:i detection:i rpn:i", "failure_mode_id"),
    ("ControlPlan", "control_plan", "control_plan_id failure_mode_id description", "control_plan_id"),
    ("Incident", "incident",
     "incident_id title status severity detected_at:t detected_by metric baseline_value:f observed_value:f description line_ids closed_at:t", "incident_id"),
    ("Evidence", "evidence", "evidence_id incident_id evidence_type ref_id summary", "evidence_id"),
    ("Cause", "cause", "cause_id incident_id description category confidence:f", "cause_id"),
    ("CorrectiveAction", "corrective_action", "corrective_action_id incident_id description status owner_id", "corrective_action_id"),
    ("Decision", "decision", "decision_id incident_id decision_type proposed_by summary status", "decision_id"),
    ("Approval", "approval", "approval_id decision_id approver_id approved_at:t outcome", "approval_id"),
    # written by the agent at runtime, no CSV
    ("Action", None, "action_id incident_id decision_id action_type target_id description status proposed_by proposed_at:t payload", "action_id"),
]
# edge tables that have their own CSV: (table, csv, columns, pk, label, src_col, src_table, dst_col, dst_table)
OWN_EDGES = [
    ("Processed", "edges_processed", "machine_id lot_id first_used:t last_used:t work_orders:i units:i", "machine_id lot_id", "PROCESSED", "machine_id", "Machine", "lot_id", "MaterialLot"),
    ("SuppliedBy", "edges_supplied_by", "lot_id supplier_id relation", "lot_id supplier_id relation", "SUPPLIED_BY", "lot_id", "MaterialLot", "supplier_id", "Supplier"),
    ("Supplies", "edges_supplies", "supplier_id buyer_supplier_id material_id", "supplier_id buyer_supplier_id", "SUPPLIES", "supplier_id", "Supplier", "buyer_supplier_id", "Supplier"),
    ("MaintenanceOn", "edges_maintenance_on", "order_id machine_id", "order_id machine_id", "MAINTENANCE_ON", "order_id", "MaintenanceOrder", "machine_id", "Machine"),
    ("PerformedBy", "edges_performed_by", "order_id crew_id", "order_id crew_id", "PERFORMED_BY", "order_id", "MaintenanceOrder", "crew_id", "Crew"),
    ("MemberOf", "edges_member_of", "employee_id crew_id", "employee_id crew_id", "MEMBER_OF", "employee_id", "Employee", "crew_id", "Crew"),
    ("Affects", "edges_affects", "incident_id machine_id", "incident_id machine_id", "AFFECTS", "incident_id", "Incident", "machine_id", "Machine"),
    ("EvidencedBy", "edges_evidenced_by", "incident_id evidence_id", "incident_id evidence_id", "EVIDENCED_BY", "incident_id", "Incident", "evidence_id", "Evidence"),
    ("HasCause", "edges_has_cause", "incident_id cause_id", "incident_id cause_id", "HAS_CAUSE", "incident_id", "Incident", "cause_id", "Cause"),
    ("CauseMapsTo", "edges_cause_maps_to", "cause_id failure_mode_id", "cause_id failure_mode_id", "CAUSE_MAPS_TO", "cause_id", "Cause", "failure_mode_id", "FailureMode"),
    ("CorrectedBy", "edges_corrected_by", "incident_id corrective_action_id", "incident_id corrective_action_id", "CORRECTED_BY", "incident_id", "Incident", "corrective_action_id", "CorrectiveAction"),
    ("HasDecision", "edges_has_decision", "incident_id decision_id", "incident_id decision_id", "HAS_DECISION", "incident_id", "Incident", "decision_id", "Decision"),
    ("ApprovedBy", "edges_approved_by", "decision_id approval_id", "decision_id approval_id", "APPROVED_BY", "decision_id", "Decision", "approval_id", "Approval"),
    ("ControlledBy", "edges_controlled_by", "failure_mode_id control_plan_id", "failure_mode_id control_plan_id", "CONTROLLED_BY", "failure_mode_id", "FailureMode", "control_plan_id", "ControlPlan"),
]
# edges derived from foreign-key columns of node tables: (alias, table, label, key, src_col, src_table, dst_col, dst_table)
ALIAS_EDGES = [
    ("SiteHasArea", "Area", "HAS_AREA", "area_id", "site_id", "Site", "area_id", "Area"),
    ("AreaHasLine", "Line", "HAS_LINE", "line_id", "area_id", "Area", "line_id", "Line"),
    ("LineHasMachine", "Machine", "HAS_MACHINE", "machine_id", "line_id", "Line", "machine_id", "Machine"),
    ("MachineHasComponent", "Component", "HAS_COMPONENT", "component_id", "machine_id", "Machine", "component_id", "Component"),
    ("MachineHasSensor", "Sensor", "HAS_SENSOR", "sensor_id", "machine_id", "Machine", "sensor_id", "Sensor"),
    ("SensorHasTag", "Tag", "HAS_TAG", "tag_id", "sensor_id", "Sensor", "tag_id", "Tag"),
    ("SensorHasObservation", "ObservationWindow", "HAS_OBSERVATION", "obs_id", "sensor_id", "Sensor", "obs_id", "ObservationWindow"),
    ("SensorHasAlarm", "Alarm", "HAS_ALARM", "alarm_id", "sensor_id", "Sensor", "alarm_id", "Alarm"),
    ("SensorHasAnomaly", "Anomaly", "HAS_ANOMALY", "anomaly_id", "sensor_id", "Sensor", "anomaly_id", "Anomaly"),
    ("WorkOrderOnMachine", "WorkOrder", "RAN_ON", "work_order_id", "work_order_id", "WorkOrder", "machine_id", "Machine"),
    ("WorkOrderLot", "WorkOrder", "CONSUMED_LOT", "work_order_id", "work_order_id", "WorkOrder", "lot_id", "MaterialLot"),
    ("WorkOrderShift", "WorkOrder", "IN_SHIFT", "work_order_id", "work_order_id", "WorkOrder", "shift_id", "Shift"),
    ("WorkOrderOperator", "WorkOrder", "OPERATED_BY", "work_order_id", "work_order_id", "WorkOrder", "operator_id", "Employee"),
    ("WorkOrderBatch", "Batch", "PRODUCED_BATCH", "batch_id", "work_order_id", "WorkOrder", "batch_id", "Batch"),
    ("WorkOrderInspection", "Inspection", "HAS_INSPECTION", "inspection_id", "work_order_id", "WorkOrder", "inspection_id", "Inspection"),
    ("ShiftCrew", "Shift", "SHIFT_CREW", "shift_id", "shift_id", "Shift", "crew_id", "Crew"),
    ("HandoverToCrew", "Handover", "HANDOVER_TO", "handover_id", "handover_id", "Handover", "to_crew_id", "Crew"),
    ("HandoverFromCrew", "Handover", "HANDOVER_FROM", "handover_id", "handover_id", "Handover", "from_crew_id", "Crew"),
    ("CalibrationOnMachine", "Calibration", "CALIBRATED", "calibration_id", "calibration_id", "Calibration", "machine_id", "Machine"),
    ("CalibrationOrder", "Calibration", "CALIBRATION_ORDER", "calibration_id", "calibration_id", "Calibration", "order_id", "MaintenanceOrder"),
    ("CalibrationHandover", "Calibration", "DURING_HANDOVER", "calibration_id", "calibration_id", "Calibration", "handover_id", "Handover"),
    ("OrderTechnician", "MaintenanceOrder", "PERFORMED_BY_TECH", "order_id", "order_id", "MaintenanceOrder", "technician_id", "Employee"),
    ("EmployeeTraining", "TrainingRecord", "HAS_TRAINING", "training_id", "employee_id", "Employee", "training_id", "TrainingRecord"),
    ("LotCertificate", "MillCertificate", "HAS_CERT", "mill_cert_id", "lot_id", "MaterialLot", "mill_cert_id", "MillCertificate"),
    ("CertIssuer", "MillCertificate", "ISSUED_BY", "mill_cert_id", "mill_cert_id", "MillCertificate", "issued_by_supplier_id", "Supplier"),
    ("IncidentAction", "Action", "HAS_ACTION", "action_id", "incident_id", "Incident", "action_id", "Action"),
]


def parse_cols(spec, pk):
    pks, out = pk.split(), []
    for tok in spec.split():
        code = "s"
        if ":" in tok:
            tok, code = tok.split(":")
        src, db = (tok.split(">") + [tok])[:2] if ">" in tok else (tok, tok)
        if code == "s" and (db in pks or db.endswith("_id")):
            code = "k"
        out.append((src, db, code))
    return out


TABLES = {}   # table -> dict(csv, cols, pk, kind)
for t, c, cols, pk in NODES:
    TABLES[t] = {"csv": c, "cols": parse_cols(cols, pk), "pk": pk.split(), "kind": "node"}
for t, c, cols, pk, *_ in OWN_EDGES:
    TABLES[t] = {"csv": c, "cols": parse_cols(cols, pk), "pk": pk.split(), "kind": "edge"}


def table_ddl():
    stmts = []
    for t, d in TABLES.items():
        lines = []
        for _, db, code in d["cols"]:
            lines.append(f"  {db} {TYPES[code]}" + (" NOT NULL" if db in d["pk"] else ""))
        stmts.append(f"CREATE TABLE {t} (\n" + ",\n".join(lines) + f"\n) PRIMARY KEY ({', '.join(d['pk'])})")
    return stmts


def graph_ddl(no_alias_props=True):
    nodes = ",\n    ".join(t for t, *_ in NODES)
    edges = []
    for t, _c, _cols, _pk, label, sc, st, dc, dt in OWN_EDGES:
        edges.append(f"    {t}\n      SOURCE KEY ({sc}) REFERENCES {st} ({sc})\n      DESTINATION KEY ({dc}) REFERENCES {dt} ({dc})\n      LABEL {label}")
    for alias, t, label, key, sc, st, dc, dt in ALIAS_EDGES:
        edges.append(f"    {t} AS {alias}\n      KEY ({key})\n      SOURCE KEY ({sc}) REFERENCES {st} ({sc})\n"
                     f"      DESTINATION KEY ({dc}) REFERENCES {dt} ({dc})\n      LABEL {label}" + (" NO PROPERTIES" if no_alias_props else ""))
    return (f"CREATE OR REPLACE PROPERTY GRAPH {GRAPH}\n  NODE TABLES (\n    {nodes}\n  )\n  EDGE TABLES (\n"
            + ",\n".join(edges) + "\n  )")


DEFAULTS = {"incident": "INC-2026-1015-001", "lot": "LOT-409",
            "since": datetime(2026, 10, 14, tzinfo=timezone.utc)}
QUERIES = {
    "common_lots": ("Lots currently in use on the incident's machines. Expect LOT-409 with machines = 5.",
                    f"GRAPH {GRAPH}\nMATCH (i:Incident {{incident_id: @incident}})-[:AFFECTS]->(m:Machine)-[p:PROCESSED]->(l:MaterialLot)\n"
                    "WHERE p.last_used >= @since\nRETURN l.lot_id AS lot_id, COUNT(DISTINCT m.machine_id) AS machines\nORDER BY machines DESC"),
    "common_crews": ("Crews that calibrated the incident's machines since @since. Expect CREW-B with machines = 5.",
                     f"GRAPH {GRAPH}\nMATCH (i:Incident {{incident_id: @incident}})-[:AFFECTS]->(m:Machine)<-[:CALIBRATED]-(c:Calibration)"
                     "-[:CALIBRATION_ORDER]->(o:MaintenanceOrder)-[:PERFORMED_BY]->(cr:Crew)\nWHERE c.started_at >= @since\n"
                     "RETURN cr.crew_id AS crew_id, COUNT(DISTINCT m.machine_id) AS machines, MIN(c.steps_completed) AS min_steps\nORDER BY machines DESC"),
    "cause_intersection": ("Machines on the lot AND calibrated with a skipped step. Expect exactly M02, M03, M06, M09, M11.",
                           f"GRAPH {GRAPH}\nMATCH (m:Machine)-[:PROCESSED]->(l:MaterialLot {{lot_id: @lot}}),\n      (c:Calibration)-[:CALIBRATED]->(m)\n"
                           "WHERE c.started_at >= @since AND c.steps_completed < c.steps_required\n"
                           "RETURN m.machine_id AS machine_id, m.line_id AS line_id, c.calibration_id AS calibration_id, c.skipped_step AS skipped_step\nORDER BY machine_id"),
    "blast_radius": ("Every machine that processed the lot. Expect 8 machines across L1, L2, L3.",
                     f"GRAPH {GRAPH}\nMATCH (m:Machine)-[p:PROCESSED]->(l:MaterialLot {{lot_id: @lot}})\n"
                     "RETURN m.machine_id AS machine_id, m.line_id AS line_id, p.first_used AS first_used, p.units AS units\nORDER BY machine_id"),
    "supplier_chain": ("Origin (Tier 3) supplier of the lot and everything downstream. Expect SUP-T3-01 -> SUP-T2-01 -> SUP-T1-01.",
                       f"GRAPH {GRAPH}\nMATCH (l:MaterialLot {{lot_id: @lot}})-[r:SUPPLIED_BY]->(t3:Supplier)-[:SUPPLIES]->{{1,2}}(s:Supplier)\n"
                       "WHERE r.relation = 'ORIGIN'\nRETURN t3.supplier_id AS origin, s.supplier_id AS downstream, s.tier AS tier\nORDER BY tier DESC"),
}


def conv(v, code):
    if v == "":
        return None
    if code == "i":
        return int(v)
    if code == "f":
        return float(v)
    if code == "b":
        return v.strip().lower() == "true"
    if code == "t":
        return datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return v


def read_table(data_dir, t):
    d = TABLES[t]
    if not d["csv"]:
        return []
    path = os.path.join(data_dir, d["csv"] + ".csv")
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        missing = [s for s, _, _ in d["cols"] if s not in (r.fieldnames or [])]
        extra = [h for h in (r.fieldnames or []) if h not in [s for s, _, _ in d["cols"]]]
        if missing or extra:
            raise SystemExit(f"{t}: CSV header mismatch. missing={missing} extra={extra}")
        return [{db: conv(row[s], code) for s, db, code in d["cols"]} for row in r]


def cmd_ddl(a):
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "schema_tables.sql"), "w") as f:
        f.write(";\n\n".join(table_ddl()) + ";\n")
    with open(os.path.join(a.out, "schema_graph.sql"), "w") as f:
        f.write(graph_ddl(not a.keep_edge_props) + ";\n")
    with open(os.path.join(a.out, "queries.gql"), "w") as f:
        for n, (doc, q) in QUERIES.items():
            f.write(f"-- {n}: {doc}\n-- params: " + ", ".join(sorted(set(re.findall(r"@(\w+)", q)))) + f"\n{q};\n\n")
    print("wrote schema_tables.sql, schema_graph.sql, queries.gql to", a.out)


def cmd_check(a):
    data, bad = {}, 0
    for t in TABLES:
        data[t] = read_table(a.data_dir, t)
        pks = [tuple(r[c] for c in TABLES[t]["pk"]) for r in data[t]]
        if len(set(pks)) != len(pks):
            print(f"  DUPLICATE PRIMARY KEYS in {t}"); bad += 1
        if any(x is None for p in pks for x in p):
            print(f"  NULL primary key part in {t}"); bad += 1
    ids = {t: {r[TABLES[t]["pk"][0]] for r in rows} for t, rows in data.items() if TABLES[t]["kind"] == "node"}
    links = [(t, sc, st, dc, dt) for t, _c, _cols, _pk, _l, sc, st, dc, dt in OWN_EDGES] + \
            [(t, sc, st, dc, dt) for _al, t, _l, _k, sc, st, dc, dt in ALIAS_EDGES]
    for t, sc, st, dc, dt in links:
        for col, tgt in ((sc, st), (dc, dt)):
            missing = [r[col] for r in data[t] if r[col] is not None and r[col] not in ids[tgt]]
            nulls = sum(1 for r in data[t] if r[col] is None)
            if missing or nulls:
                bad += 1
                print(f"  {t}.{col} -> {tgt}: {len(missing)} dangling, {nulls} null (e.g. {missing[:3]})")
    print("rows:", {t: len(r) for t, r in data.items() if r})
    print("CHECK", "FAILED" if bad else "PASSED", f"({bad} problem groups)")
    return 1 if bad else 0


def get_db(a, create=False):
    from google.cloud import spanner
    c = spanner.Client(project=a.project)
    return c.instance(a.instance).database(a.database)


def cmd_create(a):
    db = get_db(a)
    if db.exists():
        print("database exists; skipping table creation (drop it to recreate)")
    else:
        from google.cloud import spanner
        db = spanner.Client(project=a.project).instance(a.instance).database(a.database, ddl_statements=table_ddl())
        db.create().result(600)
        print("created database and tables")
    try:
        db.update_ddl([graph_ddl(not a.keep_edge_props)]).result(600)
        print("created property graph", GRAPH)
    except Exception as e:
        print("GRAPH DDL FAILED:", e)
        print("Tables are created. Fix schema_graph.sql (try --keep-edge-props if NO PROPERTIES is rejected) and re-run create.")
        return 1


def cmd_load(a):
    db = get_db(a)
    for t, d in TABLES.items():
        rows = read_table(a.data_dir, t)
        if not rows:
            continue
        cols = [db_ for _, db_, _ in d["cols"]]
        chunk = max(1, 20000 // len(cols))   # keep each commit well under the 80k-mutation limit
        for i in range(0, len(rows), chunk):
            part = rows[i:i + chunk]
            with db.batch() as b:
                b.insert_or_update(table=t, columns=cols, values=[[r[c] for c in cols] for r in part])
        print(f"loaded {t}: {len(rows)} rows")


def run_query(db, gql):
    from google.cloud.spanner_v1 import param_types as pt
    names = sorted(set(re.findall(r"@(\w+)", gql)))
    types = {n: (pt.TIMESTAMP if n == "since" else pt.STRING) for n in names}
    with db.snapshot() as s:
        return [list(r) for r in s.execute_sql(gql, params={n: DEFAULTS[n] for n in names}, param_types=types)]


def cmd_verify(a):
    db = get_db(a)
    gt = json.load(open(a.ground_truth)) if a.ground_truth and os.path.exists(a.ground_truth) else None
    res, ok = {}, True
    for n, (doc, q) in QUERIES.items():
        try:
            res[n] = run_query(db, q)
            print(f"\n{n}: {len(res[n])} rows\n  {doc}")
            for r in res[n][:8]:
                print("  ", r)
        except Exception as e:
            ok = False
            print(f"\n{n}: ERROR {e}")
    if gt and res:
        checks = [("cause_intersection", {r[0] for r in res.get("cause_intersection", [])}, set(gt["affected_machines"])),
                  ("blast_radius", {r[0] for r in res.get("blast_radius", [])}, set(gt["blast_radius"]["machines_on_lot_409"])),
                  ("common_lots top", {res["common_lots"][0][0]} if res.get("common_lots") else set(), {"LOT-409"}),
                  ("common_crews top", {res["common_crews"][0][0]} if res.get("common_crews") else set(), {"CREW-B"})]
        for name, got, want in checks:
            good = got == want
            ok &= good
            print(f"{'PASS' if good else 'FAIL'}  {name}: got {sorted(got)} want {sorted(want)}")
    return 0 if ok else 1


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["ddl", "check", "create", "load", "verify"])
    p.add_argument("--project", default=os.getenv("SPANNER_PROJECT"))
    p.add_argument("--instance", default=os.getenv("SPANNER_INSTANCE"))
    p.add_argument("--database", default=os.getenv("SPANNER_DATABASE"))
    p.add_argument("--data-dir", default="data")
    p.add_argument("--out", default=".")
    p.add_argument("--ground-truth", default="ground_truth.json")
    p.add_argument("--keep-edge-props", action="store_true", help="omit NO PROPERTIES on foreign-key edges")
    a = p.parse_args()
    if a.cmd in ("create", "load", "verify") and not (a.project and a.instance and a.database):
        sys.exit("need --project --instance --database (or SPANNER_* env vars)")
    sys.exit({"ddl": cmd_ddl, "check": cmd_check, "create": cmd_create, "load": cmd_load, "verify": cmd_verify}[a.cmd](a) or 0)


if __name__ == "__main__":
    main()
