#!/usr/bin/env python3
"""AI3 — Edge health monitor (offline, soft pause ladder).

Rolling live-like metrics → health 0–100 → normal/caution/pause/suspend.
Approve by default; pause new baskets only when health is clearly degraded.
Calibrate pause floor on train (2024–2025); single eval on 2026 validate (AI-G1).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parent
import sys

if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from csv_util import read_csv_rows  # noqa: E402


def parse_time(s: str) -> datetime:
    return datetime.strptime(s.strip(), "%Y.%m.%d %H:%M:%S")


def f(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def load_dataset(path: Path) -> list[dict]:
    rows = read_csv_rows(path)
    rows.sort(key=lambda r: parse_time(r["open_time"]))
    return rows


def window_stats(rows: list[dict]) -> dict:
    if not rows:
        return {
            "n": 0,
            "pf": 1.0,
            "wr": 0.5,
            "expectancy": 0.0,
            "bsl_rate": 0.25,
            "avg_mae": 0.0,
            "net": 0.0,
        }
    profits = [f(r, "profit") for r in rows]
    wins = [p for p in profits if p > 0]
    losses = [p for p in profits if p < 0]
    gw, gl = sum(wins), -sum(losses)
    pf = (gw / gl) if gl > 0 else (99.0 if gw > 0 else 0.0)
    bsl = sum(1 for r in rows if int(float(r.get("hit_bsl", 0) or 0)) == 1)
    maes = [f(r, "mae") for r in rows]
    return {
        "n": len(rows),
        "pf": pf,
        "wr": len(wins) / len(rows),
        "expectancy": sum(profits) / len(rows),
        "bsl_rate": bsl / len(rows),
        "avg_mae": sum(maes) / len(maes),
        "net": sum(profits),
    }


def window_path_dd(rows: list[dict], deposit_unit: float = 100.0) -> float:
    """Max equity DD inside the rolling window only (stress clears after recovery)."""
    if not rows:
        return 0.0
    equity = deposit_unit
    peak = deposit_unit
    max_dd = 0.0
    for r in rows:
        equity += f(r, "profit")
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak * 100.0)
    cur_dd = ((peak - equity) / peak * 100.0) if peak > 0 else 0.0
    return max(max_dd, cur_dd)


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def score_pf(pf: float) -> float:
    # 1.30+ → 100; 1.10 → 75; 1.00 → 55; 0.90 → 35; 0.80 → 15
    if pf >= 1.30:
        return 100.0
    if pf >= 1.10:
        return 75.0 + (pf - 1.10) / 0.20 * 25.0
    if pf >= 1.00:
        return 55.0 + (pf - 1.00) / 0.10 * 20.0
    if pf >= 0.90:
        return 35.0 + (pf - 0.90) / 0.10 * 20.0
    if pf >= 0.80:
        return 15.0 + (pf - 0.80) / 0.10 * 20.0
    return clamp(pf / 0.80 * 15.0)


def score_wr(wr: float) -> float:
    # PRODUCTION basket WR ~0.71–0.78; collapse below 0.60 is bad
    if wr >= 0.75:
        return 100.0
    if wr >= 0.68:
        return 70.0 + (wr - 0.68) / 0.07 * 30.0
    if wr >= 0.60:
        return 40.0 + (wr - 0.60) / 0.08 * 30.0
    if wr >= 0.50:
        return 15.0 + (wr - 0.50) / 0.10 * 25.0
    return clamp(wr / 0.50 * 15.0)


def score_expectancy(exp: float) -> float:
    # ~+$2 basket expectancy healthy; 0 flat; negative sick
    if exp >= 2.0:
        return 100.0
    if exp >= 0.5:
        return 70.0 + (exp - 0.5) / 1.5 * 30.0
    if exp >= 0.0:
        return 45.0 + exp / 0.5 * 25.0
    if exp >= -2.0:
        return 20.0 + (exp + 2.0) / 2.0 * 25.0
    return clamp(10.0 + (exp + 5.0) / 3.0 * 10.0)


def score_bsl(bsl_rate: float) -> float:
    # ~0.23 validate baseline; rising fail share hurts
    if bsl_rate <= 0.20:
        return 100.0
    if bsl_rate <= 0.28:
        return 70.0 + (0.28 - bsl_rate) / 0.08 * 30.0
    if bsl_rate <= 0.35:
        return 40.0 + (0.35 - bsl_rate) / 0.07 * 30.0
    if bsl_rate <= 0.45:
        return 15.0 + (0.45 - bsl_rate) / 0.10 * 25.0
    return clamp(15.0 * (0.55 - bsl_rate) / 0.10)


def score_underwater(dd_pct: float) -> float:
    if dd_pct <= 5.0:
        return 100.0
    if dd_pct <= 12.0:
        return 75.0 + (12.0 - dd_pct) / 7.0 * 25.0
    if dd_pct <= 20.0:
        return 45.0 + (20.0 - dd_pct) / 8.0 * 30.0
    if dd_pct <= 35.0:
        return 20.0 + (35.0 - dd_pct) / 15.0 * 25.0
    return clamp(20.0 * (50.0 - dd_pct) / 15.0)


@dataclass
class HealthThresholds:
    high: float = 70.0
    medium: float = 50.0
    low: float = 35.0
    pause_dd: float = 12.0
    pause_bsl: float = 0.35
    # below low → critical


def action_from_health(health: float, thr: HealthThresholds) -> str:
    if health >= thr.high:
        return "high"
    if health >= thr.medium:
        return "medium"
    if health >= thr.low:
        return "low"
    return "critical"


def compute_health_series(
    rows: list[dict],
    window: int,
    deposit: float,
    thr: HealthThresholds,
    warmup: int | None = None,
    start_equity: float | None = None,
    start_peak: float | None = None,
    history_prefix: list[dict] | None = None,
) -> list[dict]:
    """Causal health at each basket open using prior closed baskets only.

    Optional history_prefix (e.g. end of train) seeds the rolling window without
    emitting health rows for those baskets. start_equity/peak carry path stress.
    """
    warm = warmup if warmup is not None else max(8, window // 2)
    equity = deposit if start_equity is None else start_equity
    peak = deposit if start_peak is None else start_peak
    prefix = list(history_prefix or [])
    out: list[dict] = []

    for i, row in enumerate(rows):
        # prior closed = prefix + rows[:i]
        prior = prefix + rows[:i]
        hist = prior[-window:] if prior else []
        st = window_stats(hist)
        roll_dd = window_path_dd(hist)
        # lifetime path dd kept for logging only
        dd_pct = ((peak - equity) / peak * 100.0) if peak > 0 else 0.0
        prior_n = len(prior)

        if prior_n < warm or st["n"] < min(warm, window):
            health = 75.0  # approve-by-default during warmup
            components = {
                "pf": 75.0,
                "wr": 75.0,
                "expectancy": 75.0,
                "bsl": 75.0,
                "underwater": score_underwater(roll_dd),
            }
        else:
            components = {
                "pf": score_pf(st["pf"]),
                "wr": score_wr(st["wr"]),
                "expectancy": score_expectancy(st["expectancy"]),
                "bsl": score_bsl(st["bsl_rate"]),
                "underwater": score_underwater(roll_dd),
            }
            health = (
                0.30 * components["pf"]
                + 0.25 * components["expectancy"]
                + 0.15 * components["wr"]
                + 0.15 * components["bsl"]
                + 0.15 * components["underwater"]
            )

        action = action_from_health(health, thr)
        # Soft pause = edge-stress confirm using *rolling* DD (not lifetime peak).
        neg_edge = st["n"] >= warm and st["expectancy"] < 0.0 and st["pf"] < 1.0
        rising_stress = roll_dd >= thr.pause_dd
        hot_fail = st["n"] >= warm and st["bsl_rate"] >= thr.pause_bsl
        pause = bool(neg_edge and (rising_stress or hot_fail))
        if action == "critical" and rising_stress and st["n"] >= warm and st["pf"] < 1.05:
            pause = True

        out.append(
            {
                "basket_id": str(row.get("basket_id", "")),
                "open_time": row.get("open_time", ""),
                "profit": f(row, "profit"),
                "hit_bsl": int(float(row.get("hit_bsl", 0) or 0)),
                "y_fail": int(float(row.get("y_fail", 0) or 0)),
                "health": round(health, 2),
                "action": action,
                "pause_new": int(pause),
                "roll_n": st["n"],
                "roll_pf": round(st["pf"], 4),
                "roll_wr": round(st["wr"], 4),
                "roll_exp": round(st["expectancy"], 4),
                "roll_bsl": round(st["bsl_rate"], 4),
                "roll_dd_pct": round(roll_dd, 2),
                "path_dd_pct": round(dd_pct, 2),
                "components": {k: round(v, 2) for k, v in components.items()},
            }
        )

        equity += f(row, "profit")
        peak = max(peak, equity)

    return out


def path_state(rows: list[dict], deposit: float) -> tuple[float, float]:
    equity = deposit
    peak = deposit
    for r in rows:
        equity += f(r, "profit")
        peak = max(peak, equity)
    return equity, peak


def equity_metrics(profits: list[float], deposit: float = 400.0) -> dict:
    n = len(profits)
    if n == 0:
        return {
            "n": 0,
            "net": 0.0,
            "pf": 0.0,
            "wr": 0.0,
            "bsl_rate": 0.0,
            "max_dd_pct": 0.0,
            "expectancy": 0.0,
        }
    wins = [p for p in profits if p > 0]
    losses = [p for p in profits if p < 0]
    gw, gl = sum(wins), -sum(losses)
    pf = (gw / gl) if gl > 0 else (99.0 if gw > 0 else 0.0)
    equity = deposit
    peak = deposit
    max_dd = 0.0
    for p in profits:
        equity += p
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak * 100.0)
    return {
        "n": n,
        "net": round(sum(profits), 2),
        "pf": round(pf, 4),
        "wr": round(len(wins) / n, 4),
        "max_dd_pct": round(max_dd, 2),
        "expectancy": round(sum(profits) / n, 4),
    }


def replay_with_pauses(
    rows: list[dict], series: list[dict], deposit: float, pause_actions: set[str] | None = None
) -> dict:
    """Replay using series pause_new flags (preferred) or action set fallback."""
    kept_profits = []
    paused = []
    for row, h in zip(rows, series):
        use_pause = bool(h.get("pause_new", 0))
        if pause_actions is not None and not use_pause:
            use_pause = h["action"] in pause_actions
        if use_pause:
            paused.append(h)
        else:
            kept_profits.append(f(row, "profit"))
    base = equity_metrics([f(r, "profit") for r in rows], deposit)
    kept = equity_metrics(kept_profits, deposit)
    pause_profits = [x["profit"] for x in paused]
    pause_net = round(sum(pause_profits), 2) if pause_profits else 0.0
    pause_fail = (
        sum(1 for x in paused if x["y_fail"] == 1) / len(paused) if paused else 0.0
    )
    pause_loser = (
        sum(1 for x in paused if x["profit"] < 0) / len(paused) if paused else 0.0
    )
    return {
        "baseline": base,
        "after_pause": kept,
        "pause_n": len(paused),
        "pause_rate": round(len(paused) / len(rows), 4) if rows else 0.0,
        "pause_net": pause_net,
        "pause_y_fail_rate": round(pause_fail, 4),
        "pause_loser_rate": round(pause_loser, 4),
        "paused_ids": [x["basket_id"] for x in paused],
    }


def ai_g1(base: dict, cand: dict, min_trade_frac: float = 0.85) -> dict:
    checks = {
        "pf_ge_baseline": cand["pf"] + 1e-12 >= float(base["pf"]),
        "dd_le_baseline": cand["max_dd_pct"] <= float(base["max_dd_pct"]) + 1e-9,
        "trades_ge_85pct": cand["n"] >= int(math.ceil(float(base["n"]) * min_trade_frac)),
        "wr_ge_baseline": cand["wr"] + 1e-12 >= float(base["wr"]),
    }
    checks["ai_g1_pass"] = (
        checks["pf_ge_baseline"] and checks["dd_le_baseline"] and checks["trades_ge_85pct"]
    )
    return checks


def worst_dd_episodes(rows: list[dict], deposit: float, top_k: int = 3) -> list[dict]:
    """Find start indices of deepest drawdown troughs (for catch analysis)."""
    equity = deposit
    peak = deposit
    events = []
    for i, row in enumerate(rows):
        equity += f(row, "profit")
        peak = max(peak, equity)
        dd = (peak - equity) / peak * 100.0 if peak > 0 else 0.0
        events.append({"i": i, "dd": dd, "open_time": row["open_time"], "equity": equity})
    # local troughs: dd higher than neighbors, take top_k by dd
    troughs = []
    for i in range(1, len(events) - 1):
        if events[i]["dd"] >= events[i - 1]["dd"] and events[i]["dd"] >= events[i + 1]["dd"]:
            if events[i]["dd"] >= 10.0:
                troughs.append(events[i])
    troughs.sort(key=lambda e: e["dd"], reverse=True)
    return troughs[:top_k]


def pause_before_trough(series: list[dict], trough_i: int, lookback: int = 15) -> bool:
    start = max(0, trough_i - lookback)
    return any(series[j]["pause_new"] == 1 for j in range(start, trough_i + 1))


def calibrate(
    train_rows: list[dict],
    deposit: float,
    windows: list[int],
    dd_grid: list[float],
    bsl_grid: list[float],
) -> tuple[dict, list[dict]]:
    """Pick window + pause stress floors on late-train cal (pause 5–20%)."""
    split = max(len(train_rows) // 2, len(train_rows) - 120)
    cal_rows = train_rows[split:]
    base_full = equity_metrics([f(r, "profit") for r in train_rows], deposit)
    candidates = []
    for window in windows:
        for pause_dd in dd_grid:
            for pause_bsl in bsl_grid:
                thr = HealthThresholds(pause_dd=pause_dd, pause_bsl=pause_bsl)
                prefix = train_rows[max(0, split - window) : split]
                eq, pk = path_state(train_rows[:split], deposit)
                cal_series = compute_health_series(
                    cal_rows,
                    window,
                    deposit,
                    thr,
                    start_equity=eq,
                    start_peak=pk,
                    history_prefix=prefix,
                )
                cal_rep = replay_with_pauses(cal_rows, cal_series, deposit)
                pause_rate = cal_rep["pause_rate"]
                if pause_rate < 0.03 or pause_rate > 0.25:
                    continue

                full_series = compute_health_series(train_rows, window, deposit, thr)
                full_rep = replay_with_pauses(train_rows, full_series, deposit)
                trade_frac = (
                    full_rep["after_pause"]["n"] / base_full["n"] if base_full["n"] else 0.0
                )
                # Train years are weak — allow heavier pause there; validate gate is what matters
                if trade_frac < 0.60:
                    continue
                dd_cut = base_full["max_dd_pct"] - full_rep["after_pause"]["max_dd_pct"]
                troughs = worst_dd_episodes(train_rows, deposit)
                catches = sum(1 for t in troughs if pause_before_trough(full_series, t["i"]))
                score = (
                    2.5 * dd_cut
                    + 55.0 * cal_rep["pause_y_fail_rate"]
                    + 25.0 * cal_rep["pause_loser_rate"]
                    + (20.0 if cal_rep["pause_net"] < 0 else -30.0)
                    - 25.0 * abs(pause_rate - 0.10)
                    + 10.0 * catches
                )
                candidates.append(
                    {
                        "window": window,
                        "thresholds": asdict(thr),
                        "score": round(score, 4),
                        "cal_pause_rate": pause_rate,
                        "cal_replay": {k: v for k, v in cal_rep.items() if k != "paused_ids"},
                        "train_replay": {k: v for k, v in full_rep.items() if k != "paused_ids"},
                        "dd_cut": round(dd_cut, 2),
                        "trade_frac": round(trade_frac, 4),
                        "trough_catch": {
                            "caught": catches,
                            "of": len(troughs),
                            "troughs": troughs,
                        },
                    }
                )
    candidates.sort(key=lambda c: c["score"], reverse=True)
    if not candidates:
        thr = HealthThresholds()
        series = compute_health_series(train_rows, 30, deposit, thr)
        rep = replay_with_pauses(train_rows, series, deposit)
        fallback = {
            "window": 30,
            "thresholds": asdict(thr),
            "score": 0.0,
            "cal_pause_rate": rep["pause_rate"],
            "train_replay": {k: v for k, v in rep.items() if k != "paused_ids"},
            "dd_cut": round(base_full["max_dd_pct"] - rep["after_pause"]["max_dd_pct"], 2),
            "trade_frac": round(rep["after_pause"]["n"] / max(base_full["n"], 1), 4),
            "trough_catch": {"caught": 0, "of": 0, "troughs": []},
            "note": "no candidate in pause budget — using defaults",
        }
        return fallback, [fallback]
    return candidates[0], candidates[:12]


def write_md(path: Path, report: dict) -> None:
    v = report["validate"]
    t = report["train"]
    lines = [
        "# AI3 — Edge health monitor report",
        "",
        f"**Status:** `{report['status']}`",
        f"**Window:** last **{report['window']}** baskets",
        f"**Pause rule:** neg roll edge (PF<1 & exp<0) + (DD≥{report['thresholds']['pause_dd']}% or BSL≥{report['thresholds']['pause_bsl']:.0%}); "
        f"or critical + DD stress",
        f"**Health bands:** high≥{report['thresholds']['high']} · "
        f"medium≥{report['thresholds']['medium']} · low≥{report['thresholds']['low']}",
        "",
        "## Validate 2026 Jan–Jul",
        "",
        f"- Pause rate: **{v['replay']['pause_rate']:.1%}** ({v['replay']['pause_n']} baskets)",
        f"- Pause y_fail rate: **{v['replay']['pause_y_fail_rate']:.1%}** · "
        f"loser rate: **{v['replay']['pause_loser_rate']:.1%}** · "
        f"net paused: **{v['replay']['pause_net']:+.2f}**",
        f"- PF {v['replay']['baseline']['pf']:.2f} → **{v['replay']['after_pause']['pf']:.2f}** · "
        f"DD {v['replay']['baseline']['max_dd_pct']:.1f}% → "
        f"**{v['replay']['after_pause']['max_dd_pct']:.1f}%** · "
        f"n {v['replay']['baseline']['n']} → {v['replay']['after_pause']['n']}",
        f"- AI-G1: **{'PASS' if v['ai_g1']['ai_g1_pass'] else 'FAIL'}**",
        "",
        "## Train 2024–2025 (calibration)",
        "",
        f"- Pause rate: {t['replay']['pause_rate']:.1%} · DD cut: {t['dd_cut']:.1f} pp · "
        f"trade frac: {t['trade_frac']:.1%}",
        f"- Worst-trough catch: {t['trough_catch']['caught']}/{t['trough_catch']['of']}",
        "",
        "## Soft ladder",
        "",
        "| Health | Action |",
        "| ------ | ------ |",
        "| High / Medium | Full PRODUCTION (health logged) |",
        "| Low | Caution flag — pause only with neg-edge confirm |",
        "| Critical + stress | Pause **new** baskets |",
        "",
        "Shadow only — do not wire until status is `promote_candidate`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="AI3 edge health monitor")
    ap.add_argument("--train", type=Path, default=Path("AI/data/dataset_train_2024_2025.csv"))
    ap.add_argument("--validate", type=Path, default=Path("AI/data/dataset_validate_2026.csv"))
    ap.add_argument("--deposit", type=float, default=400.0)
    ap.add_argument("--out-dir", type=Path, default=Path("AI/data"))
    args = ap.parse_args()

    train_rows = load_dataset(args.train)
    val_rows = load_dataset(args.validate)
    if not train_rows or not val_rows:
        raise SystemExit("empty train/validate")

    best, grid = calibrate(
        train_rows,
        args.deposit,
        windows=[15, 20, 25, 30],
        dd_grid=[40.0, 50.0, 60.0, 70.0, 80.0, 90.0],
        bsl_grid=[0.40, 0.50, 0.60, 0.99],
    )
    window = int(best["window"])
    thr = HealthThresholds(**best["thresholds"])

    train_series = compute_health_series(train_rows, window, args.deposit, thr)
    eq, pk = path_state(train_rows, args.deposit)
    val_series_warm = compute_health_series(
        val_rows,
        window,
        args.deposit,
        thr,
        start_equity=eq,
        start_peak=pk,
        history_prefix=train_rows[-window:],
    )

    train_rep = replay_with_pauses(train_rows, train_series, args.deposit)
    val_rep = replay_with_pauses(val_rows, val_series_warm, args.deposit)
    val_g1 = ai_g1(val_rep["baseline"], val_rep["after_pause"])

    troughs = worst_dd_episodes(train_rows, args.deposit)
    catches = sum(1 for t in troughs if pause_before_trough(train_series, t["i"]))

    pause_ok = (
        0.03 <= val_rep["pause_rate"] <= 0.20
        and val_rep["pause_n"] >= 3
        and (val_rep["pause_y_fail_rate"] >= 0.45 or val_rep["pause_net"] < 0)
    )
    if val_g1["ai_g1_pass"] and pause_ok and catches >= 1:
        status = "promote_candidate"
    elif val_g1["ai_g1_pass"]:
        status = "shadow_watch_g1_pass"
    elif pause_ok:
        status = "shadow_pauses_useful_g1_fail"
    else:
        status = "reject_shadow"

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # shadow log validate
    shadow_path = out_dir / "ai3_shadow.csv"
    with shadow_path.open("w", newline="", encoding="utf-8") as fh:
        fields = [
            "basket_id",
            "open_time",
            "health",
            "action",
            "pause_new",
            "roll_pf",
            "roll_wr",
            "roll_exp",
            "roll_bsl",
            "roll_dd_pct",
            "path_dd_pct",
            "y_fail",
            "hit_bsl",
            "profit",
        ]
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for h in val_series_warm:
            w.writerow({k: h.get(k, "") for k in fields})

    pause_ids = val_rep["paused_ids"]
    pause_path = out_dir / "ai3_pause_ids.txt"
    pause_path.write_text("\n".join(pause_ids) + ("\n" if pause_ids else ""), encoding="utf-8")

    report = {
        "phase": "AI3-HEALTH",
        "status": status,
        "window": window,
        "thresholds": asdict(thr),
        "pause_actions": "stress_confirm_pause_new",
        "pause_rule": (
            "(roll_exp<0 AND roll_pf<1.0 AND (roll_dd>=pause_dd OR roll_bsl>=pause_bsl)) "
            "OR (critical AND roll_dd>=pause_dd AND roll_pf<1.05)"
        ),
        "train": {
            "n": len(train_rows),
            "replay": {k: v for k, v in train_rep.items() if k != "paused_ids"},
            "dd_cut": round(
                train_rep["baseline"]["max_dd_pct"] - train_rep["after_pause"]["max_dd_pct"], 2
            ),
            "trade_frac": round(train_rep["after_pause"]["n"] / train_rep["baseline"]["n"], 4),
            "trough_catch": {"caught": catches, "of": len(troughs), "troughs": troughs},
        },
        "validate": {
            "n": len(val_rows),
            "warm_start_from_train": True,
            "replay": {k: v for k, v in val_rep.items() if k != "paused_ids"},
            "ai_g1": val_g1,
            "action_counts": {
                a: sum(1 for h in val_series_warm if h["action"] == a)
                for a in ("high", "medium", "low", "critical")
            },
        },
        "calibration_top": grid[:8],
        "artifacts": {
            "shadow": str(shadow_path).replace("\\", "/"),
            "pause_ids": str(pause_path).replace("\\", "/"),
        },
        "note": (
            "Health is causal (prior baskets only). Validate uses warm-start from end of train. "
            "Pause = skip new baskets while low/critical; medium still trades."
        ),
    }

    json_path = out_dir / "ai3_report.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path = out_dir / "ai3_report.md"
    write_md(md_path, report)

    print(
        f"AI3 status={status} | window={window} | "
        f"val pause={val_rep['pause_rate']:.1%} ({val_rep['pause_n']}) | "
        f"pause_yfail={val_rep['pause_y_fail_rate']:.1%} | "
        f"PF {val_rep['baseline']['pf']:.2f}->{val_rep['after_pause']['pf']:.2f} | "
        f"DD {val_rep['baseline']['max_dd_pct']:.1f}->{val_rep['after_pause']['max_dd_pct']:.1f} | "
        f"AI-G1={'PASS' if val_g1['ai_g1_pass'] else 'FAIL'} | "
        f"train trough catch {catches}/{len(troughs)}"
    )
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    print(f"wrote {shadow_path}")
    print(f"wrote {pause_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
