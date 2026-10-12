"""Severity scoring and impact calculation for detected anomalies."""

from __future__ import annotations

from typing import Any

from app.domain.enums import Severity


class SeverityCalculator:
    """Computes incident severity, blast radius estimate, and initial financial impact."""

    COST_PER_SCRAPPED_UNIT_USD: float = 385.0  # Precision engine block carrier
    HOURLY_DOWNTIME_COST_USD: float = 12500.0  # Line 3 assembly downtime

    @classmethod
    def compute_severity(
        cls,
        metric: str,
        value: float,
        baseline: float,
        details: dict[str, Any] | None = None,
    ) -> Severity:
        """Determine severity level based on metric deviation."""
        det = details or {}

        # 1. Scrap rate percentage
        if "SCRAP" in metric.upper():
            spike = value - baseline
            if spike >= 10.0 or value >= 12.0:
                return Severity.CRITICAL
            if spike >= 5.0 or value >= 6.0:
                return Severity.HIGH
            if spike >= 2.0 or value >= 3.0:
                return Severity.MEDIUM
            return Severity.LOW

        # 2. Vibration
        if "VIB" in metric.upper():
            ratio = value / max(0.1, baseline)
            if ratio >= 3.0 or value >= 3.5:
                return Severity.CRITICAL
            if ratio >= 2.0 or value >= 2.2:
                return Severity.HIGH
            return Severity.MEDIUM

        # 3. Temperature
        if "TEMP" in metric.upper():
            if value >= 80.0:
                return Severity.CRITICAL
            if value >= 65.0:
                return Severity.HIGH
            return Severity.MEDIUM

        # General score-based fallback
        score = float(det.get("score", 0.5))
        if score >= 0.85:
            return Severity.CRITICAL
        if score >= 0.65:
            return Severity.HIGH
        if score >= 0.40:
            return Severity.MEDIUM
        return Severity.LOW

    @classmethod
    def estimate_financial_impact(
        cls,
        severity: Severity,
        affected_units: int = 420,
        estimated_downtime_hours: float = 2.0,
    ) -> float:
        """Estimate initial financial exposure from scrapped units and line downtime."""
        scrap_cost = affected_units * cls.COST_PER_SCRAPPED_UNIT_USD
        downtime_cost = estimated_downtime_hours * cls.HOURLY_DOWNTIME_COST_USD
        multiplier = 1.0
        if severity == Severity.CRITICAL:
            multiplier = 1.15  # expedited shipping & customer penalty
        return round((scrap_cost + downtime_cost) * multiplier, 2)
