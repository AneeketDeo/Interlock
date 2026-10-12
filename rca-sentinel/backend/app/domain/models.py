"""Domain models for RCA-Sentinel.

Pydantic v2 models for all data crossing boundaries: API, MCP tools,
agent outputs, ingestion records. Bi-temporal properties and provenance
on every entity.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from app.domain.enums import (
    ActionReversibility,
    ActionType,
    ApprovalStatus,
    ApproverRole,
    DecisionStage,
    DetectorType,
    IncidentStatus,
    MaintenanceType,
    SensorType,
    Severity,
    ShiftType,
    SourceSystem,
)

# ── Base models with common fields ──────────────────────────────────


class TimestampMixin(BaseModel):
    """Bi-temporal + provenance fields required on every graph entity."""

    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_to: datetime | None = None
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    source_system: SourceSystem = SourceSystem.SIMULATOR
    source_record_id: str = ""
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    pipeline_run_id: str = ""


class BaseEntity(TimestampMixin):
    """Base entity with ID."""

    id: str = Field(default_factory=lambda: str(uuid4()))


# ── Manufacturing Entities ──────────────────────────────────────────


class Plant(BaseEntity):
    """Manufacturing plant."""

    name: str
    code: str
    location: str


class Line(BaseEntity):
    """Assembly/production line within a plant."""

    name: str
    code: str
    plant_id: str
    downtime_cost_per_hour: float = 5000.0
    target_oee: float = 0.85


class Machine(BaseEntity):
    """Machine on a production line."""

    name: str
    code: str
    line_id: str
    machine_type: str
    status: str = "operational"


class Sensor(BaseEntity):
    """Sensor attached to a machine."""

    tag: str
    sensor_type: SensorType
    machine_id: str
    unit: str = ""
    upper_limit: float | None = None
    lower_limit: float | None = None


class Tag(BaseEntity):
    """Process tag for telemetry data."""

    name: str
    description: str = ""
    sensor_id: str
    engineering_unit: str = ""


# ── Work and Production ─────────────────────────────────────────────


class WorkOrder(BaseEntity):
    """MES work order."""

    order_number: str
    product_id: str
    line_id: str
    quantity_planned: int
    quantity_produced: int = 0
    quantity_scrapped: int = 0
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str = "open"


class Batch(BaseEntity):
    """Production batch."""

    batch_number: str
    product_id: str
    work_order_id: str
    quantity: int
    scrap_count: int = 0


class Product(BaseEntity):
    """Product being manufactured."""

    name: str
    part_number: str
    product_family: str = ""


# ── Personnel ───────────────────────────────────────────────────────


class Operator(BaseEntity):
    """Production operator."""

    employee_id: str
    name: str
    certification_level: str = "standard"


class Shift(BaseEntity):
    """Shift period."""

    shift_type: ShiftType
    start_time: datetime
    end_time: datetime
    line_id: str
    notes: str = ""


class Crew(BaseEntity):
    """Maintenance or operations crew."""

    name: str
    crew_type: str  # "maintenance", "operations"
    member_ids: list[str] = Field(default_factory=list)


# ── Maintenance ─────────────────────────────────────────────────────


class MaintenanceLog(BaseEntity):
    """Maintenance activity record."""

    machine_id: str
    crew_id: str
    maintenance_type: MaintenanceType
    description: str
    performed_at: datetime
    duration_minutes: int
    calibration_step_completed: bool = True
    notes: str = ""


class CalibrationEvent(BaseEntity):
    """Calibration event for a machine/sensor."""

    machine_id: str
    sensor_id: str | None = None
    crew_id: str
    performed_at: datetime
    passed: bool = True
    deviation: float = 0.0
    notes: str = ""


# ── Supply Chain ────────────────────────────────────────────────────


class Supplier(BaseEntity):
    """Supplier in the tier chain."""

    name: str
    code: str
    tier: int  # 1, 2, or 3
    parent_supplier_id: str | None = None
    material_types: list[str] = Field(default_factory=list)


class MaterialLot(BaseEntity):
    """Lot of material from a supplier."""

    lot_number: str
    supplier_id: str
    material_type: str
    quantity: float
    unit: str = "kg"
    received_date: datetime | None = None
    certificate_of_analysis: str = ""
    quality_grade: str = "A"


class Component(BaseEntity):
    """Component used in production, traced to a material lot."""

    part_number: str
    material_lot_id: str
    quantity: float


class BOMItem(BaseEntity):
    """Bill of Materials item."""

    product_id: str
    component_part_number: str
    quantity_per_unit: float
    position: int


# ── Quality ─────────────────────────────────────────────────────────


class DefectCode(BaseEntity):
    """Standardized defect classification code."""

    code: str
    description: str
    category: str
    failure_mode_id: str | None = None


class FailureMode(BaseEntity):
    """PFMEA failure mode."""

    name: str
    description: str
    severity_score: int = 1  # 1-10
    occurrence_score: int = 1  # 1-10
    detection_score: int = 1  # 1-10
    category: str = ""
    control_plan_id: str | None = None

    @property
    def rpn(self) -> int:
        """Risk Priority Number."""
        return self.severity_score * self.occurrence_score * self.detection_score


class ControlPlan(BaseEntity):
    """Quality control plan."""

    name: str
    description: str
    product_id: str
    inspection_method: str = ""
    frequency: str = ""


# ── Incident and Decision ──────────────────────────────────────────


class Incident(BaseEntity):
    """Detected anomaly incident."""

    title: str
    description: str
    status: IncidentStatus = IncidentStatus.DETECTED
    severity: Severity = Severity.MEDIUM
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    line_ids: list[str] = Field(default_factory=list)
    machine_ids: list[str] = Field(default_factory=list)
    detector_type: DetectorType | None = None
    detector_confidence: float = 0.0
    scrap_rate_observed: float = 0.0
    scrap_rate_baseline: float = 0.0
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))

    # 5W2H auto-populated
    who: str = ""
    what: str = ""
    when: str = ""
    where: str = ""
    why: str = ""
    how: str = ""
    how_many: str = ""


class EvidenceLink(BaseEntity):
    """Link from a decision to a piece of evidence in the graph."""

    decision_object_id: str
    evidence_type: str  # "node", "relationship", "telemetry_window", "document"
    evidence_id: str
    label: str = ""
    confidence: float = 1.0
    summary: str = ""


class DecisionObject(BaseEntity):
    """First-class node in the RCA chain. Forms a verifiable chain:
    Detect -> Diagnose -> Classify -> Forecast -> Remediate.
    """

    incident_id: str
    stage: DecisionStage
    agent_name: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    conclusion: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    previous_decision_id: str | None = None
    next_decision_id: str | None = None
    metadata: dict = Field(default_factory=dict)  # type: ignore[type-arg]


# ── Remediation ─────────────────────────────────────────────────────


class RemediationAction(BaseEntity):
    """Proposed remediation action awaiting approval."""

    incident_id: str
    decision_object_id: str
    action_type: ActionType
    description: str
    parameters: dict = Field(default_factory=dict)  # type: ignore[type-arg]
    reversibility: ActionReversibility = ActionReversibility.REVERSIBLE
    required_approver_role: ApproverRole = ApproverRole.RELIABILITY_ENGINEER
    priority: int = 1  # 1 = highest


class Approval(BaseEntity):
    """Approval record for a remediation action."""

    action_id: str
    incident_id: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    decided_at: datetime | None = None
    decided_by: str | None = None
    justification: str = ""
    evidence_snapshot_hash: str = ""
    edited_parameters: dict | None = None  # type: ignore[type-arg]
    expires_at: datetime | None = None


# ── Telemetry ───────────────────────────────────────────────────────


class TelemetryReading(BaseModel):
    """Single telemetry data point (stored in TimescaleDB)."""

    sensor_id: str
    tag: str
    timestamp: datetime
    value: float
    quality: int = 192  # OPC UA good quality


class TelemetrySummary(BaseModel):
    """Aggregated telemetry summary (stored in graph as summary node)."""

    sensor_id: str
    period_start: datetime
    period_end: datetime
    mean: float
    std_dev: float
    min_val: float
    max_val: float
    count: int
    anomaly_count: int = 0


# ── API Models ──────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Structured error response."""

    code: str
    message: str
    details: dict = Field(default_factory=dict)  # type: ignore[type-arg]
    correlation_id: str = ""


class HealthStatus(BaseModel):
    """Health check response."""

    status: str  # "ok" or "degraded"
    version: str
    environment: str
    checks: dict[str, bool] = Field(default_factory=dict)


class PaginatedResponse(BaseModel):
    """Cursor-based pagination wrapper."""

    items: list = Field(default_factory=list)  # type: ignore[type-arg]
    cursor: str | None = None
    has_more: bool = False
    total: int | None = None


# ── RCA Evidence Package (agent output) ─────────────────────────────


class RcaEvidencePackage(BaseModel):
    """Complete RCA output from the agent pipeline."""

    incident_id: str
    incident: Incident
    decisions: list[DecisionObject]
    evidence_links: list[EvidenceLink]
    root_cause_summary: str = ""
    failure_classification: str = ""
    blast_radius: dict = Field(default_factory=dict)  # type: ignore[type-arg]
    financial_impact: dict = Field(default_factory=dict)  # type: ignore[type-arg]
    proposed_actions: list[RemediationAction] = Field(default_factory=list)
    confidence: float = 0.0
    graph_paths: list[dict] = Field(default_factory=list)  # type: ignore[type-arg]


# ── Auth ────────────────────────────────────────────────────────────


class UserAccount(BaseModel):
    """User account for authentication."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    hashed_password: str
    role: ApproverRole
    full_name: str = ""
    is_active: bool = True


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str
    role: ApproverRole
    exp: datetime
