"""ASI-P1-02 — basket-open TEP features (no outcome leakage)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

OPEN_COLS = [
    "basket_id",
    "open_time",
    "symbol",
    "direction",
    "open_level",
    "ema_fast",
    "ema_trend",
    "ema_sep",
    "ema_sep_atr",
    "ema_slope",
    "atr",
    "adx",
    "grid_center",
    "dist_ema_trend_atr",
    "spread_points",
    "hour",
    "dow",
    "roll_wr",
    "roll_pf",
    "roll_n",
]

TEP_DERIVED = [
    "ema_slope_accel",
    "adx_accel",
    "atr_expansion_rate",
    "consecutive_same_dir",
    "dist_ema_abs",
    "impulse_score",
    # v1 interactions (ASI retune)
    "adx_x_atr_expand",
    "slope_x_consec",
    "impulse_x_dist",
]


def parse_open_time(s: str) -> datetime:
    return datetime.strptime(str(s).strip(), "%Y.%m.%d %H:%M:%S")


def _f(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def _safe_div(num: float, den: float, default: float = 0.0) -> float:
    if abs(den) < 1e-12:
        return default
    return num / den


def tep_derived(prev: dict | None, cur: dict) -> dict[str, float]:
    """Features knowable at basket open using prior basket open snapshots only."""
    ema_slope = _f(cur, "ema_slope")
    adx = _f(cur, "adx")
    atr = _f(cur, "atr")
    dist = _f(cur, "dist_ema_trend_atr")
    direction = str(cur.get("direction", "") or "").upper()

    if prev is None:
        ema_slope_accel = 0.0
        adx_accel = 0.0
        atr_expansion_rate = 0.0
        consecutive_same_dir = 1
    else:
        ema_slope_accel = ema_slope - _f(prev, "ema_slope")
        adx_accel = adx - _f(prev, "adx")
        prev_atr = _f(prev, "atr")
        atr_expansion_rate = _safe_div(atr - prev_atr, prev_atr, 0.0)
        prev_dir = str(prev.get("direction", "") or "").upper()
        prev_run = int(float(prev.get("_consecutive_same_dir", 1) or 1))
        consecutive_same_dir = prev_run + 1 if prev_dir == direction and direction else 1

    dist_ema_abs = abs(dist)
    impulse_score = (
        abs(ema_slope_accel) * 1e4
        + max(0.0, adx_accel) * 2.0
        + max(0.0, atr_expansion_rate) * 10.0
        + consecutive_same_dir * 0.5
        + dist_ema_abs * 0.25
    )
    adx_x_atr_expand = max(0.0, adx_accel) * max(0.0, atr_expansion_rate)
    slope_x_consec = abs(ema_slope_accel) * 1e4 * consecutive_same_dir
    impulse_x_dist = impulse_score * dist_ema_abs

    return {
        "ema_slope_accel": round(ema_slope_accel, 8),
        "adx_accel": round(adx_accel, 4),
        "atr_expansion_rate": round(atr_expansion_rate, 6),
        "consecutive_same_dir": consecutive_same_dir,
        "dist_ema_abs": round(dist_ema_abs, 4),
        "impulse_score": round(impulse_score, 4),
        "adx_x_atr_expand": round(adx_x_atr_expand, 6),
        "slope_x_consec": round(slope_x_consec, 4),
        "impulse_x_dist": round(impulse_x_dist, 4),
    }


def tep_interactions(row: dict) -> dict[str, float]:
    """V1 interaction features (basket-open only)."""
    adx_a = _f(row, "adx_accel")
    atr_e = max(0.0, _f(row, "atr_expansion_rate"))
    slope_a = abs(_f(row, "ema_slope_accel"))
    dist = _f(row, "dist_ema_abs") or abs(_f(row, "dist_ema_trend_atr"))
    impulse = _f(row, "impulse_score")
    consec = _f(row, "consecutive_same_dir", 1.0)
    adx = _f(row, "adx")
    return {
        "adx_x_atr_expand": round(max(0.0, adx_a) * atr_e * 100.0, 6),
        "slope_x_dist": round(slope_a * 1e4 * dist, 6),
        "impulse_x_consec": round(impulse * consec, 4),
        "adx_level_x_accel": round(adx * max(0.0, adx_a), 4),
    }


TEP_INTERACTIONS = [
    "adx_x_atr_expand",
    "slope_x_dist",
    "impulse_x_consec",
    "adx_level_x_accel",
]


def build_open_features(rows: list[dict]) -> list[dict[str, Any]]:
    """Sort by open_time; attach TEP v0 derived fields at open (outcome cols kept separate)."""
    ordered = sorted(rows, key=lambda r: parse_open_time(r["open_time"]))
    out: list[dict[str, Any]] = []
    prev: dict | None = None
    for raw in ordered:
        row = {c: raw.get(c, "") for c in OPEN_COLS}
        derived = tep_derived(prev, raw)
        row.update(derived)
        prev = {**raw, "_consecutive_same_dir": derived["consecutive_same_dir"]}
        out.append(row)
    return out
