"""Tests for Phase 4: MCP Server, Graph Queries, Impact Analysis, and Action Tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from app.graph.analysis.backward import BackwardAnalysisEngine
from app.graph.analysis.financial import FinancialForecaster
from app.graph.analysis.forward import BlastRadiusAnalyzer
from app.graph.queries.traversal import GraphTraversalQueries
from app.mcp_server.action_tools import (
    propose_cmms_work_order,
    propose_equipment_interlock,
    propose_erp_quarantine,
)
from app.mcp_server.graph_tools import (
    get_machine_subgraph,
    trace_lot_provenance,
)
from app.mcp_server.impact_tools import (
    calculate_blast_radius,
    diagnose_root_cause,
    forecast_financial_impact,
)
from app.mcp_server.resources import (
    get_ontology_summary,
)
from app.mcp_server.server import mcp


# ── Traversal Query Tests ───────────────────────────────────────────


class TestGraphTraversal:
    @pytest.mark.asyncio
    async def test_trace_lot_provenance(self) -> None:
        mock_client = AsyncMock()
        mock_client.execute_read = AsyncMock(
            return_value=[
                {
                    "provenance": {
                        "target_lot": {"id": "lot-62933"},
                        "upstream_lots": [
                            {"id": "lot-51804", "supplier": {"name": "Precision Stampings"}},
                            {"id": "lot-40921", "supplier": {"name": "AlloyTech Global"}},
                        ],
                        "total_hops": 2,
                    }
                }
            ]
        )
        traversal = GraphTraversalQueries(client=mock_client)

        result = await traversal.trace_lot_provenance("lot-62933")
        assert result["target_lot"]["id"] == "lot-62933"
        assert len(result["upstream_lots"]) == 2
        assert result["total_hops"] == 2

    @pytest.mark.asyncio
    async def test_get_machine_subgraph(self) -> None:
        mock_client = AsyncMock()
        mock_client.execute_read = AsyncMock(
            return_value=[
                {
                    "neighborhood": {
                        "machine": {"id": "station-03b", "name": "Station B"},
                        "sensors": [{"id": "s1"}],
                        "maintenance_events": [{"id": "wo-8821"}],
                        "operator_logs": [{"id": "log-1"}],
                        "processed_lots": [{"id": "lot-62933"}],
                    }
                }
            ]
        )
        traversal = GraphTraversalQueries(client=mock_client)

        result = await traversal.get_machine_subgraph("station-03b")
        assert result["machine"]["id"] == "station-03b"
        assert len(result["sensors"]) == 1
        assert len(result["maintenance_events"]) == 1


# ── Backward & Forward Analysis Tests ───────────────────────────────


class TestBackwardAnalysis:
    @pytest.mark.asyncio
    async def test_diagnose_golden_scenario_compound_cause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        engine = BackwardAnalysisEngine()

        # Mock machine neighborhood query
        mock_machine_data = [
            {
                "data": {
                    "machine": {"id": "station-03b"},
                    "maintenance_events": [
                        {
                            "id": "wo-8821",
                            "title": "Spindle Bearing Replacement",
                            "technician_name": "Marcus Vance",
                            "crew_name": "Maintenance Crew B",
                            "calibration_offset_mm": 0.035,
                            "tolerance_limit_mm": 0.010,
                            "notes": "Calibration offset set to +0.035mm due to gauge drift.",
                        }
                    ],
                    "operator_logs": [
                        {"id": "log-1", "text": "Spindle felt warm after bearing swap, slight hum."}
                    ],
                    "processed_lots": [{"id": "lot-62933"}],
                }
            }
        ]

        # Mock upstream provenance chain query
        mock_chain_data = [
            {
                "chain": {
                    "target": {"id": "lot-62933"},
                    "upstream_lots": [
                        {
                            "id": "lot-40921",
                            "lot_number": "LOT-40921",
                            "material_type": "AlSi10Mg_ingot",
                            "supplier": {"id": "sup-tier3-001", "name": "AlloyTech Global", "tier": 3},
                            "properties_json": json.dumps({"silicon_content_pct": 1.82, "out_of_spec": True}),
                        }
                    ],
                }
            }
        ]

        async def fake_execute_read(query: str, params: dict | None = None) -> list[dict]:
            if "HAS_MAINTENANCE_EVENT" in query:
                return mock_machine_data
            return mock_chain_data

        mock_client = AsyncMock()
        mock_client.execute_read = AsyncMock(side_effect=fake_execute_read)
        engine = BackwardAnalysisEngine(client=mock_client)

        result = await engine.analyze_incident(line_id="line-03", machine_id="station-03b")
        assert len(result["suspicious_maintenance"]) == 1
        assert result["suspicious_maintenance"][0]["calibration_offset_mm"] == 0.035

        assert len(result["culprit_lots"]) == 1
        assert result["culprit_lots"][0]["properties"]["silicon_content_pct"] == 1.82

        assert len(result["hypotheses"]) > 0
        compound_hyp = result["hypotheses"][0]
        assert compound_hyp["type"] == "compound_failure"
        assert compound_hyp["confidence"] >= 0.95
        assert "AlloyTech Global" in str(compound_hyp)


class TestBlastRadius:
    @pytest.mark.asyncio
    async def test_compute_blast_radius(self, monkeypatch: pytest.MonkeyPatch) -> None:
        analyzer = BlastRadiusAnalyzer()
        mock_blast_records = [
            {
                "blast": {
                    "culprit_lot": {"id": "lot-40921", "lot_number": "LOT-40921"},
                    "downstream_lots": [
                        {
                            "id": "lot-51804",
                            "lot_number": "LOT-51804",
                            "properties_json": json.dumps({"affected_units_count": 220}),
                        },
                        {
                            "id": "lot-62933",
                            "lot_number": "LOT-62933",
                            "properties_json": json.dumps({"affected_units_count": 200}),
                        },
                    ],
                    "total_downstream_lots": 2,
                }
            }
        ]
        mock_client = AsyncMock()
        mock_client.execute_read = AsyncMock(return_value=mock_blast_records)
        analyzer = BlastRadiusAnalyzer(client=mock_client)

        result = await analyzer.compute_blast_radius("lot-40921", "station-03b")
        assert result["total_affected_units"] == 420
        assert len(result["quarantine_candidates"]) == 3  # culprit + 2 downstream
        assert result["containment_action_required"] is True


class TestFinancialForecaster:
    def test_forecast_values(self) -> None:
        forecast = FinancialForecaster.calculate_forecast(scrapped_units=420, downtime_hours=2.0)
        assert forecast["scrapped_units"] == 420
        assert forecast["itemized_costs"]["material_scrap_usd"] == 420 * 385.00
        assert forecast["itemized_costs"]["line_downtime_usd"] == 25000.00
        assert forecast["gross_impact_usd"] > 180000.00
        assert forecast["estimated_supplier_chargeback_usd"] > 100000.00
        assert forecast["net_projected_loss_usd"] < forecast["gross_impact_usd"]


# ── Action Proposal Tools Tests ─────────────────────────────────────


class TestActionProposalTools:
    @pytest.mark.asyncio
    async def test_propose_interlock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.mcp_server.action_tools import _incident_repo

        mock_propose = AsyncMock(
            return_value={
                "id": "ACT-INT-123",
                "action_type": "interlock",
                "status": "pending_approval",
                "requires_human_approval": True,
            }
        )
        monkeypatch.setattr(_incident_repo, "propose_action", mock_propose)

        action = await propose_equipment_interlock(
            machine_id="station-03b",
            reason="Thermal runaway and excessive spindle vibration",
            incident_id="INC-20261010-01",
        )
        assert action["requires_human_approval"] is True
        assert action["status"] == "pending_approval"
        assert action["action_type"] == "interlock"

    @pytest.mark.asyncio
    async def test_propose_erp_quarantine(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.mcp_server.action_tools import _incident_repo

        mock_propose = AsyncMock(
            return_value={
                "id": "ACT-ERP-123",
                "action_type": "erp_reroute",
                "status": "pending_approval",
                "requires_human_approval": True,
            }
        )
        monkeypatch.setattr(_incident_repo, "propose_action", mock_propose)

        action = await propose_erp_quarantine(
            lot_id="lot-40921",
            reason="Out-of-spec silicon content",
            incident_id="INC-20261010-01",
        )
        assert action["requires_human_approval"] is True

    @pytest.mark.asyncio
    async def test_propose_cmms_work_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.mcp_server.action_tools import _incident_repo

        mock_propose = AsyncMock(
            return_value={
                "id": "ACT-CMMS-123",
                "action_type": "maintenance_order",
                "status": "pending_approval",
                "requires_human_approval": True,
            }
        )
        monkeypatch.setattr(_incident_repo, "propose_action", mock_propose)

        action = await propose_cmms_work_order(
            machine_id="station-03b",
            title="Spindle Runout Recalibration",
            description="Laser alignment and bearing pre-load check",
            incident_id="INC-20261010-01",
        )
        assert action["requires_human_approval"] is True


# ── FastMCP Server Integration Tests ────────────────────────────────


class TestMcpServer:
    @pytest.mark.asyncio
    async def test_tools_registered(self) -> None:
        # FastMCP instance should have registered tools
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "get_machine_subgraph" in tool_names
        assert "trace_lot_provenance" in tool_names
        assert "diagnose_root_cause" in tool_names
        assert "calculate_blast_radius" in tool_names
        assert "forecast_financial_impact" in tool_names
        assert "propose_equipment_interlock" in tool_names
        assert "propose_erp_quarantine" in tool_names
        assert "propose_cmms_work_order" in tool_names

    @pytest.mark.asyncio
    async def test_ontology_resource(self) -> None:
        summary = await get_ontology_summary()
        assert "Plant" in summary["classes"]
        assert "Machine" in summary["classes"]
        assert "CONTAINS_MACHINE" in summary["relationships"]
