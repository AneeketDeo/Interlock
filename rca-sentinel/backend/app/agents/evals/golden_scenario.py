"""ADK eval sets for the golden scenario: Lot #40921 + Maintenance Crew B skipped calibration."""

from __future__ import annotations

from typing import Any

# ── Golden Scenario Ground Truth ─────────────────────────────────────

GOLDEN_INCIDENT_ID = "INC-20261010-001"
GOLDEN_LINE_ID = "line-03"
GOLDEN_MACHINE_ID = "station-03b"
GOLDEN_CULPRIT_LOT_ID = "lot-40921"
GOLDEN_CULPRIT_SUPPLIER = "AlloyTech Global"  # Tier-3 supplier
GOLDEN_CULPRIT_CREW = "Maintenance Crew B"
GOLDEN_SILICON_PCT = 1.82  # Out-of-spec threshold: > 1.35%
GOLDEN_CALIBRATION_OFFSET_MM = 0.035  # Tolerance: ±0.010mm
GOLDEN_SCRAP_RATE_SPIKE_PCT = 13.4  # vs baseline 1.2%
GOLDEN_AFFECTED_UNITS = 420
GOLDEN_GROSS_IMPACT_USD = 180_000.0  # Minimum expected

# ── Eval Assertions ──────────────────────────────────────────────────


def assert_detect_result(detect_result: dict[str, Any]) -> None:
    """Validate DetectAgent output for golden scenario."""
    assert detect_result is not None, "DetectAgent produced no output"
    assert detect_result.get("incident_confirmed") is True, (
        "DetectAgent must confirm the golden scenario incident"
    )
    assert "machine_context" in detect_result, "DetectAgent must return machine_context"
    assert "anomaly_summary" in detect_result, "DetectAgent must return anomaly_summary"


def assert_diagnose_result(diagnose_result: dict[str, Any]) -> None:
    """Validate DiagnoseAgent output for golden scenario."""
    assert diagnose_result is not None, "DiagnoseAgent produced no output"

    primary = diagnose_result.get("primary_cause", {})
    assert primary, "DiagnoseAgent must identify a primary cause"
    assert primary.get("confidence", 0) >= 0.80, (
        "Primary cause confidence must be >= 0.80 for golden scenario"
    )

    # Must identify the culprit lot
    culprit_lot = diagnose_result.get("culprit_lot_id")
    assert culprit_lot is not None, "DiagnoseAgent must identify culprit_lot_id"
    assert "40921" in str(culprit_lot), (
        f"Golden scenario culprit lot must contain '40921', got: {culprit_lot}"
    )

    # Must identify the maintenance crew
    evidence_ids = diagnose_result.get("evidence_ids", [])
    assert len(evidence_ids) >= 2, (
        "DiagnoseAgent must cite at least 2 graph entity IDs as evidence"
    )


def assert_classify_result(classify_result: dict[str, Any]) -> None:
    """Validate ClassifyAgent output for golden scenario."""
    assert classify_result is not None, "ClassifyAgent produced no output"

    failure_modes = classify_result.get("failure_modes", [])
    assert len(failure_modes) >= 1, "ClassifyAgent must identify at least one failure mode"

    iso_category = classify_result.get("iso_category", "")
    assert iso_category in {"process_failure", "supplier_material", "human_error", "compound"}, (
        f"Unexpected ISO category: {iso_category}"
    )

    assert classify_result.get("classification_confidence", 0) >= 0.70, (
        "Classification confidence must be >= 0.70"
    )


def assert_forecast_result(forecast_result: dict[str, Any]) -> None:
    """Validate ForecastAgent output for golden scenario."""
    assert forecast_result is not None, "ForecastAgent produced no output"

    total_units = forecast_result.get("total_affected_units", 0)
    assert total_units >= 300, (
        f"Golden scenario must affect >= 300 units, got: {total_units}"
    )

    gross_impact = forecast_result.get("gross_impact_usd", 0)
    assert gross_impact >= GOLDEN_GROSS_IMPACT_USD, (
        f"Gross impact must be >= ${GOLDEN_GROSS_IMPACT_USD:,.0f}, got: ${gross_impact:,.2f}"
    )

    quarantine_candidates = forecast_result.get("quarantine_candidates", [])
    assert len(quarantine_candidates) >= 1, (
        "ForecastAgent must identify quarantine candidates"
    )

    assert forecast_result.get("containment_urgency") in {"immediate", "high"}, (
        "Golden scenario requires 'immediate' or 'high' containment urgency"
    )


def assert_remediate_result(remediate_result: dict[str, Any]) -> None:
    """Validate RemediateAgent output for golden scenario."""
    assert remediate_result is not None, "RemediateAgent produced no output"

    proposed_actions = remediate_result.get("proposed_actions", [])
    assert len(proposed_actions) >= 2, (
        "RemediateAgent must propose at least 2 actions for golden scenario"
    )

    # ALL actions must require human approval
    for action in proposed_actions:
        assert action.get("requires_human_approval") is True, (
            f"Action {action.get('id')} must require human approval"
        )

    pending_count = remediate_result.get("actions_pending_approval", 0)
    assert pending_count >= 2, "At least 2 actions must be pending approval"

    # Must include 8D report stub
    report_8d = remediate_result.get("8d_report_stub", {})
    assert "D3_containment" in report_8d, "8D report must include D3 containment"
    assert "D5_corrective_action" in report_8d, "8D report must include D5 corrective action"


def assert_full_evidence_package(evidence_package: dict[str, Any]) -> None:
    """Validate the complete 5-stage RCA Evidence Package for the golden scenario."""
    assert evidence_package is not None

    stages = evidence_package.get("stages", {})
    assert stages, "Evidence package must contain stages"

    # Run all stage-level assertions
    assert_detect_result(stages.get("detect") or {})
    assert_diagnose_result(stages.get("diagnose") or {})
    assert_classify_result(stages.get("classify") or {})
    assert_forecast_result(stages.get("forecast") or {})
    assert_remediate_result(stages.get("remediate") or {})
