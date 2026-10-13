"""Tests for Phase 5: ADK Agents, Pipeline, Callbacks, and Eval Assertions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.agents.base import GEMINI_MODEL, RcaSessionState
from app.agents.callbacks import after_model_callback, before_agent_callback
from app.agents.evals.golden_scenario import (
    GOLDEN_AFFECTED_UNITS,
    GOLDEN_GROSS_IMPACT_USD,
    assert_classify_result,
    assert_detect_result,
    assert_diagnose_result,
    assert_forecast_result,
    assert_full_evidence_package,
    assert_remediate_result,
)

# ── Base + Agent Builder Tests ───────────────────────────────────────


class TestAgentBase:
    def test_gemini_model_constant(self) -> None:
        assert GEMINI_MODEL == "gemini-2.5-flash"

    def test_session_state_keys(self) -> None:
        assert RcaSessionState.INCIDENT_ID == "incident_id"
        assert RcaSessionState.LINE_ID == "line_id"
        assert RcaSessionState.MACHINE_ID == "machine_id"
        assert RcaSessionState.CULPRIT_LOT_ID == "culprit_lot_id"
        assert RcaSessionState.DETECT_RESULT == "detect_result"
        assert RcaSessionState.DIAGNOSE_RESULT == "diagnose_result"
        assert RcaSessionState.CLASSIFY_RESULT == "classify_result"
        assert RcaSessionState.FORECAST_RESULT == "forecast_result"
        assert RcaSessionState.REMEDIATE_RESULT == "remediate_result"


class TestAgentBuilders:
    """Test that all five agent builder functions return LlmAgent-like objects."""

    def _mock_mcp_toolset(self) -> MagicMock:
        return MagicMock()

    @patch("app.agents.detect_agent.build_mcp_toolset")
    def test_build_detect_agent(self, mock_toolset: MagicMock) -> None:
        mock_toolset.return_value = self._mock_mcp_toolset()
        from app.agents.detect_agent import build_detect_agent

        agent = build_detect_agent()
        assert agent is not None
        assert agent.name == "DetectAgent"  # type: ignore[union-attr]
        assert agent.output_key == RcaSessionState.DETECT_RESULT  # type: ignore[union-attr]

    @patch("app.agents.diagnose_agent.build_mcp_toolset")
    def test_build_diagnose_agent(self, mock_toolset: MagicMock) -> None:
        mock_toolset.return_value = self._mock_mcp_toolset()
        from app.agents.diagnose_agent import build_diagnose_agent

        agent = build_diagnose_agent()
        assert agent is not None
        assert agent.name == "DiagnoseAgent"  # type: ignore[union-attr]
        assert agent.output_key == RcaSessionState.DIAGNOSE_RESULT  # type: ignore[union-attr]

    @patch("app.agents.classify_agent.build_mcp_toolset")
    def test_build_classify_agent(self, mock_toolset: MagicMock) -> None:
        mock_toolset.return_value = self._mock_mcp_toolset()
        from app.agents.classify_agent import build_classify_agent

        agent = build_classify_agent()
        assert agent is not None
        assert agent.name == "ClassifyAgent"  # type: ignore[union-attr]
        assert agent.output_key == RcaSessionState.CLASSIFY_RESULT  # type: ignore[union-attr]

    @patch("app.agents.forecast_agent.build_mcp_toolset")
    def test_build_forecast_agent(self, mock_toolset: MagicMock) -> None:
        mock_toolset.return_value = self._mock_mcp_toolset()
        from app.agents.forecast_agent import build_forecast_agent

        agent = build_forecast_agent()
        assert agent is not None
        assert agent.name == "ForecastAgent"  # type: ignore[union-attr]
        assert agent.output_key == RcaSessionState.FORECAST_RESULT  # type: ignore[union-attr]

    @patch("app.agents.remediate_agent.build_mcp_toolset")
    def test_build_remediate_agent(self, mock_toolset: MagicMock) -> None:
        mock_toolset.return_value = self._mock_mcp_toolset()
        from app.agents.remediate_agent import build_remediate_agent

        agent = build_remediate_agent()
        assert agent is not None
        assert agent.name == "RemediateAgent"  # type: ignore[union-attr]
        assert agent.output_key == RcaSessionState.REMEDIATE_RESULT  # type: ignore[union-attr]


class TestPipelineAssembly:
    @patch("app.agents.detect_agent.build_mcp_toolset")
    @patch("app.agents.diagnose_agent.build_mcp_toolset")
    @patch("app.agents.classify_agent.build_mcp_toolset")
    @patch("app.agents.forecast_agent.build_mcp_toolset")
    @patch("app.agents.remediate_agent.build_mcp_toolset")
    def test_pipeline_has_five_agents(
        self,
        m1: MagicMock,
        m2: MagicMock,
        m3: MagicMock,
        m4: MagicMock,
        m5: MagicMock,
    ) -> None:
        for m in [m1, m2, m3, m4, m5]:
            m.return_value = MagicMock()

        from app.agents.pipeline import build_rca_pipeline

        pipeline = build_rca_pipeline()
        assert pipeline is not None
        assert pipeline.name == "RcaSentinelPipeline"
        assert len(pipeline.sub_agents) == 5  # type: ignore[arg-type]


# ── Callback / Guardrail Tests ───────────────────────────────────────


class TestCallbacks:
    def _make_callback_context(self, agent_name: str = "TestAgent") -> MagicMock:
        ctx = MagicMock()
        ctx.agent_name = agent_name
        ctx.invocation_id = "inv-001"
        return ctx

    def _make_llm_response(self, text: str) -> MagicMock:
        from google.genai import types

        part = types.Part(text=text)
        content = types.Content(role="model", parts=[part])
        response = MagicMock()
        response.content = content
        return response

    def test_before_agent_callback_runs(self) -> None:
        ctx = self._make_callback_context("DetectAgent")
        # Should not raise; just logs
        before_agent_callback(ctx)

    def test_after_model_callback_grounded_response_passes(self) -> None:
        ctx = self._make_callback_context("DiagnoseAgent")
        response = self._make_llm_response(
            "Based on lot-40921 and station-03b data, the root cause is confirmed."
        )
        result = after_model_callback(ctx, response)
        # Grounded response with entity IDs — should pass through unchanged (None)
        assert result is None

    def test_after_model_callback_pii_scrubbed(self) -> None:
        ctx = self._make_callback_context("DiagnoseAgent")
        response = self._make_llm_response(
            "Technician john.doe@example.com performed maintenance on station-03b."
        )
        result = after_model_callback(ctx, response)
        # Email should be scrubbed → returns a new LlmResponse
        assert result is not None
        scrubbed_text = result.content.parts[0].text
        assert "john.doe@example.com" not in scrubbed_text
        assert "[REDACTED]" in scrubbed_text
        assert "station-03b" in scrubbed_text

    def test_after_model_callback_empty_response_passthrough(self) -> None:
        ctx = self._make_callback_context("DetectAgent")
        empty_response = MagicMock()
        empty_response.content = None
        result = after_model_callback(ctx, empty_response)
        assert result is None


# ── Eval Assertion Tests ─────────────────────────────────────────────


class TestEvalAssertions:
    """Test that the golden scenario eval assertions work against synthetic data."""

    def test_assert_detect_result_pass(self) -> None:
        detect_result = {
            "incident_confirmed": True,
            "machine_context": {"id": "station-03b", "line": "line-03"},
            "anomaly_summary": "Scrap rate spiked to 13.4% vs baseline 1.2%.",
            "recommended_next_step": "Proceed to root cause diagnosis.",
        }
        assert_detect_result(detect_result)  # Should not raise

    def test_assert_detect_result_fail_not_confirmed(self) -> None:
        with pytest.raises(AssertionError, match="confirm"):
            assert_detect_result({"incident_confirmed": False})

    def test_assert_diagnose_result_pass(self) -> None:
        diagnose_result = {
            "primary_cause": {
                "type": "mechanical_miscalibration",
                "entity_id": "wo-8821",
                "description": "Spindle offset 0.035mm exceeded tolerance.",
                "confidence": 0.96,
            },
            "compounding_causes": [{"type": "supplier_material", "entity_id": "lot-40921"}],
            "culprit_lot_id": "lot-40921",
            "culprit_crew": "Maintenance Crew B",
            "hypothesis_summary": "Compound failure: miscalibration + out-of-spec alloy lot.",
            "evidence_ids": ["wo-8821", "lot-40921"],
        }
        assert_diagnose_result(diagnose_result)  # Should not raise

    def test_assert_diagnose_result_fail_wrong_lot(self) -> None:
        with pytest.raises(AssertionError, match="40921"):
            assert_diagnose_result(
                {
                    "primary_cause": {"confidence": 0.90},
                    "culprit_lot_id": "lot-99999",
                    "evidence_ids": ["e1", "e2"],
                }
            )

    def test_assert_classify_result_pass(self) -> None:
        classify_result = {
            "failure_modes": [
                {"id": "fm-001", "name": "Spindle Runout", "total_rpn": 360}
            ],
            "classification_codes": ["ISO22400-PF-01", "PFMEA-M-MACH-007"],
            "iso_category": "compound",
            "highest_rpn_mode": "Spindle Runout",
            "classification_confidence": 0.92,
        }
        assert_classify_result(classify_result)  # Should not raise

    def test_assert_forecast_result_pass(self) -> None:
        forecast_result = {
            "total_affected_units": GOLDEN_AFFECTED_UNITS,
            "downstream_lots_count": 2,
            "quarantine_candidates": ["lot-40921", "lot-62933"],
            "financial_forecast": {"material_scrap_usd": 161700.0},
            "gross_impact_usd": GOLDEN_GROSS_IMPACT_USD + 10000,
            "net_projected_loss_usd": 80000.0,
            "estimated_supplier_chargeback_usd": 105000.0,
            "containment_urgency": "immediate",
        }
        assert_forecast_result(forecast_result)  # Should not raise

    def test_assert_remediate_result_pass(self) -> None:
        remediate_result = {
            "proposed_actions": [
                {"id": "ACT-INT-001", "action_type": "interlock", "requires_human_approval": True},
                {"id": "ACT-ERP-001", "action_type": "erp_reroute", "requires_human_approval": True},
                {"id": "ACT-CMMS-001", "action_type": "maintenance_order", "requires_human_approval": True},
            ],
            "actions_pending_approval": 3,
            "remediation_summary": "Three containment actions proposed; all pending operations manager approval.",
            "8d_report_stub": {
                "D3_containment": "Interlock station-03b; quarantine lot-40921",
                "D5_corrective_action": "Recalibrate spindle bearing; audit AlloyTech Global supply",
                "D6_verification_plan": "CMM runout measurement + 7-day scrap rate monitoring",
            },
        }
        assert_remediate_result(remediate_result)  # Should not raise

    def test_assert_remediate_result_fail_no_approval(self) -> None:
        with pytest.raises(AssertionError, match="human approval"):
            assert_remediate_result(
                {
                    "proposed_actions": [
                        {"id": "ACT-001", "requires_human_approval": False},
                        {"id": "ACT-002", "requires_human_approval": True},
                    ],
                    "actions_pending_approval": 1,
                    "remediation_summary": "test",
                    "8d_report_stub": {
                        "D3_containment": "x",
                        "D5_corrective_action": "y",
                    },
                }
            )

    def test_assert_full_evidence_package_golden_scenario(self) -> None:
        """Integration eval: simulate a complete golden scenario evidence package."""
        evidence_package = {
            "incident_id": "INC-20261010-001",
            "pipeline": "RcaSentinelPipeline",
            "stages": {
                "detect": {
                    "incident_confirmed": True,
                    "machine_context": {"id": "station-03b"},
                    "anomaly_summary": "Scrap rate spike detected.",
                    "recommended_next_step": "Diagnose root cause.",
                },
                "diagnose": {
                    "primary_cause": {
                        "type": "compound_failure",
                        "entity_id": "wo-8821",
                        "description": "Miscalibrated spindle + out-of-spec alloy",
                        "confidence": 0.96,
                    },
                    "compounding_causes": [],
                    "culprit_lot_id": "lot-40921",
                    "culprit_crew": "Maintenance Crew B",
                    "hypothesis_summary": "Compound failure.",
                    "evidence_ids": ["wo-8821", "lot-40921", "log-001"],
                },
                "classify": {
                    "failure_modes": [{"id": "fm-001", "name": "Spindle Runout", "total_rpn": 360}],
                    "classification_codes": ["ISO22400-PF-01"],
                    "iso_category": "compound",
                    "highest_rpn_mode": "Spindle Runout",
                    "classification_confidence": 0.92,
                },
                "forecast": {
                    "total_affected_units": 420,
                    "downstream_lots_count": 2,
                    "quarantine_candidates": ["lot-40921"],
                    "financial_forecast": {},
                    "gross_impact_usd": 200000.0,
                    "net_projected_loss_usd": 100000.0,
                    "estimated_supplier_chargeback_usd": 100000.0,
                    "containment_urgency": "immediate",
                },
                "remediate": {
                    "proposed_actions": [
                        {"id": "ACT-INT-001", "action_type": "interlock", "requires_human_approval": True},
                        {"id": "ACT-ERP-001", "action_type": "erp_reroute", "requires_human_approval": True},
                    ],
                    "actions_pending_approval": 2,
                    "remediation_summary": "Two actions pending approval.",
                    "8d_report_stub": {
                        "D3_containment": "Interlock station-03b",
                        "D5_corrective_action": "Recalibrate spindle",
                        "D6_verification_plan": "Monitor scrap rate",
                    },
                },
            },
        }
        assert_full_evidence_package(evidence_package)  # Should not raise — all stages pass
