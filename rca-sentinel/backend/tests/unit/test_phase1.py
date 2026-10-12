"""Tests for Phase 1: config, domain models, ontology, SHACL validation, bootstrap."""

from __future__ import annotations

from app.core.config import AppEnv, Settings
from app.core.errors import (
    ApprovalRequired,
    ConfidenceBelowThreshold,
    GraphConnectionError,
    GraphQueryError,
    PolicyViolation,
    RcaError,
    ValidationRejected,
)
from app.domain.enums import (
    ActionType,
    ApprovalStatus,
    DecisionStage,
    IncidentStatus,
    Severity,
)
from app.domain.models import (
    Approval,
    DecisionObject,
    ErrorResponse,
    FailureMode,
    HealthStatus,
    Incident,
    MaterialLot,
    Plant,
    RemediationAction,
    Supplier,
)

# ── Config Tests ────────────────────────────────────────────────────


class TestConfig:
    def test_default_settings(self) -> None:
        settings = Settings(
            neo4j_password="test",
            timescale_password="test",
            _env_file=None,
        )
        assert settings.app_env == AppEnv.DEV
        assert settings.dry_run is True
        assert settings.kill_switch_enabled is False
        assert settings.proactive_detection_enabled is False

    def test_cors_origins_from_string(self) -> None:
        settings = Settings(
            cors_origins="http://a.com, http://b.com",
            neo4j_password="test",
            timescale_password="test",
            _env_file=None,
        )
        assert settings.cors_origins == ["http://a.com", "http://b.com"]

    def test_timescale_dsn(self) -> None:
        settings = Settings(
            timescale_host="db",
            timescale_port=5432,
            timescale_user="user",
            timescale_password="pass",
            timescale_db="mydb",
            neo4j_password="test",
            _env_file=None,
        )
        assert settings.timescale_dsn == "postgresql://user:pass@db:5432/mydb"

    def test_is_production(self) -> None:
        settings = Settings(
            app_env="prod",
            neo4j_password="test",
            timescale_password="test",
            _env_file=None,
        )
        assert settings.is_production is True


# ── Domain Model Tests ──────────────────────────────────────────────


class TestDomainModels:
    def test_plant_creation(self) -> None:
        plant = Plant(name="Factory Alpha", code="FA01", location="Detroit, MI")
        assert plant.name == "Factory Alpha"
        assert plant.code == "FA01"
        assert plant.id  # UUID auto-generated

    def test_incident_defaults(self) -> None:
        incident = Incident(title="Scrap spike", description="12% scrap rate")
        assert incident.status == IncidentStatus.DETECTED
        assert incident.severity == Severity.MEDIUM
        assert incident.correlation_id  # auto-generated

    def test_failure_mode_rpn(self) -> None:
        fm = FailureMode(
            name="Material Defect",
            description="Lot variation",
            severity_score=8,
            occurrence_score=4,
            detection_score=6,
        )
        assert fm.rpn == 192  # 8 * 4 * 6

    def test_decision_object_stages(self) -> None:
        for stage in DecisionStage:
            do = DecisionObject(
                incident_id="inc-1",
                stage=stage,
                agent_name=f"{stage}_agent",
                confidence=0.85,
            )
            assert do.stage == stage

    def test_material_lot(self) -> None:
        lot = MaterialLot(
            lot_number="40921",
            supplier_id="sup-1",
            material_type="steel_alloy",
            quantity=500.0,
        )
        assert lot.lot_number == "40921"

    def test_supplier_tiers(self) -> None:
        for tier in [1, 2, 3]:
            s = Supplier(name=f"Tier{tier}Co", code=f"T{tier}", tier=tier)
            assert s.tier == tier

    def test_approval_defaults(self) -> None:
        approval = Approval(action_id="act-1", incident_id="inc-1")
        assert approval.status == ApprovalStatus.PENDING
        assert approval.decided_at is None

    def test_remediation_action(self) -> None:
        action = RemediationAction(
            incident_id="inc-1",
            decision_object_id="do-1",
            action_type=ActionType.INTERLOCK,
            description="Engage safety interlock on machine M-05",
        )
        assert action.action_type == ActionType.INTERLOCK

    def test_health_status(self) -> None:
        hs = HealthStatus(
            status="ok",
            version="0.1.0",
            environment="dev",
            checks={"neo4j_aura": True, "redis": True},
        )
        assert hs.status == "ok"
        assert hs.checks["neo4j_aura"] is True

    def test_error_response(self) -> None:
        err = ErrorResponse(
            code="NOT_FOUND",
            message="Incident not found",
            correlation_id="abc-123",
        )
        assert err.code == "NOT_FOUND"


# ── Error Hierarchy Tests ───────────────────────────────────────────


class TestErrors:
    def test_rca_error_base(self) -> None:
        err = RcaError("Something failed", details={"key": "value"})
        assert str(err) == "Something failed"
        assert err.details == {"key": "value"}

    def test_graph_connection_error(self) -> None:
        err = GraphConnectionError("Cannot connect to Aura")
        assert isinstance(err, RcaError)

    def test_approval_required(self) -> None:
        err = ApprovalRequired(
            "Interlock requires approval",
            approval_id="apr-1",
            action_type="interlock",
        )
        assert err.approval_id == "apr-1"
        assert err.details["action_type"] == "interlock"

    def test_confidence_below_threshold(self) -> None:
        err = ConfidenceBelowThreshold(
            "Low confidence",
            confidence=0.3,
            threshold=0.7,
        )
        assert err.confidence == 0.3
        assert err.threshold == 0.7

    def test_error_hierarchy(self) -> None:
        """All domain errors are subclasses of RcaError."""
        errors = [
            GraphQueryError("query failed"),
            GraphConnectionError("conn failed"),
            ValidationRejected("invalid data"),
            PolicyViolation("policy violated"),
        ]
        for err in errors:
            assert isinstance(err, RcaError)


# ── Enum Tests ──────────────────────────────────────────────────────


class TestEnums:
    def test_incident_status_values(self) -> None:
        assert IncidentStatus.DETECTED.value == "detected"
        assert IncidentStatus.RESOLVED.value == "resolved"

    def test_severity_values(self) -> None:
        assert Severity.CRITICAL.value == "critical"

    def test_decision_stage_order(self) -> None:
        stages = list(DecisionStage)
        assert stages == [
            DecisionStage.DETECT,
            DecisionStage.DIAGNOSE,
            DecisionStage.CLASSIFY,
            DecisionStage.FORECAST,
            DecisionStage.REMEDIATE,
        ]

    def test_action_type_values(self) -> None:
        assert ActionType.INTERLOCK.value == "interlock"
        assert ActionType.ERP_REROUTE.value == "erp_reroute"


# ── Ontology Tests ──────────────────────────────────────────────────


class TestOntology:
    def test_ontology_file_exists(self) -> None:
        from app.ontology.loader import ONTOLOGY_PATH

        assert ONTOLOGY_PATH.exists()

    def test_parse_ontology(self) -> None:
        from rdflib import Graph

        from app.ontology.loader import ONTOLOGY_PATH

        g = Graph()
        g.parse(str(ONTOLOGY_PATH), format="turtle")
        assert len(g) > 50  # Should have many triples

    def test_ontology_loader_extract_classes(self) -> None:
        from app.ontology.loader import OntologyLoader

        # We can't test load() without Neo4j, but can test parsing
        loader = OntologyLoader.__new__(OntologyLoader)
        from rdflib import Graph

        loader._graph = Graph()
        loader.parse()
        classes = loader._extract_classes()
        class_names = {c["name"] for c in classes}
        expected = {
            "Plant", "Line", "Machine", "Sensor", "Tag",
            "WorkOrder", "Batch", "Product",
            "Operator", "Shift", "Crew",
            "MaintenanceLog", "CalibrationEvent",
            "Supplier", "MaterialLot", "Component", "BOMItem",
            "DefectCode", "FailureMode", "Cause", "ControlPlan",
            "Incident", "DecisionObject", "EvidenceLink",
            "RemediationAction", "Approval",
        }
        assert expected.issubset(class_names), f"Missing: {expected - class_names}"

    def test_ontology_loader_extract_relationships(self) -> None:
        from rdflib import Graph

        from app.ontology.loader import OntologyLoader

        loader = OntologyLoader.__new__(OntologyLoader)
        loader._graph = Graph()
        loader.parse()
        props = loader._extract_object_properties()
        prop_names = {p["name"] for p in props}
        expected = {
            "HAS_SENSOR", "PROCESSED", "RUNS", "SERVICED", "PERFORMED",
            "SUPPLIED_BY", "SUPPLIES_TO", "FROM_LOT", "MAPS_TO",
            "HAS_DECISION", "HAS_EVIDENCE", "CHAIN_NEXT",
            "HANDOVER_TO", "PROPOSES", "REQUIRES_APPROVAL",
        }
        assert expected.issubset(prop_names), f"Missing: {expected - prop_names}"

    def test_supplier_has_vendor_alias(self) -> None:
        from rdflib import Graph
        from rdflib.namespace import SKOS

        from app.ontology.loader import ONTOLOGY_PATH, RCA

        g = Graph()
        g.parse(str(ONTOLOGY_PATH), format="turtle")
        alt_labels = list(g.objects(RCA.Supplier, SKOS.altLabel))
        assert any(str(label) == "Vendor" for label in alt_labels)


# ── SHACL Validator Tests ───────────────────────────────────────────


class TestShaclValidator:
    def test_shapes_file_exists(self) -> None:
        from app.ontology.validator import SHAPES_PATH

        assert SHAPES_PATH.exists()

    def test_valid_material_lot(self) -> None:
        from app.ontology.validator import ShaclValidator

        validator = ShaclValidator()
        conforms, reason = validator.validate_single(
            {
                "id": "lot-1",
                "lot_number": "40921",
                "material_type": "steel_alloy",
                "quantity": 500.0,
            },
            "MaterialLot",
        )
        assert conforms, f"Expected valid, got: {reason}"

    def test_invalid_material_lot_missing_lot_number(self) -> None:
        from app.ontology.validator import ShaclValidator

        validator = ShaclValidator()
        conforms, reason = validator.validate_single(
            {
                "id": "lot-bad",
                "material_type": "steel_alloy",
                "quantity": 500.0,
            },
            "MaterialLot",
        )
        assert not conforms
        assert reason is not None

    def test_valid_supplier(self) -> None:
        from app.ontology.validator import ShaclValidator

        validator = ShaclValidator()
        conforms, reason = validator.validate_single(
            {"id": "sup-1", "name": "SteelCo", "tier": 3},
            "Supplier",
        )
        assert conforms, f"Expected valid, got: {reason}"

    def test_invalid_supplier_tier(self) -> None:
        from app.ontology.validator import ShaclValidator

        validator = ShaclValidator()
        conforms, reason = validator.validate_single(
            {"id": "sup-bad", "name": "BadCo", "tier": 5},
            "Supplier",
        )
        assert not conforms
        assert reason is not None

    def test_batch_validation(self) -> None:
        from app.ontology.validator import ShaclValidator

        validator = ShaclValidator()
        records = [
            {"id": "lot-1", "lot_number": "001", "material_type": "steel", "quantity": 100.0},
            {"id": "lot-2", "lot_number": "002", "material_type": "copper", "quantity": 200.0},
            {"id": "lot-3", "material_type": "aluminum", "quantity": 50.0},  # missing lot_number
        ]
        result = validator.validate_records(records, "MaterialLot")
        assert result.records_validated == 3
        assert result.records_passed == 2
        assert result.records_failed == 1
        assert len(result.violations) == 1


# ── Bootstrap Tests (no Neo4j needed) ───────────────────────────────


class TestBootstrap:
    def test_constraints_are_defined(self) -> None:
        from app.graph.bootstrap import CONSTRAINTS

        assert len(CONSTRAINTS) > 20
        # Verify key constraints exist
        constraint_str = " ".join(CONSTRAINTS)
        for label in ["Plant", "Line", "Machine", "Sensor", "MaterialLot",
                       "Supplier", "Incident", "DecisionObject", "Approval"]:
            assert label in constraint_str, f"Missing constraint for {label}"

    def test_indexes_are_defined(self) -> None:
        from app.graph.bootstrap import INDEXES

        assert len(INDEXES) > 5
