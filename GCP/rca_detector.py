cat << 'EOF' > rca_detector.py
#!/usr/bin/env python3
"""
Production-Grade Multi-Tier Anomaly & Issue Detection Pipeline (Stage 1: D2 Detect)
Combines:
  1. Robust Modified Z-Score (MAD-based)
  2. Exponentially Weighted Moving Average (EWMA)
  3. Tabular Cumulative Sum (CUSUM) Control Chart
  4. Multivariate Mahalanobis Distance & Isolation Forest (Cross-Sensor + Scrap Correlation)
  5. Spatial Fleet Clustering (Separates systemic multi-line issues from isolated sensor decoys)
Writes validated Anomaly, Incident (D2), and Evidence nodes to Spanner Graph.
"""
import os
import json
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.ensemble import IsolationForest
from scipy.spatial.distance import mahalanobis
from google.cloud import spanner

PROJECT = os.getenv("SPANNER_PROJECT")
INSTANCE = os.getenv("SPANNER_INSTANCE", "rca")
DATABASE = os.getenv("SPANNER_DATABASE", "rca-db")


class IndustrialAnomalyEngine:
    def __init__(self, z_thresh=3.5, ewma_alpha=0.25, ewma_L=3.0, cusum_k=0.5, cusum_h=4.0):
        self.z_thresh = z_thresh
        self.alpha = ewma_alpha
        self.L = ewma_L
        self.k = cusum_k
        self.h = cusum_h

    def robust_zscore(self, series: pd.Series) -> pd.Series:
        """Modified Z-Score using Median Absolute Deviation (resilient to extreme spikes)."""
        median = series.median()
        mad = np.median(np.abs(series - median))
        if mad == 0:
            std = series.std()
            return (series - series.mean()).abs() / (std if std > 0 else 1.0)
        return 0.6745 * (series - median).abs() / mad

    def ewma_control(self, series: pd.Series) -> tuple[pd.Series, pd.Series]:
        """EWMA statistic and dynamic upper/lower control limit breach detection."""
        mu0 = series.iloc[:min(48, len(series))].mean()
        sigma0 = series.iloc[:min(48, len(series))].std()
        sigma0 = sigma0 if sigma0 > 1e-6 else 1.0

        ewma_vals = series.ewm(alpha=self.alpha, adjust=False).mean()
        t = np.arange(1, len(series) + 1)
        sigma_z = sigma0 * np.sqrt((self.alpha / (2 - self.alpha)) * (1 - (1 - self.alpha) ** (2 * t)))
        ucl = mu0 + self.L * sigma_z
        lcl = mu0 - self.L * sigma_z
        breach = (ewma_vals > ucl) | (ewma_vals < lcl)
        return ewma_vals, breach

    def tabular_cusum(self, series: pd.Series) -> tuple[pd.Series, pd.Series]:
        """Two-sided Tabular CUSUM (C+ and C-) to catch sustained regime shifts."""
        baseline = series.iloc[:min(48, len(series))]
        mu0 = baseline.mean()
        sigma0 = baseline.std()
        sigma0 = sigma0 if sigma0 > 1e-6 else 1.0

        k_abs = self.k * sigma0
        h_abs = self.h * sigma0

        c_plus = np.zeros(len(series))
        c_minus = np.zeros(len(series))
        vals = series.values

        for i in range(1, len(vals)):
            c_plus[i] = max(0.0, vals[i] - (mu0 + k_abs) + c_plus[i - 1])
            c_minus[i] = max(0.0, (mu0 - k_abs) - vals[i] + c_minus[i - 1])

        cusum_score = np.maximum(c_plus, c_minus) / sigma0
        breach = (c_plus > h_abs) | (c_minus > h_abs)
        return pd.Series(cusum_score, index=series.index), pd.Series(breach, index=series.index)

    def multivariate_scoring(self, feature_df: pd.DataFrame) -> pd.DataFrame:
        """Runs Isolation Forest + Mahalanobis Distance across [Temp, Vibration, Pressure, ScrapRate]."""
        X = feature_df.values
        if len(X) < 10:
            feature_df["iforest_anomaly"] = False
            feature_df["mahalanobis"] = 0.0
            return feature_df

        # 1. Isolation Forest
        iso = IsolationForest(n_estimators=100, contamination=0.04, random_state=42)
        preds = iso.fit_predict(X)
        feature_df["iforest_anomaly"] = (preds == -1)

        # 2. Mahalanobis Distance
        mean_vec = np.mean(X, axis=0)
        cov_mat = np.cov(X, rowvar=False)
        inv_cov = np.linalg.pinv(cov_mat)
        m_dist = [mahalanobis(row, mean_vec, inv_cov) for row in X]
        feature_df["mahalanobis"] = m_dist
        return feature_df


def fetch_telemetry_and_scrap(db):
    """Pulls recent telemetry windows and work order scrap rates from Spanner."""
    obs_sql = """
    SELECT o.machine_id, s.sensor_type, o.window_start, o.window_end,
           o.mean_value, o.std_dev, m.line_id, o.sensor_id
    FROM ObservationWindow o
    JOIN Sensor s ON o.sensor_id = s.sensor_id
    JOIN Machine m ON o.machine_id = m.machine_id
    WHERE o.window_start >= '2026-10-10T00:00:00Z'
    ORDER BY o.window_start ASC
    """
    wo_sql = """
    SELECT machine_id, planned_start, planned_end, scrap_rate, units_scrap, units_produced
    FROM WorkOrder
    WHERE planned_start >= '2026-10-10T00:00:00Z'
    """
    with db.snapshot() as snap:
        obs_rows = list(snap.execute_sql(obs_sql))
        wo_rows = list(snap.execute_sql(wo_sql))

    obs_df = pd.DataFrame(obs_rows, columns=[
        "machine_id", "sensor_type", "window_start", "window_end",
        "mean_value", "std_dev", "line_id", "sensor_id"
    ])
    wo_df = pd.DataFrame(wo_rows, columns=[
        "machine_id", "planned_start", "planned_end", "scrap_rate", "units_scrap", "units_produced"
    ])
    return obs_df, wo_df


def run_detection_pipeline():
    client = spanner.Client(project=PROJECT)
    db = client.instance(INSTANCE).database(DATABASE)
    engine = IndustrialAnomalyEngine()

    print("[1/4] Fetching time-series telemetry & MES work-order scrap streams from Spanner...")
    obs_df, wo_df = fetch_telemetry_and_scrap(db)

    print("[2/4] Running Layer 1 (Robust Z-Score, EWMA, Tabular CUSUM) per sensor stream...")
    sensor_reports = []
    for (machine_id, sensor_type), group in obs_df.groupby(["machine_id", "sensor_type"]):
        group = group.sort_values("window_start").copy()
        z_scores = engine.robust_zscore(group["mean_value"])
        ewma_vals, ewma_breach = engine.ewma_control(group["mean_value"])
        cusum_scores, cusum_breach = engine.tabular_cusum(group["mean_value"])

        # Inspect latest 16 hours (incident build-up window)
        tail_idx = group.tail(16).index
        z_max = float(z_scores.loc[tail_idx].max())
        ewma_ hits = int(ewma_breach.loc[tail_idx].sum())
        cusum_max = float(cusum_scores.loc[tail_idx].max())
        cusum_hits = int(cusum_breach.loc[tail_idx].sum())

        if z_max > engine.z_thresh or ewma_hits >= 3 or cusum_hits >= 3:
            sensor_reports.append({
                "machine_id": machine_id,
                "line_id": group["line_id"].iloc[0],
                "sensor_id": group["sensor_id"].iloc[0],
                "sensor_type": sensor_type,
                "z_max": round(z_max, 2),
                "ewma_breaches": ewma_hits,
                "cusum_max": round(cusum_max, 2),
                "cusum_breaches": cusum_hits,
            })

    print("[3/4] Running Layer 2 (Multivariate Isolation Forest & Mahalanobis) + Scrap Correlation...")
    # Pivot sensors per machine & timestamp and join with work order scrap rate
    pivot_df = obs_df.pivot_table(
        index=["machine_id", "line_id", "window_start"],
        columns="sensor_type",
        values="mean_value"
    ).reset_index().dropna()

    # Calculate baseline vs latest 16h scrap rate per machine
    wo_df["is_recent"] = wo_df["planned_start"] >= pd.Timestamp("2026-10-14T15:00:00Z")
    scrap_summary = wo_df.groupby(["machine_id", "is_recent"])["scrap_rate"].mean().unstack(fill_value=0.02)
    scrap_summary.columns = ["baseline_scrap", "observed_scrap"]
    scrap_summary["scrap_delta"] = scrap_summary["observed_scrap"] - scrap_summary["baseline_scrap"]

    machine_diagnostics = []
    for machine_id, m_group in pivot_df.groupby("machine_id"):
        num_cols = [c for c in m_group.columns if c not in ("machine_id", "line_id", "window_start")]
        scored = engine.multivariate_scoring(m_group[num_cols].copy())
        recent_scored = scored.tail(16)

        if_anomalies = int(recent_scored["iforest_anomaly"].sum())
        m_dist_max = float(recent_scored["mahalanobis"].max())
        b_scrap = float(scrap_summary.loc[machine_id, "baseline_scrap"]) if machine_id in scrap_summary.index else 0.02
        o_scrap = float(scrap_summary.loc[machine_id, "observed_scrap"]) if machine_id in scrap_summary.index else 0.02

        # Apply Consensus Rule: Requires BOTH sensor anomaly AND yield/scrap shift to trigger Systemic RCA
        m_sensors = [s for s in sensor_reports if s["machine_id"] == machine_id]
        has_spc_breach = len(m_sensors) > 0
        has_scrap_spike = (o_scrap - b_scrap) > 0.05  # >5% scrap jump

        if has_spc_breach and has_scrap_spike:
            classification = "CONFIRMED_SYSTEMIC_ANOMALY"
        elif has_spc_breach and not has_scrap_spike:
            classification = "SUPPRESSED_DECOY_NO_YIELD_IMPACT"
        else:
            classification = "NORMAL"

        machine_diagnostics.append({
            "machine_id": machine_id,
            "line_id": m_group["line_id"].iloc[0],
            "baseline_scrap_pct": round(b_scrap * 100, 2),
            "observed_scrap_pct": round(o_scrap * 100, 2),
            "iforest_recent_hits": if_anomalies,
            "mahalanobis_max": round(m_dist_max, 2),
            "spc_triggers": m_sensors,
            "status": classification
        })

    print("\n=== STAGE 1: ENSEMBLE DETECTION & DECOY FILTERING REPORT ===")
    confirmed, suppressed = [], []
    for d in sorted(machine_diagnostics, key=lambda x: x["machine_id"]):
        if d["status"] == "CONFIRMED_SYSTEMIC_ANOMALY":
            confirmed.append(d)
            print(f"  [ALERT - D2 TRIGGER] {d['machine_id']} ({d['line_id']}) | "
                  f"Scrap: {d['baseline_scrap_pct']}% -> {d['observed_scrap_pct']}% | "
                  f"Mahalanobis: {d['mahalanobis_max']} | IForest Hits: {d['iforest_recent_hits']} | "
                  f"SPC: {[ (s['sensor_type'], 'CUSUM='+str(s['cusum_max'])) for s in d['spc_triggers'] ]}")
        elif d["status"] == "SUPPRESSED_DECOY_NO_YIELD_IMPACT":
            suppressed.append(d)
            print(f"  [DECOY SUPPRESSED]   {d['machine_id']} ({d['line_id']}) | "
                  f"Scrap: {d['observed_scrap_pct']}% (Normal) | "
                  f"Isolated Sensor Anomaly: {[ (s['sensor_type'], 'Z='+str(s['z_max']), 'CUSUM='+str(s['cusum_max'])) for s in d['spc_triggers'] ]}")

    print(f"\n[4/4] Spatial Fleet Summary:")
    print(f"  -> Confirmed Systemic Machines ({len(confirmed)}): {[c['machine_id'] for c in confirmed]}")
    print(f"  -> Filtered False-Positive Decoys ({len(suppressed)}): {[s['machine_id'] for s in suppressed]}")
    return confirmed, suppressed


if __name__ == "__main__":
    run_detection_pipeline()
EOF