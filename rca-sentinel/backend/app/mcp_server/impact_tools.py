"""Impact and root cause analysis MCP tools."""

from __future__ import annotations

from typing import Any

from app.graph.analysis.backward import BackwardAnalysisEngine
from app.graph.analysis.financial import FinancialForecaster
from app.graph.analysis.forward import BlastRadiusAnalyzer

_backward = BackwardAnalysisEngine()
_blast = BlastRadiusAnalyzer()


async def diagnose_root_cause(
    line_id: str = "line-03",
    machine_id: str = "station-03b",
) -> dict[str, Any]:
    """Execute backward multi-hop diagnostic analysis to identify primary and compounding root causes.

    Args:
        line_id: Production line experiencing scrap anomaly (e.g. 'line-03').
        machine_id: Machine station under investigation (e.g. 'station-03b').

    Returns:
        Dict containing suspicious maintenance events (out-of-spec calibration offsets),
        culprit upstream material lots (silicon excess), operator log corroboration,
        and generated root cause hypotheses with confidence scores.
    """
    return await _backward.analyze_incident(line_id=line_id, machine_id=machine_id)


async def calculate_blast_radius(
    culprit_lot_id: str = "lot-40921",
    machine_id: str = "station-03b",
) -> dict[str, Any]:
    """Perform forward propagation analysis to determine contaminated inventory and affected units.

    Args:
        culprit_lot_id: Culprit material lot ID identified by diagnostic traversal.
        machine_id: Culprit machine ID.

    Returns:
        Dict containing total affected unit count, downstream assembly lots in flight,
        and inventory quarantine candidates.
    """
    return await _blast.compute_blast_radius(
        culprit_lot_id=culprit_lot_id, machine_id=machine_id
    )


async def forecast_financial_impact(
    scrapped_units: int = 420,
    downtime_hours: float = 2.0,
) -> dict[str, Any]:
    """Model financial exposure from scrapped precision components and assembly line downtime.

    Args:
        scrapped_units: Total units contaminated or scrapped.
        downtime_hours: Duration of assembly line stoppage in hours.

    Returns:
        Itemized cost forecast including material scrap cost, line downtime loss,
        inspection overhead, and supplier warranty chargeback recovery.
    """
    return FinancialForecaster.calculate_forecast(
        scrapped_units=scrapped_units, downtime_hours=downtime_hours
    )
