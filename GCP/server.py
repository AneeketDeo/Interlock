"""FastAPI: serves web/ and the RCA API. Run: uvicorn server:app --port 8080"""
import json, os, uuid, datetime as dt
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google.cloud import spanner

app = FastAPI()
REPORT = Path(os.getenv("RCA_REPORT", "latest_rca_report.json"))
_db = None
def db():
    global _db
    if _db is None:
        _db = spanner.Client(project=os.environ["SPANNER_PROJECT"]).instance(
            os.environ["SPANNER_INSTANCE"]).database(os.environ["SPANNER_DATABASE"])
    return _db

@app.get("/api/report")
def report():
    if not REPORT.exists(): raise HTTPException(404, "no report yet")
    return json.loads(REPORT.read_text())   # TODO: replace with live Spanner reads of Action/Decision nodes

class Decision(BaseModel):
    outcome: str      # APPROVED | REJECTED
    approver_id: str

@app.post("/api/actions/{action_id}/decision")
def decide(action_id: str, d: Decision):
    if d.outcome not in ("APPROVED", "REJECTED"): raise HTTPException(400, "bad outcome")
    def tx(t):
        rows = list(t.execute_sql("SELECT decision_id, status FROM Action WHERE action_id=@a",
                    params={"a": action_id}, param_types={"a": spanner.param_types.STRING}))
        if not rows: raise HTTPException(404, "unknown action")
        if rows[0][1] != "PROPOSED": raise HTTPException(409, "already decided")   # no double approval
        aid = "APR-" + uuid.uuid4().hex[:10]
        t.insert("Approval", ("approval_id", "decision_id", "approver_id", "approved_at", "outcome"),
                 [(aid, rows[0][0], d.approver_id, dt.datetime.now(dt.timezone.utc), d.outcome)])
        t.insert("ApprovedBy", ("decision_id", "approval_id"), [(rows[0][0], aid)])
        t.update("Action", ("action_id", "status"), [(action_id, d.outcome)])
    db().run_in_transaction(tx)
    return {"status": d.outcome}   # execution (Pub/Sub `commands`) is the remediation step, not here

app.mount("/", StaticFiles(directory="web", html=True), name="web")
