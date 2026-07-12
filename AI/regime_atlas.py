#!/usr/bin/env python3
"""EC1 / AI1 — Coarse regime atlas (rule-based, offline, soft-skip).

Assigns each basket a regime, builds a scorecard (train/holdout time split),
and emits a permissive skip list (toxic regimes only, <=10% of baskets).

Soft-skip promotes only when train is toxic AND holdout confirms weakness.
Empty skip list is a valid EC1 outcome (atlas still useful for EC2 features).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path


from csv_util import read_csv_rows  # noqa: E402


REGIME_ORDER = [
    "late_session",
    "asia_open",
    "wide_spread",
    "high_adx",
    "expansion",
    "compression",
    "shallow_pullback",
    "grinding",
    "transition",
]


def parse_time(s: str) -> datetime:
    return datetime.strptime(s.strip(), "%Y.%m.%d %H:%M:%S")


def f(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except ValueError:
        return default


def metrics(rows: list[dict], deposit: float = 400.0) -> dict:
    if not rows:
        return {
            "n": 0,
            "pf": 0.0,
            "wr": 0.0,
            "net": 0.0,
            "bsl_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "max_dd_pct": 0.0,
            "dd_contrib_net": 0.0,
            "share": 0.0,
        }
    profits = [f(r, "profit") for r in rows]
    wins = [p for p in profits if p > 0]
    losses = [p for p in profits if p < 0]
    gw, gl = sum(wins), -sum(losses)
    pf = (gw / gl) if gl > 0 else (99.0 if gw > 0 else 0.0)
    bsl = sum(1 for r in rows if int(float(r.get("hit_bsl", 0) or 0)) == 1)
    equity = deposit
    peak = deposit
    max_dd = 0.0
    for p in profits:
        equity += p
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak * 100.0)
    return {
        "n": len(rows),
        "pf": round(pf, 4),
        "wr": round(len(wins) / len(rows), 4),
        "net": round(sum(profits), 2),
        "bsl_rate": round(bsl / len(rows), 4),
        "avg_win": round(sum(wins) / len(wins), 4) if wins else 0.0,
        "avg_loss": round(sum(losses) / len(losses), 4) if losses else 0.0,
        "max_dd_pct": round(max_dd, 2),
        "dd_contrib_net": round(sum(losses), 2),
    }


def assign_regime(row: dict, atr_p25: float, atr_p75: float) -> str:
    hour = int(f(row, "hour"))
    adx = f(row, "adx")
    atr = f(row, "atr")
    sep = abs(f(row, "ema_sep_atr"))
    slope = abs(f(row, "ema_slope"))
    spread = f(row, "spread_points")

    if hour in (21, 22, 23):
        return "late_session"
    if hour == 0:
        return "asia_open"
    if spread >= 12:
        return "wide_spread"
    if adx >= 27.0:
        return "high_adx"
    if sep >= 8.0 or (slope >= 0.00005 and atr >= atr_p75):
        return "expansion"
    if atr <= atr_p25:
        return "compression"
    if 15.0 <= adx < 27.0 and sep < 5.0:
        return "shallow_pullback"
    if slope <= 0.00002:
        return "grinding"
    return "transition"


def load_dataset(path: Path) -> list[dict]:
    rows = read_csv_rows(path)
    for i, r in enumerate(rows, start=1):
        r["_row_id"] = str(i)
        r["_ts"] = parse_time(r["open_time"])
    rows.sort(key=lambda r: r["_ts"])
    return rows


def scorecard_for(rows: list[dict], atr_p25: float, atr_p75: float, deposit: float = 400.0) -> dict:
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        reg = assign_regime(r, atr_p25, atr_p75)
        r["regime"] = reg
        by[reg].append(r)
    card = {}
    for name in REGIME_ORDER:
        card[name] = metrics(by.get(name, []), deposit)
        card[name]["share"] = round(len(by.get(name, [])) / len(rows), 4) if rows else 0.0
    card["_all"] = metrics(rows, deposit)
    return card


def soft_skip_holdout_report(hold: list[dict], toxic: list[str], deposit: float) -> dict:
    """EC1-005: soft-skip mask on holdout only (approve-by-default if toxic empty)."""
    if not hold:
        return {"n": 0, "skipped": 0, "kept": 0}
    skipped = [r for r in hold if r.get("regime") in toxic]
    kept = [r for r in hold if r.get("regime") not in toxic]
    base = metrics(hold, deposit)
    soft = metrics(kept, deposit)
    skip_m = metrics(skipped, deposit)
    # Bad-path precision: skipped baskets that lost or hit BSL
    bad = 0
    for r in skipped:
        if f(r, "profit") < 0 or int(float(r.get("hit_bsl", 0) or 0)) == 1:
            bad += 1
    precision = (bad / len(skipped)) if skipped else None
    net_avoided = skip_m["net"]  # <= 0 means skipped set was net damaging (good)
    return {
        "holdout_baseline": base,
        "holdout_soft_skip": soft,
        "skipped_set": skip_m,
        "skip_count": len(skipped),
        "skip_share": round(len(skipped) / len(hold), 4),
        "bad_path_precision": None if precision is None else round(precision, 4),
        "net_avoided": net_avoided,
        "trades_retained_pct": round(soft["n"] / base["n"], 4) if base["n"] else 0.0,
        "guardrail": {
            "skip_share_le_15pct": (len(skipped) / len(hold)) <= 0.15 + 1e-9,
            "net_avoided_le_0": net_avoided <= 0 + 1e-9 if skipped else True,
            "trades_ge_85pct": soft["n"] >= math.floor(base["n"] * 0.85),
            "approve_by_default_ok": len(toxic) == 0 or (
                (len(skipped) / len(hold)) <= 0.10 + 1e-9
                and (precision is None or precision >= 0.5)
            ),
        },
    }


def pick_toxic(
    train_card: dict,
    hold_card: dict,
    max_skip_share: float = 0.10,
    min_n_train: int = 5,
) -> tuple[list[str], list[dict]]:
    """Train toxic + holdout-confirmed weak. Returns (chosen, watchlist notes)."""
    watch = []
    candidates = []
    for name in REGIME_ORDER:
        tr = train_card[name]
        ho = hold_card[name]
        if tr["n"] < min_n_train:
            continue
        if not (tr["pf"] < 0.85 and tr["bsl_rate"] >= 0.35):
            continue
        note = {
            "regime": name,
            "train_pf": tr["pf"],
            "train_bsl": tr["bsl_rate"],
            "train_share": tr["share"],
            "hold_n": ho["n"],
            "hold_pf": ho["pf"],
        }
        if ho["n"] < 3:
            note["status"] = "watch_sparse_holdout"
            watch.append(note)
            continue
        if ho["pf"] >= 1.0:
            note["status"] = "watch_holdout_recovered"
            watch.append(note)
            continue
        note["status"] = "toxic_candidate"
        watch.append(note)
        candidates.append((name, tr["pf"], tr["share"], tr["bsl_rate"]))

    candidates.sort(key=lambda x: (x[1], -x[3]))
    chosen = []
    share = 0.0
    for name, pf, sh, bsl in candidates:
        if share + sh > max_skip_share + 1e-9:
            continue
        chosen.append(name)
        share += sh
    return chosen, watch


def holdout_hurt_notes(train_card: dict, hold_card: dict, min_n_hold: int = 20) -> list[dict]:
    """Descriptive only — holdout-weak regimes that were NOT train-toxic (no soft-skip)."""
    notes = []
    for name in REGIME_ORDER:
        tr, ho = train_card[name], hold_card[name]
        if ho["n"] < min_n_hold:
            continue
        if ho["pf"] >= 0.85:
            continue
        train_toxic = tr["n"] >= 5 and tr["pf"] < 0.85 and tr["bsl_rate"] >= 0.35
        if train_toxic:
            continue
        notes.append(
            {
                "regime": name,
                "status": "holdout_hurt_not_train_toxic",
                "train_pf": tr["pf"],
                "train_bsl": tr["bsl_rate"],
                "train_share": tr["share"],
                "hold_n": ho["n"],
                "hold_pf": ho["pf"],
                "hold_bsl": ho["bsl_rate"],
                "hold_net": ho["net"],
                "action": "do_not_soft_skip — feed EC2 as feature context only",
            }
        )
    return notes


def main() -> int:
    ap = argparse.ArgumentParser(description="EC1 regime atlas")
    ap.add_argument("--dataset", type=Path, default=Path("AI/data/dataset_2020_2025.csv"))
    ap.add_argument("--out-dir", type=Path, default=Path("AI/data"))
    ap.add_argument("--holdout-frac", type=float, default=0.35,
                    help="Used only if --validate-from is not set")
    ap.add_argument("--validate-from", type=str, default="2024.01.01",
                    help="YYYY.MM.DD — rows on/after this date are holdout")
    ap.add_argument("--validate-to", type=str, default="2025.12.31",
                    help="YYYY.MM.DD optional end of holdout window")
    ap.add_argument("--max-skip-share", type=float, default=0.10)
    ap.add_argument("--deposit", type=float, default=1000.0,
                    help="For DD% only; collect deposit may differ from demo $400")
    args = ap.parse_args()

    rows = load_dataset(args.dataset)
    n = len(rows)

    if args.validate_from:
        v0 = datetime.strptime(args.validate_from, "%Y.%m.%d")
        v1 = datetime.strptime(args.validate_to, "%Y.%m.%d") if args.validate_to else datetime(9999, 12, 31)
        train = [r for r in rows if r["_ts"] < v0]
        hold = [r for r in rows if v0 <= r["_ts"] <= v1.replace(hour=23, minute=59, second=59)]
    else:
        split = max(1, int(n * (1.0 - args.holdout_frac)))
        train, hold = rows[:split], rows[split:]

    atrs = sorted(f(r, "atr") for r in train)
    atr_p25 = atrs[int(0.25 * (len(atrs) - 1))]
    atr_p75 = atrs[int(0.75 * (len(atrs) - 1))]

    for r in rows:
        r["regime"] = assign_regime(r, atr_p25, atr_p75)

    train_card = scorecard_for(train, atr_p25, atr_p75, args.deposit)
    hold_card = scorecard_for(hold, atr_p25, atr_p75, args.deposit)
    full_card = scorecard_for(rows, atr_p25, atr_p75, args.deposit)

    toxic, watch = pick_toxic(train_card, hold_card, max_skip_share=args.max_skip_share)
    hurt = holdout_hurt_notes(train_card, hold_card)
    skip_ids = [r["_row_id"] for r in rows if r["regime"] in toxic]
    kept = [r for r in rows if r["regime"] not in toxic]

    base = metrics(rows, args.deposit)
    soft = metrics(kept, args.deposit)
    hold_soft = soft_skip_holdout_report(hold, toxic, args.deposit)
    gate = {
        "skip_share_le_10pct": (len(skip_ids) / n if n else 0.0) <= args.max_skip_share + 1e-9,
        "pf_ge_baseline": soft["pf"] >= base["pf"] - 1e-9,
        "dd_le_baseline": soft["max_dd_pct"] <= base["max_dd_pct"] + 1e-9,
        "trades_ge_90pct": soft["n"] >= math.floor(base["n"] * 0.90),
    }
    gate["ec1_exit_pass"] = all(gate.values()) and all(hold_soft.get("guardrail", {}).values())
    # legacy alias
    gate["ai1_exit_pass"] = gate["ec1_exit_pass"]

    if not toxic:
        verdict = (
            "No holdout-confirmed toxic regime within 10% skip budget. "
            "Atlas is descriptive; soft-skip list empty (approve-by-default)."
        )
    else:
        verdict = f"Soft-skip toxic regimes (shadow only): {toxic}."

    report = {
        "phase": "EC1-REGIME",
        "philosophy": "guardrails_not_gates",
        "split": {
            "train": {"start": "2020.01.01", "end": "2023.12.31"},
            "holdout": {"start": args.validate_from, "end": args.validate_to or "open"},
        },
        "n_baskets": n,
        "train_n": len(train),
        "hold_n": len(hold),
        "thresholds": {"atr_p25": atr_p25, "atr_p75": atr_p75},
        "regimes": REGIME_ORDER,
        "scorecard_full": full_card,
        "scorecard_train": train_card,
        "scorecard_holdout": hold_card,
        "toxic_regimes": toxic,
        "watchlist": watch,
        "holdout_hurt_notes": hurt,
        "skip_count": len(skip_ids),
        "skip_share": round(len(skip_ids) / n, 4) if n else 0.0,
        "baseline_replay": base,
        "soft_skip_replay": soft,
        "holdout_soft_skip": hold_soft,
        "gate_checks": gate,
        "verdict": verdict,
        "deposit_note": "Deposit used only for DD%; ignore vs demo $400 sizing.",
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    score_path = args.out_dir / "regime_scorecard.json"
    skip_path = args.out_dir / "regime_skip_ids.txt"
    labeled_path = args.out_dir / "dataset_with_regime.csv"
    md_path = args.out_dir / "regime_scorecard.md"

    score_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    skip_path.write_text("\n".join(skip_ids) + ("\n" if skip_ids else ""), encoding="utf-8")

    out_fields = [
        "row_id", "basket_id", "open_time", "symbol", "direction", "open_level",
        "ema_fast", "ema_trend", "ema_sep", "ema_sep_atr", "ema_slope", "atr", "adx",
        "grid_center", "dist_ema_trend_atr", "spread_points", "hour", "dow",
        "roll_wr", "roll_pf", "roll_n", "close_time", "profit", "exit_reason",
        "hit_tp", "hit_bsl", "mae", "mfe", "bars_alive", "max_depth", "y_fail", "regime",
    ]
    with labeled_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=out_fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            row = {k: r.get(k, "") for k in out_fields}
            row["row_id"] = r["_row_id"]
            w.writerow(row)

    hs = hold_soft
    lines = [
        "# EC1 Regime Scorecard (2020–2025 contain)",
        "",
        f"Baskets: **{n}** | train {len(train)} (2020–2023) / holdout {len(hold)} (2024–2025)",
        f"ATR thresholds (train): p25={atr_p25:.6f} | p75={atr_p75:.6f}",
        f"Toxic soft-skip: **{toxic or 'none'}** | full skip share {report['skip_share']:.1%}",
        "",
        report["verdict"],
        "",
        "## Full sample",
        "",
        "| Regime | N | Share | PF | WR | BSL% | Net |",
        "| ------ | - | ----- | -- | -- | ---- | --- |",
    ]
    for name in REGIME_ORDER:
        c = full_card[name]
        lines.append(
            f"| {name} | {c['n']} | {c['share']:.1%} | {c['pf']:.2f} | "
            f"{c['wr']:.1%} | {c['bsl_rate']:.1%} | {c['net']:.1f} |"
        )
    lines += [
        "",
        "## Train vs holdout",
        "",
        "| Regime | Train n/PF/BSL/share | Hold n/PF/BSL |",
        "| ------ | -------------------- | ------------- |",
    ]
    for name in REGIME_ORDER:
        tr, ho = train_card[name], hold_card[name]
        if tr["n"] == 0 and ho["n"] == 0:
            continue
        lines.append(
            f"| {name} | {tr['n']}/{tr['pf']:.2f}/{tr['bsl_rate']:.0%}/{tr['share']:.0%} | "
            f"{ho['n']}/{ho['pf']:.2f}/{ho['bsl_rate']:.0%} |"
        )
    hb, hsft = hs["holdout_baseline"], hs["holdout_soft_skip"]
    lines += [
        "",
        "## Soft-skip replay (full sample)",
        "",
        f"- Baseline: PF {base['pf']:.2f} | net {base['net']:.1f} | n {base['n']}",
        f"- Soft-skip: PF {soft['pf']:.2f} | net {soft['net']:.1f} | n {soft['n']}",
        "",
        "## Soft-skip replay (holdout — EC1-005)",
        "",
        f"- Holdout baseline: PF {hb['pf']:.2f} | net {hb['net']:.1f} | n {hb['n']}",
        f"- After soft-skip: PF {hsft['pf']:.2f} | net {hsft['net']:.1f} | n {hsft['n']}",
        f"- Skip share (holdout): {hs['skip_share']:.1%} | bad-path precision: {hs['bad_path_precision']}",
        f"- Net of skipped set: {hs['net_avoided']:.1f} (want ≤0)",
        f"- Guardrail: `{json.dumps(hs['guardrail'])}`",
        f"- Gates: `{json.dumps(gate)}`",
        "",
        "## Watchlist",
        "",
    ]
    if watch:
        for witem in watch:
            lines.append(
                f"- `{witem['regime']}` | {witem['status']} | "
                f"train PF {witem['train_pf']:.2f} BSL {witem['train_bsl']:.0%} | "
                f"hold n={witem['hold_n']} PF {witem['hold_pf']:.2f}"
            )
    else:
        lines.append("- none")
    lines += [
        "",
        "## Holdout-hurt (not soft-skipped)",
        "",
        "Regimes weak on holdout but **not** train-toxic — approve by default; useful as EC2 context.",
        "",
    ]
    if hurt:
        for hitem in hurt:
            lines.append(
                f"- `{hitem['regime']}` | hold n={hitem['hold_n']} PF {hitem['hold_pf']:.2f} "
                f"BSL {hitem['hold_bsl']:.0%} net {hitem['hold_net']:.1f} | "
                f"train PF {hitem['train_pf']:.2f} BSL {hitem['train_bsl']:.0%} | {hitem['action']}"
            )
    else:
        lines.append("- none")
    lines += [
        "",
        "## Policy",
        "",
        "- Approve by default.",
        "- Skip only holdout-confirmed toxic regimes (<=10% train share budget).",
        "- Offline / shadow only — not wired to EA.",
        "- Grade PF/WR/BSL — deposit elevated for collect continuity only.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "phase": "EC1-REGIME",
        "toxic_regimes": toxic,
        "skip_share": report["skip_share"],
        "gate_checks": gate,
        "verdict": report["verdict"],
        "watchlist": watch,
        "holdout_hurt_notes": hurt,
        "holdout_soft_skip": {
            "skip_share": hs["skip_share"],
            "bad_path_precision": hs["bad_path_precision"],
            "net_avoided": hs["net_avoided"],
            "guardrail": hs["guardrail"],
            "baseline_pf": hb["pf"],
            "soft_pf": hsft["pf"],
        },
        "artifacts": {
            "scorecard": str(score_path),
            "markdown": str(md_path),
            "skip_ids": str(skip_path),
            "labeled": str(labeled_path),
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
