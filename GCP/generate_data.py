#!/usr/bin/env python3
"""Deterministic synthetic data for the manufacturing RCA knowledge graph.

Outputs (under --out/data): one CSV per node class, edges_*.csv per relationship,
and --out/ground_truth.json describing the planted scenario.
All timestamps are UTC ISO-8601 (simplified: plant local time == UTC).
Pure standard library. Same seed -> identical output.
"""
import argparse, csv, json, math, os, random
from datetime import datetime, timedelta, date

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="rca_sim")
ap.add_argument("--seed", type=int, default=42)
args = ap.parse_args()
rng = random.Random(args.seed)
DATA = os.path.join(args.out, "data")
os.makedirs(DATA, exist_ok=True)
FILES = {}


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def write(name, fields, rows):
    with open(os.path.join(DATA, name + ".csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (iso(v) if isinstance(v, datetime) else v) for k, v in r.items()})
    FILES[name] = len(rows)


def H(n):
    return timedelta(hours=n)


def M(n):
    return timedelta(minutes=n)


# ------------------------------------------------------------------ timeline
START = datetime(2026, 9, 17, 6)
END = datetime(2026, 10, 15, 7)          # data cut-off
CAL_T = datetime(2026, 10, 14, 14)       # rushed handover (SWING shift start)
DETECT = datetime(2026, 10, 15, 7, 15)   # incident detected
SHIFT_NAMES = {6: "DAY", 14: "SWING", 22: "NIGHT"}

# ------------------------------------------------------------------ assets
site = [{"site_id": "SITE-PUN", "name": "Vantage Motors Powertrain Plant", "city": "Pune", "country": "IN"}]
areas = [{"area_id": "AR-MACH", "site_id": "SITE-PUN", "name": "Machining Hall"},
         {"area_id": "AR-GRIND", "site_id": "SITE-PUN", "name": "Grinding Hall"}]
LINEDEF = [("L1", "Housing Machining", "AR-MACH", "GH-118"),
           ("L2", "Shaft Turning", "AR-MACH", "OS-210"),
           ("L3", "Ring Gear Grinding", "AR-GRIND", "GR-330")]
lines = [{"line_id": a, "name": b, "area_id": c, "product_code": d} for a, b, c, d in LINEDEF]
MTYPE = {"L1": "5-axis CNC mill", "L2": "CNC turning center", "L3": "Gear grinder"}
RATE = {"L1": 150, "L2": 190, "L3": 130}   # units per machine per 8h shift
PRODUCT = {"L1": "GH-118", "L2": "OS-210", "L3": "GR-330"}
machines = []
for i in range(1, 13):
    ln = f"L{(i - 1) // 4 + 1}"
    machines.append({"machine_id": f"M{i:02d}", "line_id": ln, "name": f"{MTYPE[ln]} {i:02d}",
                     "machine_type": MTYPE[ln], "install_year": rng.choice([2018, 2019, 2021, 2022])})
MID = [m["machine_id"] for m in machines]
LINE_OF = {m["machine_id"]: m["line_id"] for m in machines}
TYPE_OF = {m["machine_id"]: m["machine_type"] for m in machines}

components, sensors, tags = [], [], []
for idx, m in enumerate(MID, 1):
    cmp = {"SPN": "Spindle", "CPM": "Coolant pump", "FIX": "Clamp fixture"}
    for k, nm in cmp.items():
        components.append({"component_id": f"CMP-{m}-{k}", "machine_id": m, "name": nm})
    for kind, unit, cmpk, base_tag, hz in (("TEMP", "degC", "SPN", 400, 10), ("VIB", "mm/s", "SPN", 500, 1000),
                                           ("PRES", "bar", "CPM", 600, 10)):
        sid = f"SN-{m}-{kind}"
        sensors.append({"sensor_id": sid, "machine_id": m, "component_id": f"CMP-{m}-{cmpk}",
                        "sensor_type": kind, "unit": unit, "sampling_hz": hz})
        tags.append({"tag_id": f"TAG-{m}-{kind}", "tag_name": f"TAG_{kind}_{base_tag + idx}", "sensor_id": sid,
                     "protocol": "OPCUA", "node_id": f"ns=2;s={LINE_OF[m]}.{m}.{kind.title()}"})

# scenario roles ------------------------------------------------------------
AFFECTED = ["M02", "M03", "M06", "M09", "M11"]      # LOT-409 + rushed calibration -> scrap
LOT409_ONLY = ["M04", "M07", "M10"]                  # LOT-409, calibrated properly -> fine
CALIB_ONLY = ["M01", "M08"]                          # rushed calibration, other lots -> fine
NEITHER = ["M05", "M12"]
LOT409_MACHINES = AFFECTED + LOT409_ONLY
MISCAL = AFFECTED + CALIB_ONLY

# ------------------------------------------------------------------ people
CREWS = ["CREW-A", "CREW-B", "CREW-C"]
people, TECH, OPS = [], {}, {}
for c in CREWS:
    L = c[-1]
    TECH[c], OPS[c] = [], []
    for n in range(1, 7):
        role = "OPERATOR" if n <= 4 else "TECHNICIAN"
        eid = f"EMP-{L}{n}"
        people.append({"employee_id": eid, "name": f"{role.title()} {L}{n}", "role": role, "crew_id": c})
        (OPS if role == "OPERATOR" else TECH)[c].append(eid)
for n, role in enumerate(["QUALITY_ENGINEER", "RELIABILITY_ENGINEER", "QUALITY_ENGINEER"], 1):
    people.append({"employee_id": f"EMP-E{n}", "name": f"Engineer E{n}", "role": role, "crew_id": ""})
crews = [{"crew_id": c, "name": f"Crew {c[-1]}"} for c in CREWS]
training = []
for p in people:
    if p["role"] != "OPERATOR":
        continue
    for t in MTYPE.values():
        exp, st = datetime(2027, 6, 30), "VALID"
        if (p["employee_id"], t) in (("EMP-C2", "CNC turning center"), ("EMP-B3", "Gear grinder")):
            exp, st = datetime(2026, 9, 30), "EXPIRED"       # red herring
        training.append({"training_id": f"TR-{p['employee_id']}-{t[:3].upper()}", "employee_id": p["employee_id"],
                         "machine_type": t, "issued": datetime(2025, 7, 1), "expires": exp, "status": st})

# ------------------------------------------------------------------ shifts & handovers
shifts, s = [], START
while s < END:
    d = (s.date() - date(2026, 9, 17)).days
    crew = CREWS[(d + {6: 0, 14: 1, 22: 2}[s.hour]) % 3]
    nm = SHIFT_NAMES[s.hour]
    shifts.append({"shift_id": f"SH-{s:%Y%m%d}-{nm[0]}", "shift_name": nm, "start": s, "end": s + H(8),
                   "crew_id": crew, "status": "COMPLETE" if s + H(8) <= END else "IN_PROGRESS"})
    s += H(8)
DECOY_SHORT = {datetime(2026, 9, 28, 14), datetime(2026, 10, 3, 22)}
handovers = []
for i in range(1, len(shifts)):
    prev, cur = shifts[i - 1], shifts[i]
    hid = f"HO-{cur['start']:%Y%m%d}-{cur['shift_name'][0]}"
    dur, ok, rushed, note = rng.randint(25, 40), True, False, "Normal handover"
    if cur["start"] == CAL_T:
        dur, ok, rushed = 6, False, True
        note = "Line stoppage overran; incoming crew asked to complete PM calibrations; checklist not completed"
    elif cur["start"] in DECOY_SHORT:
        dur, ok, rushed, note = 9, False, True, "Short handover, no maintenance work followed"
    handovers.append({"handover_id": hid, "from_shift_id": prev["shift_id"], "to_shift_id": cur["shift_id"],
                      "from_crew_id": prev["crew_id"], "to_crew_id": cur["crew_id"], "handover_time": cur["start"],
                      "duration_min": dur, "checklist_complete": ok, "rushed": rushed, "notes": note})
HO_BY_START = {h["handover_time"]: h["handover_id"] for h in handovers}
shift_crew = {sh["start"]: sh["crew_id"] for sh in shifts}


def shift_start_of(dt):
    b = dt.replace(minute=0, second=0, microsecond=0)
    if b.hour >= 22:
        return b.replace(hour=22)
    if b.hour >= 14:
        return b.replace(hour=14)
    if b.hour >= 6:
        return b.replace(hour=6)
    return (b - timedelta(days=1)).replace(hour=22)


def next_shift(crew, after):
    return next(sh["start"] for sh in shifts if sh["start"] >= after and sh["crew_id"] == crew)


# ------------------------------------------------------------------ maintenance & calibration events
STEPS = ["Zero reference", "Axis geometry", "Spindle runout", "Tool length offset", "Coolant flow check",
         "Thermal offset verification", "Probe calibration", "Test-cut sign-off"]
SKIPPED = "Step 6: Thermal offset verification"
events = []   # dicts


def cal(machine, start, dur, steps, hs, plan):
    events.append({"kind": "CALIBRATION", "machine": machine, "start": start, "end": start + M(dur), "dur": dur,
                   "crew": shift_crew[shift_start_of(start)], "steps": steps, "hs": hs, "plan": plan})


for i, m in enumerate(["M04", "M05", "M07", "M10", "M12"]):          # Crew A, morning, full checklist
    cal(m, datetime(2026, 10, 14, 8) + M(95 * (i // 2)), 90, 8, datetime(2026, 10, 14, 6), "PM-CAL")
B_ORDER = ["M01", "M02", "M03", "M06", "M08", "M09", "M11"]           # Crew B, after rushed handover
for i, m in enumerate(B_ORDER):
    cal(m, CAL_T + M(10 + 38 * (i // 2) + 2 * (i % 2)), 35, 7, CAL_T, "PM-CAL")
for m, crew, after in (("M05", "CREW-B", datetime(2026, 9, 24)), ("M12", "CREW-B", datetime(2026, 10, 2)),
                       ("M04", "CREW-B", datetime(2026, 10, 6)), ("M03", "CREW-A", datetime(2026, 9, 22)),
                       ("M02", "CREW-A", datetime(2026, 9, 25)), ("M09", "CREW-C", datetime(2026, 9, 30)),
                       ("M11", "CREW-C", datetime(2026, 10, 8))):      # earlier proper ad-hoc calibrations
    hs = next_shift(crew, after)
    cal(m, hs + M(90), 90, 8, hs, "")
for _ in range(8):                                                     # corrective noise
    hs = rng.choice(shifts[:-8])["start"]
    t = hs + M(rng.randint(30, 200))
    d = rng.randint(20, 60)
    events.append({"kind": rng.choice(["LUBRICATION", "FILTER_REPLACE", "BELT_ADJUST", "COOLANT_TOP_UP"]),
                   "machine": rng.choice(MID), "start": t, "end": t + M(d), "dur": d, "crew": shift_crew[hs],
                   "steps": 0, "hs": hs, "plan": ""})
events.sort(key=lambda e: (e["start"], e["machine"]))
maint, calibs, maint_on, maint_by = [], [], [], []
cal_end_oct14 = {}
for n, e in enumerate(events, 1):
    oid = f"MO-{n:04d}"
    e["order_id"] = oid
    tech = rng.choice(TECH[e["crew"]])
    maint.append({"order_id": oid, "machine_id": e["machine"], "order_type": e["kind"], "plan_id": e["plan"],
                  "crew_id": e["crew"], "technician_id": tech, "scheduled_start": e["start"],
                  "actual_start": e["start"], "actual_end": e["end"], "status": "COMPLETE",
                  "spare_part_id": rng.choice(["SP-001", "SP-002", "SP-003"]) if e["kind"] in ("FILTER_REPLACE", "BELT_ADJUST") else ""})
    maint_on.append({"order_id": oid, "machine_id": e["machine"]})
    maint_by.append({"order_id": oid, "crew_id": e["crew"]})
    if e["kind"] == "CALIBRATION":
        full = e["steps"] == 8
        calibs.append({"calibration_id": f"CAL-{n:04d}", "order_id": oid, "machine_id": e["machine"],
                       "started_at": e["start"], "ended_at": e["end"], "steps_required": 8,
                       "steps_completed": e["steps"], "skipped_step": "" if full else SKIPPED,
                       "duration_min": e["dur"], "handover_id": HO_BY_START.get(e["hs"], ""),
                       "recorded_result": "PASS", "verification_signed_off": full})
        if e["start"] >= datetime(2026, 10, 14):
            cal_end_oct14[e["machine"]] = e["end"]
downtime = {m: [(e["start"], e["end"]) for e in events if e["machine"] == m] for m in MID}
pm_plans = [{"plan_id": "PM-CAL", "name": "Machine calibration", "interval_days": 28},
            {"plan_id": "PM-LUBE", "name": "Lubrication", "interval_days": 7},
            {"plan_id": "PM-FILTER", "name": "Filter replacement", "interval_days": 14}]
spares = [{"spare_part_id": f"SP-00{i}", "name": n, "stock_qty": q} for i, (n, q) in
          enumerate([("Coolant filter", 14), ("Drive belt", 6), ("Spindle seal kit", 3), ("Grinding wheel", 5),
                     ("Probe stylus", 9), ("Pressure transducer", 2)], 1)]

# ------------------------------------------------------------------ supply chain
suppliers = [
    {"supplier_id": "SUP-T3-01", "name": "Meridian Specialty Steels", "tier": 3, "iatf_certified": False, "shares_batch_data": False},
    {"supplier_id": "SUP-T3-02", "name": "Orion Alloys", "tier": 3, "iatf_certified": False, "shares_batch_data": True},
    {"supplier_id": "SUP-T3-03", "name": "Kestrel Metals", "tier": 3, "iatf_certified": False, "shares_batch_data": True},
    {"supplier_id": "SUP-T2-01", "name": "Northgate Forgings", "tier": 2, "iatf_certified": True, "shares_batch_data": True},
    {"supplier_id": "SUP-T2-02", "name": "Vista Machining", "tier": 2, "iatf_certified": True, "shares_batch_data": True},
    {"supplier_id": "SUP-T1-01", "name": "Apex Drivetrain Systems", "tier": 1, "iatf_certified": True, "shares_batch_data": True},
    {"supplier_id": "SUP-T1-02", "name": "Helix Powertrain", "tier": 1, "iatf_certified": True, "shares_batch_data": True}]
supplies = [{"supplier_id": a, "buyer_supplier_id": b, "material_id": "MAT-20MNCR5"} for a, b in
            (("SUP-T3-01", "SUP-T2-01"), ("SUP-T3-02", "SUP-T2-01"), ("SUP-T3-02", "SUP-T2-02"),
             ("SUP-T3-03", "SUP-T2-02"), ("SUP-T2-01", "SUP-T1-01"), ("SUP-T2-02", "SUP-T1-02"))]
materials = [{"material_id": "MAT-20MNCR5", "name": "20MnCr5 alloy steel bar stock", "spec_hardness_hrc": "28-32",
              "spec_carbon_pct": "0.17-0.23", "spec_mn_pct": "0.90-1.40"}]
products = [{"product_code": c, "name": n, "line_id": l} for c, n, l in
            (("GH-118", "Gear housing", "L1"), ("OS-210", "Output shaft", "L2"), ("GR-330", "Ring gear", "L3"))]
bom = [{"bom_id": f"BOM-{p}", "product_code": p, "material_id": "MAT-20MNCR5", "kg_per_unit": q}
       for p, q in (("GH-118", 7.5), ("OS-210", 4.2), ("GR-330", 3.1))]
LOTS = {  # tier1, tier2, tier3, received, heat, hardness, carbon, mn
    "LOT-377": ("SUP-T1-02", "SUP-T2-02", "SUP-T3-03", datetime(2026, 9, 8), "H-77231", 29.6, 0.201, 1.12),
    "LOT-388": ("SUP-T1-02", "SUP-T2-02", "SUP-T3-02", datetime(2026, 9, 10), "H-88104", 29.9, 0.198, 1.10),
    "LOT-392": ("SUP-T1-01", "SUP-T2-01", "SUP-T3-02", datetime(2026, 9, 12), "H-92377", 30.2, 0.205, 1.15),
    "LOT-401": ("SUP-T1-02", "SUP-T2-02", "SUP-T3-03", datetime(2026, 9, 15), "H-01455", 29.4, 0.196, 1.09),
    "LOT-403": ("SUP-T1-01", "SUP-T2-01", "SUP-T3-02", datetime(2026, 10, 1), "H-03012", 30.0, 0.202, 1.13),
    "LOT-409": ("SUP-T1-01", "SUP-T2-01", "SUP-T3-01", datetime(2026, 10, 6), "H-09918", 31.7, 0.219, 1.31),
    "LOT-412": ("SUP-T1-01", "SUP-T2-01", "SUP-T3-01", datetime(2026, 10, 2), "H-12040", 29.8, 0.200, 1.12),
    "LOT-415": ("SUP-T1-02", "SUP-T2-02", "SUP-T3-03", datetime(2026, 10, 3), "H-15266", 29.7, 0.199, 1.11)}
lots, certs, pos, lot_sup = [], [], [], []
for n, (lid, (t1, t2, t3, rec, heat, hv, c, mn)) in enumerate(LOTS.items()):
    lots.append({"lot_id": lid, "material_id": "MAT-20MNCR5", "qty_kg": 12000, "received_at": rec,
                 "po_id": f"PO-{4500 + n}", "mill_cert_id": f"MC-{lid[4:]}", "status": "IN_USE"})
    certs.append({"mill_cert_id": f"MC-{lid[4:]}", "lot_id": lid, "heat_number": heat, "issued_by_supplier_id": t3,
                  "hardness_hrc": hv, "carbon_pct": c, "manganese_pct": mn, "within_spec": True,
                  "edge_flag": "UPPER_EDGE_ALL" if lid == "LOT-409" else "", "document_ref": f"certs/MC-{lid[4:]}.pdf"})
    pos.append({"po_id": f"PO-{4500 + n}", "supplier_id": t1, "material_id": "MAT-20MNCR5", "qty_kg": 12000,
                "ordered_at": rec - timedelta(days=9), "received_at": rec})
    lot_sup += [{"lot_id": lid, "supplier_id": t1, "relation": "DIRECT"},
                {"lot_id": lid, "supplier_id": t3, "relation": "ORIGIN"}]
ROT = ["LOT-377", "LOT-388", "LOT-392", "LOT-401"]
L409_FIRST = {m: datetime(2026, 10, 9, 6) + H(8 * (i % 3)) for i, m in enumerate(LOT409_MACHINES)}
LATE = {"M01": "LOT-412", "M08": "LOT-403", "M05": "LOT-415", "M12": "LOT-415"}
LATE_T = datetime(2026, 10, 5)


def lot_for(m, t):
    if m in L409_FIRST and t >= L409_FIRST[m]:
        return "LOT-409"
    if m in LATE and t >= LATE_T:
        return LATE[m]
    return ROT[(MID.index(m) + (t - START).days // 7) % 4]


# ------------------------------------------------------------------ production
BASE_SCRAP = 0.02
wos, batches, insp = [], [], []
for sh in shifts:
    if sh["status"] != "COMPLETE":
        continue
    for m in MID:
        ln = LINE_OF[m]
        lot = lot_for(m, sh["start"])
        down = sum(max(0, (min(b, sh["end"]) - max(a, sh["start"])).total_seconds() / 60) for a, b in downtime[m])
        n = int(RATE[ln] * (1 - down / 480) * rng.uniform(0.97, 1.03))
        rate = max(0.0, rng.gauss(BASE_SCRAP, 0.006))
        overlap = 0.0
        if m in AFFECTED and lot == "LOT-409" and m in cal_end_oct14:
            overlap = max(0.0, (sh["end"] - max(sh["start"], cal_end_oct14[m])).total_seconds() / 28800)
            rate = max(0.0, rate + 0.12 * overlap + rng.gauss(0, 0.012) * overlap)
        scrap = int(round(n * rate))
        rework = int(round(n * rng.uniform(0.01, 0.02)))
        suffix = f"{sh['start']:%Y%m%d}-{sh['shift_name'][0]}-{m}"
        age = END - sh["end"]
        status = "SHIPPED" if age > timedelta(hours=72) else ("FINISHED" if age > timedelta(hours=12) else "WIP")
        wid, bid = f"WO-{suffix}", f"B-{suffix}"
        wos.append({"work_order_id": wid, "machine_id": m, "line_id": ln, "shift_id": sh["shift_id"],
                    "operator_id": rng.choice(OPS[sh["crew_id"]]), "product_code": PRODUCT[ln], "lot_id": lot,
                    "batch_id": bid, "planned_start": sh["start"], "planned_end": sh["end"], "units_planned": RATE[ln],
                    "units_produced": n, "units_good": n - scrap - rework, "units_scrap": scrap, "units_rework": rework,
                    "scrap_rate": round(scrap / n, 4) if n else 0, "status": "COMPLETE", "_overlap": overlap,
                    "_start": sh["start"]})
        batches.append({"batch_id": bid, "work_order_id": wid, "product_code": PRODUCT[ln], "lot_id": lot,
                        "qty": n, "status": status, "machine_id": m})
        hi = rate > 0.06
        dc = rng.choices(["DC-205", "DC-101"], [7, 3])[0] if hi else rng.choice(["DC-402", "DC-101"])
        insp.append({"inspection_id": f"INS-{suffix}", "work_order_id": wid, "machine_id": m, "inspected_units": n,
                     "scrap_units": scrap, "rework_units": rework, "dominant_defect_code": dc,
                     "first_pass_yield": round((n - scrap - rework) / n, 4) if n else 0})
defect_codes = [{"defect_code": a, "description": b} for a, b in
                (("DC-101", "Bore dimension out of tolerance"), ("DC-205", "Surface micro-fracture"),
                 ("DC-310", "Hardness out of range"), ("DC-402", "Burr / surface finish"))]
recipe = [{"recipe_step_id": f"RS-{l}-{q}", "line_id": l, "seq": q, "name": nm, "temp_setpoint_c": 62}
          for l in ("L1", "L2", "L3") for q, nm in enumerate(("Rough", "Semi-finish", "Finish"), 1)]
processed = {}
for w in wos:
    k = (w["machine_id"], w["lot_id"])
    e = processed.setdefault(k, {"machine_id": k[0], "lot_id": k[1], "first_used": w["planned_start"],
                                 "last_used": w["planned_end"], "work_orders": 0, "units": 0})
    e["last_used"], e["work_orders"], e["units"] = w["planned_end"], e["work_orders"] + 1, e["units"] + w["units_produced"]

# ------------------------------------------------------------------ telemetry
obs, series = [], {}
TOTAL_H = int((END - START).total_seconds() // 3600)
for idx, m in enumerate(MID, 1):
    for kind in ("TEMP", "VIB", "PRES"):
        sid = f"SN-{m}-{kind}"
        series[sid] = []
        for h in range(TOTAL_H):
            t = START + H(h)
            if kind == "TEMP":
                exp = 61.0 + (idx % 4) * 0.5 + 1.5 * math.sin(2 * math.pi * (t.hour + 0.5 - 8) / 24)
                off = 0.0
                if m in MISCAL:
                    off = 2.8 * min(1.0, max(0.0, ((t + H(1)) - cal_end_oct14[m]).total_seconds() / 3600))
                mean, sd, thr, tol = exp + off + rng.gauss(0, 0.25), rng.uniform(0.3, 0.5), 66.0, 0.9
                mx = mean + 0.9
            elif kind == "VIB":
                exp = 2.1 + idx * 0.02
                drift = 0.35 * max(0.0, (t - datetime(2026, 10, 11)).total_seconds() / 86400) if m == "M05" else 0.0
                mean, sd, thr, tol = exp + drift + rng.gauss(0, 0.08), rng.uniform(0.05, 0.1), 3.0, 0.5
                mx = mean + 0.2
            else:
                exp = 6.0
                spur = m == "M12" and datetime(2026, 10, 8, 2) <= t <= datetime(2026, 10, 8, 4)
                mean, sd, thr, tol = (8.4 if spur else exp + rng.gauss(0, 0.05)), 0.05, 7.5, 1.0
                mx = mean + 0.1
            resid = mean - exp
            series[sid].append((t, mean, mx, abs(resid) > tol, resid, thr, kind))
            obs.append({"obs_id": f"OBS-{m}-{kind}-{t:%Y%m%dT%H}", "sensor_id": sid, "machine_id": m,
                        "window_start": t, "window_end": t + H(1), "mean": round(mean, 3), "min": round(mean - 0.9 * sd * 2, 3),
                        "max": round(mx, 3), "std": round(sd, 3), "sample_count": 3600 * 10 if kind != "VIB" else 3600000,
                        "quality": "GOOD", "is_anomalous": abs(resid) > tol})
alarms, anomalies = [], []
for sid, rows in series.items():
    m, kind = sid.split("-")[1], sid.split("-")[2]
    last = None
    run = []
    for r in rows + [None]:
        if r is not None and r[3]:
            run.append(r)
        elif run:
            peak = max(run, key=lambda x: abs(x[4]))
            anomalies.append({"anomaly_id": f"ANM-{len(anomalies) + 1:04d}", "sensor_id": sid, "machine_id": m,
                              "start": run[0][0], "end": run[-1][0] + H(1), "windows": len(run),
                              "peak_residual": round(peak[4], 3),
                              "anomaly_type": "level_shift" if len(run) >= 6 else "spike"})
            run = []
        if r is None:
            continue
        val = r[2] if kind in ("TEMP", "PRES") else r[1]
        if val > r[5] and (last is None or r[0] - last >= H(6)):
            alarms.append({"alarm_id": f"ALM-{len(alarms) + 1:04d}", "sensor_id": sid, "machine_id": m,
                           "raised_at": r[0], "severity": "HIGH", "rule": f"{kind}_HIGH", "value": round(val, 3),
                           "threshold": r[5], "acknowledged_by": ""})
            last = r[0]
alarms.sort(key=lambda a: a["raised_at"])
for i, a in enumerate(alarms, 1):
    a["alarm_id"] = f"ALM-{i:04d}"

# ------------------------------------------------------------------ RCA classes
FM = [("FM-01", "MATERIAL", "Raw material hardness/chemistry at spec limit (supplier heat/lot variation)", 8, 3, 6),
      ("FM-02", "METHOD", "Calibration step skipped: thermal offset verification not completed", 7, 4, 5),
      ("FM-03", "MACHINE", "Tool or grinding wheel wear beyond limit", 6, 5, 4),
      ("FM-04", "ENVIRONMENT", "Coolant concentration drift or contamination", 6, 3, 5),
      ("FM-05", "MAN", "Operator certification lapsed", 5, 3, 4),
      ("FM-06", "MEASUREMENT", "Sensor drift or spurious reading", 4, 5, 3)]
failure_modes = [{"failure_mode_id": a, "category": b, "description": c, "severity": s, "occurrence": o,
                  "detection": d, "rpn": s * o * d} for a, b, c, s, o, d in FM]
CPLAN = [("CP-01", "FM-01", "Incoming hardness verification per heat"), ("CP-02", "FM-02", "8-step calibration checklist with sign-off"),
         ("CP-03", "FM-03", "Wheel dressing and tool-life limits"), ("CP-04", "FM-04", "Weekly coolant titration"),
         ("CP-05", "FM-05", "Certification matrix review"), ("CP-06", "FM-06", "Sensor cross-check against redundant probe")]
control_plans = [{"control_plan_id": a, "failure_mode_id": b, "description": c} for a, b, c in CPLAN]
controlled_by = [{"failure_mode_id": b, "control_plan_id": a} for a, b, c in CPLAN]


def stats(machine_list, pred):
    sel = [w for w in wos if w["machine_id"] in machine_list and pred(w)]
    n = sum(w["units_produced"] for w in sel)
    return (sum(w["units_scrap"] for w in sel) / n) if n else 0.0


FULL_EFFECT = datetime(2026, 10, 14, 22)
last_two = {m: [w for w in wos if w["machine_id"] == m][-2:] for m in MID}
incidents = [
    {"incident_id": "INC-2026-1015-001", "title": "Scrap spike on precision lines", "status": "OPEN", "severity": "HIGH",
     "detected_at": DETECT, "detected_by": "scrap-spc-detector", "metric": "scrap_rate_pct", "baseline_value": 2.0,
     "observed_value": round(100 * stats(AFFECTED, lambda w: w["_start"] >= FULL_EFFECT), 1),
     "description": "Scrap rate on 5 machines across L1, L2 and L3 rose about 12 points over baseline within 16 hours; dominant defect DC-205 micro-fracture.",
     "line_ids": "L1;L2;L3", "closed_at": ""},
    {"incident_id": "INC-2026-0719-002", "title": "Surface finish scrap on gear grinder", "status": "CLOSED", "severity": "MEDIUM",
     "detected_at": datetime(2026, 7, 19, 10), "detected_by": "quality-engineer", "metric": "scrap_rate_pct",
     "baseline_value": 2.0, "observed_value": 6.1, "description": "Burr and finish defects on M10.",
     "line_ids": "L3", "closed_at": datetime(2026, 7, 21, 16)},
    {"incident_id": "INC-2026-0825-003", "title": "Dimensional drift on shaft line", "status": "CLOSED", "severity": "MEDIUM",
     "detected_at": datetime(2026, 8, 25, 9), "detected_by": "scrap-spc-detector", "metric": "scrap_rate_pct",
     "baseline_value": 2.0, "observed_value": 5.4, "description": "Bore dimension out of tolerance on L2.",
     "line_ids": "L2", "closed_at": datetime(2026, 8, 27, 12)}]
affects = [{"incident_id": "INC-2026-1015-001", "machine_id": m} for m in AFFECTED] + \
          [{"incident_id": "INC-2026-0719-002", "machine_id": "M10"}] + \
          [{"incident_id": "INC-2026-0825-003", "machine_id": m} for m in ("M05", "M06", "M07", "M08")]
evidence, evidenced_by = [], []
for m in AFFECTED:
    w = last_two[m]
    rate = sum(x["units_scrap"] for x in w) / sum(x["units_produced"] for x in w)
    evidence.append({"evidence_id": f"EV-{m}-SCRAP", "incident_id": "INC-2026-1015-001", "evidence_type": "SCRAP_TREND",
                     "ref_id": w[-1]["work_order_id"], "summary": f"{m} scrap {100 * rate:.1f}% over last two shifts vs 2.0% baseline"})
    ta = [a for a in anomalies if a["sensor_id"] == f"SN-{m}-TEMP" and a["start"] >= CAL_T]
    if ta:
        evidence.append({"evidence_id": f"EV-{m}-TEMP", "incident_id": "INC-2026-1015-001", "evidence_type": "TEMP_ANOMALY",
                         "ref_id": ta[-1]["anomaly_id"], "summary": f"{m} temperature level shift since {iso(ta[-1]['start'])}"})
evidenced_by = [{"incident_id": e["incident_id"], "evidence_id": e["evidence_id"]} for e in evidence]
causes = [{"cause_id": "CAUSE-H1", "incident_id": "INC-2026-0719-002", "description": "Grinding wheel worn beyond dress limit", "category": "MACHINE", "confidence": 0.9},
          {"cause_id": "CAUSE-H2", "incident_id": "INC-2026-0825-003", "description": "Coolant concentration drift", "category": "ENVIRONMENT", "confidence": 0.85}]
has_cause = [{"incident_id": c["incident_id"], "cause_id": c["cause_id"]} for c in causes]
cause_maps = [{"cause_id": "CAUSE-H1", "failure_mode_id": "FM-03"}, {"cause_id": "CAUSE-H2", "failure_mode_id": "FM-04"}]
corrective = [{"corrective_action_id": "CA-H1", "incident_id": "INC-2026-0719-002", "description": "Replace grinding wheel; add wheel-life counter", "status": "DONE", "owner_id": "EMP-E2"},
              {"corrective_action_id": "CA-H2", "incident_id": "INC-2026-0825-003", "description": "Flush coolant circuit; weekly titration", "status": "DONE", "owner_id": "EMP-E1"}]
decisions = [{"decision_id": "DEC-H1", "incident_id": "INC-2026-0719-002", "decision_type": "CORRECTIVE", "proposed_by": "EMP-E2", "summary": "Stop M10, replace wheel", "status": "EXECUTED"},
             {"decision_id": "DEC-H2", "incident_id": "INC-2026-0825-003", "decision_type": "CORRECTIVE", "proposed_by": "EMP-E1", "summary": "Flush coolant on L2", "status": "EXECUTED"}]
approvals = [{"approval_id": "AP-H1", "decision_id": "DEC-H1", "approver_id": "EMP-E2", "approved_at": datetime(2026, 7, 19, 14), "outcome": "APPROVED"},
             {"approval_id": "AP-H2", "decision_id": "DEC-H2", "approver_id": "EMP-E1", "approved_at": datetime(2026, 8, 25, 13), "outcome": "APPROVED"}]
has_decision = [{"incident_id": d["incident_id"], "decision_id": d["decision_id"]} for d in decisions]
approved_by = [{"decision_id": a["decision_id"], "approval_id": a["approval_id"]} for a in approvals]
corrected_by = [{"incident_id": c["incident_id"], "corrective_action_id": c["corrective_action_id"]} for c in corrective]
member_of = [{"employee_id": p["employee_id"], "crew_id": p["crew_id"]} for p in people if p["crew_id"]]

# ------------------------------------------------------------------ write CSVs
write("site", ["site_id", "name", "city", "country"], site)
write("area", ["area_id", "site_id", "name"], areas)
write("line", ["line_id", "name", "area_id", "product_code"], lines)
write("machine", ["machine_id", "line_id", "name", "machine_type", "install_year"], machines)
write("component", ["component_id", "machine_id", "name"], components)
write("sensor", ["sensor_id", "machine_id", "component_id", "sensor_type", "unit", "sampling_hz"], sensors)
write("tag", ["tag_id", "tag_name", "sensor_id", "protocol", "node_id"], tags)
write("observation_window", ["obs_id", "sensor_id", "machine_id", "window_start", "window_end", "mean", "min", "max", "std", "sample_count", "quality", "is_anomalous"], obs)
write("alarm", ["alarm_id", "sensor_id", "machine_id", "raised_at", "severity", "rule", "value", "threshold", "acknowledged_by"], alarms)
write("anomaly", ["anomaly_id", "sensor_id", "machine_id", "start", "end", "windows", "peak_residual", "anomaly_type"], anomalies)
write("product", ["product_code", "name", "line_id"], products)
write("recipe_step", ["recipe_step_id", "line_id", "seq", "name", "temp_setpoint_c"], recipe)
WOF = ["work_order_id", "machine_id", "line_id", "shift_id", "operator_id", "product_code", "lot_id", "batch_id", "planned_start", "planned_end", "units_planned", "units_produced", "units_good", "units_scrap", "units_rework", "scrap_rate", "status"]
write("work_order", WOF, wos)
write("batch", ["batch_id", "work_order_id", "product_code", "lot_id", "qty", "status", "machine_id"], batches)
write("inspection", ["inspection_id", "work_order_id", "machine_id", "inspected_units", "scrap_units", "rework_units", "dominant_defect_code", "first_pass_yield"], insp)
write("defect_code", ["defect_code", "description"], defect_codes)
write("employee", ["employee_id", "name", "role", "crew_id"], people)
write("crew", ["crew_id", "name"], crews)
write("shift", ["shift_id", "shift_name", "start", "end", "crew_id", "status"], shifts)
write("handover", ["handover_id", "from_shift_id", "to_shift_id", "from_crew_id", "to_crew_id", "handover_time", "duration_min", "checklist_complete", "rushed", "notes"], handovers)
write("training_record", ["training_id", "employee_id", "machine_type", "issued", "expires", "status"], training)
write("maintenance_order", ["order_id", "machine_id", "order_type", "plan_id", "crew_id", "technician_id", "scheduled_start", "actual_start", "actual_end", "status", "spare_part_id"], maint)
write("calibration", ["calibration_id", "order_id", "machine_id", "started_at", "ended_at", "steps_required", "steps_completed", "skipped_step", "duration_min", "handover_id", "recorded_result", "verification_signed_off"], calibs)
write("pm_plan", ["plan_id", "name", "interval_days"], pm_plans)
write("spare_part", ["spare_part_id", "name", "stock_qty"], spares)
write("supplier", ["supplier_id", "name", "tier", "iatf_certified", "shares_batch_data"], suppliers)
write("material", ["material_id", "name", "spec_hardness_hrc", "spec_carbon_pct", "spec_mn_pct"], materials)
write("bom", ["bom_id", "product_code", "material_id", "kg_per_unit"], bom)
write("material_lot", ["lot_id", "material_id", "qty_kg", "received_at", "po_id", "mill_cert_id", "status"], lots)
write("mill_certificate", ["mill_cert_id", "lot_id", "heat_number", "issued_by_supplier_id", "hardness_hrc", "carbon_pct", "manganese_pct", "within_spec", "edge_flag", "document_ref"], certs)
write("purchase_order", ["po_id", "supplier_id", "material_id", "qty_kg", "ordered_at", "received_at"], pos)
write("failure_mode", ["failure_mode_id", "category", "description", "severity", "occurrence", "detection", "rpn"], failure_modes)
write("control_plan", ["control_plan_id", "failure_mode_id", "description"], control_plans)
write("incident", ["incident_id", "title", "status", "severity", "detected_at", "detected_by", "metric", "baseline_value", "observed_value", "description", "line_ids", "closed_at"], incidents)
write("evidence", ["evidence_id", "incident_id", "evidence_type", "ref_id", "summary"], evidence)
write("cause", ["cause_id", "incident_id", "description", "category", "confidence"], causes)
write("corrective_action", ["corrective_action_id", "incident_id", "description", "status", "owner_id"], corrective)
write("decision", ["decision_id", "incident_id", "decision_type", "proposed_by", "summary", "status"], decisions)
write("approval", ["approval_id", "decision_id", "approver_id", "approved_at", "outcome"], approvals)
E = lambda n, f, r: write("edges_" + n, f, r)
E("processed", ["machine_id", "lot_id", "first_used", "last_used", "work_orders", "units"], list(processed.values()))
E("supplied_by", ["lot_id", "supplier_id", "relation"], lot_sup)
E("supplies", ["supplier_id", "buyer_supplier_id", "material_id"], supplies)
E("maintenance_on", ["order_id", "machine_id"], maint_on)
E("performed_by", ["order_id", "crew_id"], maint_by)
E("member_of", ["employee_id", "crew_id"], member_of)
E("affects", ["incident_id", "machine_id"], affects)
E("evidenced_by", ["incident_id", "evidence_id"], evidenced_by)
E("has_cause", ["incident_id", "cause_id"], has_cause)
E("cause_maps_to", ["cause_id", "failure_mode_id"], cause_maps)
E("corrected_by", ["incident_id", "corrective_action_id"], corrected_by)
E("has_decision", ["incident_id", "decision_id"], has_decision)
E("approved_by", ["decision_id", "approval_id"], approved_by)
E("controlled_by", ["failure_mode_id", "control_plan_id"], controlled_by)

# ------------------------------------------------------------------ ground truth
pre = lambda w: w["_start"] < CAL_T
post = lambda w: w["_start"] >= FULL_EFFECT
role_of = {**{m: "AFFECTED" for m in AFFECTED}, **{m: "LOT409_ONLY" for m in LOT409_ONLY},
           **{m: "CALIBRATION_ONLY" for m in CALIB_ONLY}, **{m: "NEITHER" for m in NEITHER}}
cal14 = {c["machine_id"]: c for c in calibs if c["started_at"] >= datetime(2026, 10, 14)}
temp_anom = {m: any(a["sensor_id"] == f"SN-{m}-TEMP" and a["start"] >= CAL_T for a in anomalies) for m in MID}
machine_summary = {m: {"role": role_of[m], "line": LINE_OF[m], "lot_at_cutoff": lot_for(m, END - H(1)),
                       "oct14_calibration_crew": cal14[m]["calibration_id"] and next(e["crew"] for e in events if e["order_id"] == cal14[m]["order_id"]),
                       "oct14_steps_completed": cal14[m]["steps_completed"],
                       "scrap_pct_before_calibration": round(100 * stats([m], pre), 2),
                       "scrap_pct_full_effect_shifts": round(100 * stats([m], post), 2),
                       "temp_level_shift_since_calibration": temp_anom[m]} for m in MID}
l409 = [b for b in batches if b["lot_id"] == "LOT-409"]
excess = sum(w["units_scrap"] - BASE_SCRAP * w["units_produced"] for w in wos
             if w["machine_id"] in AFFECTED and w["_overlap"] > 0)
aff_units_day = sum(RATE[LINE_OF[m]] for m in AFFECTED) * 3
gt = {
    "scenario": "Scrap spike on 5 machines caused by the interaction of Tier-3 steel lot LOT-409 and a rushed-handover calibration that skipped thermal offset verification.",
    "seed": args.seed, "timestamps_utc": True,
    "timeline": {"lot_409_received": iso(LOTS["LOT-409"][3]), "lot_409_first_use_by_machine": {m: iso(t) for m, t in L409_FIRST.items()},
                 "rushed_handover": iso(CAL_T), "calibration_end_by_machine": {m: iso(t) for m, t in sorted(cal_end_oct14.items())},
                 "incident_detected": iso(DETECT), "data_cutoff": iso(END)},
    "root_cause": {"lot_id": "LOT-409", "tier3_supplier": "SUP-T3-01", "tier2_supplier": "SUP-T2-01", "tier1_supplier": "SUP-T1-01",
                   "mill_cert": "MC-409", "lot_note": "within spec but at upper edge on hardness, carbon and manganese",
                   "crew": "CREW-B", "handover_id": "HO-20261014-S", "skipped_step": SKIPPED,
                   "calibration_orders": {m: next(e["order_id"] for e in events if e["machine"] == m and e["start"] >= datetime(2026, 10, 14) and e["crew"] == "CREW-B") for m in B_ORDER},
                   "classification": "Material & Method Vulnerability: Supplier Lot Variation + Missed Calibration Step",
                   "maps_to_failure_modes": ["FM-01", "FM-02"], "mechanism": "interaction; neither factor alone produces the scrap spike"},
    "affected_machines": AFFECTED,
    "must_not_conclude": [
        "Supplier SUP-T3-01 alone is the cause (LOT-412 from the same supplier runs fine on M01)",
        "Crew B alone is the cause (Crew B calibrated M05, M12, M04 correctly earlier; M01 and M08 were miscalibrated by Crew B with no scrap rise)",
        "LOT-409 alone is the cause (M04, M07, M10 run LOT-409 with normal scrap)",
        "Temperature drift alone is the cause (M01 and M08 show it without scrap rise)"],
    "red_herrings": {"M05_vibration_drift": "Slow vibration drift from Oct 11, alarms from about Oct 13; scrap normal",
                     "M12_pressure_glitch": "Three spurious pressure windows on Oct 8, sensor glitch",
                     "expired_training": ["EMP-C2 (CNC turning center)", "EMP-B3 (Gear grinder)"],
                     "short_handovers_without_followup": [iso(t) for t in sorted(DECOY_SHORT)],
                     "isolated_random_anomalies": "A few single-window anomalies appear by chance in telemetry"},
    "machine_summary": machine_summary,
    "blast_radius": {"machines_on_lot_409": LOT409_MACHINES, "lines": ["L1", "L2", "L3"],
                     "batches_from_lot_409": len(l409), "units_from_lot_409": sum(b["qty"] for b in l409),
                     "batches_by_status": {s: sum(1 for b in l409 if b["status"] == s) for s in ("WIP", "FINISHED", "SHIPPED")},
                     "suspect_batches_on_failing_machines_since_effect": sum(1 for b in batches if b["machine_id"] in AFFECTED and b["lot_id"] == "LOT-409" and datetime.strptime(b["batch_id"].split("-")[1], "%Y%m%d") >= datetime(2026, 10, 14)),
                     "at_risk_but_passing_machines": LOT409_ONLY},
    "impact_inputs": {"baseline_scrap_rate": BASE_SCRAP, "excess_scrap_units_so_far": round(excess),
                      "affected_units_per_day": aff_units_day, "projected_excess_scrap_units_per_day": round(aff_units_day * 0.12),
                      "assumptions_for_agent": {"unit_cost_usd": 85, "rework_cost_multiplier": 3, "hidden_cost_uplift": 0.5, "downtime_cost_per_hour_usd": 2300000}},
    "expected_remediation": {"interlock_halt": AFFECTED, "recalibrate": B_ORDER, "lot_hold": "LOT-409 remaining stock pending hardness verification",
                             "reroute_candidates": NEITHER, "human_approval_required_for": ["interlock", "reroute", "lot hold"]},
    "agent_test_cases": [
        {"tool": "common_lots(AFFECTED)", "expect": ["LOT-409"]},
        {"tool": "common_crews_oct14(AFFECTED)", "expect": ["CREW-B"]},
        {"tool": "cause_intersection()", "expect": {"machines": AFFECTED, "lot": "LOT-409", "crew": "CREW-B"}},
        {"tool": "blast_radius('LOT-409')", "expect_machines": LOT409_MACHINES},
        {"tool": "supplier_chain('LOT-409')", "expect": ["SUP-T1-01", "SUP-T2-01", "SUP-T3-01"]}]}
with open(os.path.join(args.out, "ground_truth.json"), "w") as f:
    json.dump(gt, f, indent=2)

# ------------------------------------------------------------------ self-check
failing = sorted({w["machine_id"] for w in wos if w["_start"] >= FULL_EFFECT and w["scrap_rate"] > 0.08})
assert failing == sorted(AFFECTED), failing
for m in LOT409_ONLY + CALIB_ONLY + NEITHER:
    assert stats([m], post) < 0.05, m
print("rows per file:")
for k, v in FILES.items():
    print(f"  {k:24s}{v:>7d}")
print("self-check passed: failing machines =", failing)
print("excess scrap units so far:", round(excess))
