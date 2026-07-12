"""Component scores 0-100 from certificate bands (health_v0)."""

from __future__ import annotations


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def score_higher_is_better(
    value: float,
    red_max: float,
    amber_min: float,
    green_min: float,
    green_target: float | None = None,
) -> float:
    """Map value where higher is better (e.g. PF, TP hit)."""
    if value >= (green_target if green_target is not None else green_min):
        return 100.0
    if value >= green_min:
        # between green_min and target
        hi = green_target if green_target is not None else green_min + 0.05
        if hi <= green_min:
            return 90.0
        return 85.0 + (value - green_min) / (hi - green_min) * 15.0
    if value >= amber_min:
        return 55.0 + (value - amber_min) / max(green_min - amber_min, 1e-9) * 30.0
    if value >= red_max * 0.5:  # soft floor below red_max
        # red_max is upper bound of red zone for "higher better" → value < amber_min
        return clamp(20.0 + (value - red_max * 0.5) / max(amber_min - red_max * 0.5, 1e-9) * 35.0)
    return clamp(value / max(red_max * 0.5, 1e-9) * 20.0)


def score_pf(pf: float, bands: dict) -> float:
    g = bands["green"]
    a = bands["amber"]
    r = bands["red"]
    target = None
    t = g.get("profit_factor_target")
    if isinstance(t, (list, tuple)) and len(t) >= 1:
        target = float(t[0])
    return score_higher_is_better(
        pf,
        red_max=float(r["profit_factor_max"]),
        amber_min=float(a["profit_factor_min"]),
        green_min=float(g["profit_factor_min"]),
        green_target=target,
    )


def score_tp_hit(rate: float, bands: dict) -> float:
    g = bands["green"]
    # reuse WR amber/red as proxy floors for TP hit
    a = bands["amber"]
    r = bands["red"]
    return score_higher_is_better(
        rate,
        red_max=float(r["win_rate_max"]),
        amber_min=float(a["win_rate_min"]),
        green_min=float(g["tp_hit_rate_min"]),
        green_target=float(g["tp_hit_rate_min"]) + 0.05,
    )


def score_ratio_band(
    ratio: float,
    green_lo: float,
    green_hi: float,
    amber_lo: float,
    amber_hi: float,
) -> float:
    """Score a ratio that is healthy inside a band (duration, frequency)."""
    if green_lo <= ratio <= green_hi:
        mid = 0.5 * (green_lo + green_hi)
        span = max(green_hi - green_lo, 1e-9)
        # peak at center
        return 90.0 + 10.0 * (1.0 - abs(ratio - mid) / (0.5 * span))
    if amber_lo <= ratio <= amber_hi:
        # distance from green edge
        if ratio < green_lo:
            return 55.0 + (ratio - amber_lo) / max(green_lo - amber_lo, 1e-9) * 30.0
        return 55.0 + (amber_hi - ratio) / max(amber_hi - green_hi, 1e-9) * 30.0
    # outside amber
    if ratio < amber_lo:
        return clamp(ratio / max(amber_lo, 1e-9) * 40.0)
    # ratio > amber_hi
    over = ratio / max(amber_hi, 1e-9)
    return clamp(40.0 / max(over, 1.0))


def score_duration(avg_bars: float, birth_avg: float, bands: dict) -> float:
    if birth_avg <= 0:
        return 75.0
    ratio = avg_bars / birth_avg
    g, a = bands["green"], bands["amber"]
    return score_ratio_band(
        ratio,
        float(g["avg_bars_alive_vs_birth_min"]),
        float(g["avg_bars_alive_vs_birth_max"]),
        float(a["avg_bars_alive_vs_birth_min"]),
        float(a["avg_bars_alive_vs_birth_max"]),
    )


def score_depth(avg_depth: float, birth_avg: float, bands: dict) -> float:
    """Lower depth vs birth is better; rising depth hurts."""
    if birth_avg <= 0:
        return 75.0
    ratio = avg_depth / birth_avg
    g, a, r = bands["green"], bands["amber"], bands["red"]
    g_max = float(g["avg_depth_vs_birth_max"])
    a_min = float(a["avg_depth_vs_birth_min"])
    a_max = float(a["avg_depth_vs_birth_max"])
    r_min = float(r["avg_depth_vs_birth_min"])
    if ratio <= g_max:
        return 100.0 if ratio <= 1.0 else 85.0 + (g_max - ratio) / max(g_max - 1.0, 1e-9) * 15.0
    if ratio <= a_max:
        return 55.0 + (a_max - ratio) / max(a_max - a_min, 1e-9) * 30.0
    if ratio <= r_min * 1.25:
        return clamp(20.0 + (r_min * 1.25 - ratio) / max(r_min * 0.25, 1e-9) * 35.0)
    return clamp(15.0 * (2.0 - min(ratio, 2.0)))


def score_mae_efficiency(avg_mae_abs: float, avg_mfe: float, bsl: float, bands: dict) -> float:
    """Blend MAE/BSL (lower better) with MFE coverage when MFE > 0."""
    g, r = bands["green"], bands["red"]
    mae_ratio = avg_mae_abs / bsl if bsl > 0 else 1.0
    green_max = float(g["mae_vs_bsl_max"])
    red_min = float(r["mae_vs_bsl_min"])
    if mae_ratio <= green_max:
        mae_score = 100.0 - (mae_ratio / max(green_max, 1e-9)) * 15.0
    elif mae_ratio >= red_min:
        mae_score = clamp(25.0 * (1.2 - min(mae_ratio, 1.2)) / 0.4)
    else:
        mae_score = 40.0 + (red_min - mae_ratio) / max(red_min - green_max, 1e-9) * 45.0

    if avg_mfe > 0 and avg_mae_abs > 0:
        eff = avg_mfe / (avg_mae_abs + avg_mfe)
        # 0.5 balanced → ~70; higher MFE share → better
        mfe_score = clamp(40.0 + eff * 60.0)
    else:
        mfe_score = 60.0
    return 0.7 * mae_score + 0.3 * mfe_score


def score_trade_frequency(bpd: float, birth_bpd: float, bands: dict) -> float:
    if birth_bpd <= 0:
        return 75.0
    ratio = bpd / birth_bpd
    g = bands["green"]
    return score_ratio_band(
        ratio,
        float(g["trade_freq_vs_birth_min"]),
        float(g["trade_freq_vs_birth_max"]),
        0.5,
        1.6,
    )


def score_spread(reject_rate: float | None, bands: dict) -> float:
    if reject_rate is None:
        return 75.0  # approve-by-default when events missing
    cap = float(bands["green"]["spread_reject_rate_max"])
    if reject_rate <= cap:
        return 100.0 - (reject_rate / max(cap, 1e-9)) * 15.0
    if reject_rate <= cap * 2:
        return 55.0 + (cap * 2 - reject_rate) / max(cap, 1e-9) * 30.0
    return clamp(40.0 * (0.2 - min(reject_rate, 0.2)) / 0.2)


def score_regime(adx_ok_share: float | None, bands: dict) -> float:
    if adx_ok_share is None:
        return 75.0
    lo = float(bands["green"].get("regime_adx_ok_min", 0.7))
    if adx_ok_share >= lo:
        return 85.0 + (adx_ok_share - lo) / max(1.0 - lo, 1e-9) * 15.0
    if adx_ok_share >= lo - 0.2:
        return 50.0 + (adx_ok_share - (lo - 0.2)) / 0.2 * 35.0
    return clamp(adx_ok_share / max(lo - 0.2, 1e-9) * 50.0)
