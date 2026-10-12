"""Domain enumerations for RCA-Sentinel.

Fixed vocabularies used across boundaries. All use StrEnum for JSON-friendly
serialization and database storage.
"""

from __future__ import annotations

from enum import StrEnum


class IncidentStatus(StrEnum):
    """Lifecycle states of an incident."""

    DETECTED = "detected"
    DIAGNOSING = "diagnosing"
    CLASSIFIED = "classified"
    FORECASTED = "forecasted"
    REMEDIATING = "remediating"
    AWAITING_APPROVAL = "awaiting_approval"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Severity(StrEnum):
    """Incident severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionStage(StrEnum):
    """Stages in the RCA decision chain (mirrors 8D)."""

    DETECT = "detect"          # D2: Problem Description
    DIAGNOSE = "diagnose"      # D4: Root Cause Analysis
    CLASSIFY = "classify"      # Failure taxonomy mapping
    FORECAST = "forecast"      # Blast radius + financials
    REMEDIATE = "remediate"    # D3 + D5: Containment + Corrective


class ApprovalStatus(StrEnum):
    """Approval workflow states."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ActionType(StrEnum):
    """Types of remediation actions."""

    INTERLOCK = "interlock"
    ERP_REROUTE = "erp_reroute"
    CMMS_WORK_ORDER = "cmms_work_order"
    QUARANTINE_LOT = "quarantine_lot"
    OPERATOR_ALERT = "operator_alert"


class ActionReversibility(StrEnum):
    """Whether an action can be undone."""

    REVERSIBLE = "reversible"
    IRREVERSIBLE = "irreversible"


class ApproverRole(StrEnum):
    """Roles that can approve actions."""

    OPERATOR = "operator"
    RELIABILITY_ENGINEER = "reliability_engineer"
    QUALITY_ENGINEER = "quality_engineer"
    ADMIN = "admin"


class SourceSystem(StrEnum):
    """Source systems for ingested data."""

    PLC_MES = "plc_mes"
    ERP = "erp"
    CMMS = "cmms"
    OPERATOR_LOG = "operator_log"
    SUPPLIER_DATA = "supplier_data"
    SIMULATOR = "simulator"


class DetectorType(StrEnum):
    """Types of anomaly detectors."""

    EWMA = "ewma"
    CUSUM = "cusum"
    ZSCORE = "zscore"


class SensorType(StrEnum):
    """Types of sensors on machines."""

    TEMPERATURE = "temperature"
    VIBRATION = "vibration"
    PRESSURE = "pressure"
    CURRENT = "current"
    SPEED = "speed"
    TORQUE = "torque"
    FLOW_RATE = "flow_rate"
    HUMIDITY = "humidity"


class MaintenanceType(StrEnum):
    """Types of maintenance activities."""

    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    CALIBRATION = "calibration"
    INSPECTION = "inspection"


class ShiftType(StrEnum):
    """Shift patterns."""

    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"
