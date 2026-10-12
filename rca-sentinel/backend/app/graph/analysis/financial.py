"""Financial impact forecast model for manufacturing quality incidents."""

from __future__ import annotations

from typing import Any


class FinancialForecaster:
    """Calculates financial exposure across scrapped material, line downtime, and rework."""

    UNIT_COST_USD: float = 385.00
    HOURLY_LINE_DOWNTIME_USD: float = 12500.00
    INSPECTION_OVERHEAD_PER_UNIT_USD: float = 24.50

    @classmethod
    def calculate_forecast(
        cls,
        scrapped_units: int = 420,
        downtime_hours: float = 2.0,
        quarantined_wip_units: int = 180,
    ) -> dict[str, Any]:
        """Compute comprehensive itemized financial impact model."""
        scrap_cost = scrapped_units * cls.UNIT_COST_USD
        downtime_cost = downtime_hours * cls.HOURLY_LINE_DOWNTIME_USD
        inspection_cost = (scrapped_units + quarantined_wip_units) * cls.INSPECTION_OVERHEAD_PER_UNIT_USD

        gross_impact = scrap_cost + downtime_cost + inspection_cost

        # Supplier warranty recovery estimation (Tier 3 supplier out-of-spec chargeback)
        supplier_claimable = round(scrap_cost * 0.65, 2)
        net_impact = round(gross_impact - supplier_claimable, 2)

        return {
            "scrapped_units": scrapped_units,
            "downtime_hours": downtime_hours,
            "itemized_costs": {
                "material_scrap_usd": round(scrap_cost, 2),
                "line_downtime_usd": round(downtime_cost, 2),
                "metrology_inspection_usd": round(inspection_cost, 2),
            },
            "gross_impact_usd": round(gross_impact, 2),
            "estimated_supplier_chargeback_usd": supplier_claimable,
            "net_projected_loss_usd": net_impact,
        }
