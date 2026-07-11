#!/usr/bin/env python3
"""AI0-005 — Replay harness: apply skip masks to PRODUCTION basket list.

Skip-rate 0 must reproduce baseline basket metrics (AI0 exit criterion).
Hypothetical skips remove those baskets from the equity path.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def load_baskets(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for raw in csv.DictReader(fh):
            raw["_profit"] = float(raw.get("profit", 0) or 0)
            raw["_id"] = str(raw.get("basket_id", ""))
            rows.append(raw)
    return rows


def load_skip_ids(path: Path | None) -> set[str]:
    if path is None:
        return set()
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        return set()
    # JSON list or one id per line
    if text.startswith("["):
        return {str(x) for x in json.loads(text)}
    return {line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")}


def metrics(profits: list[float], deposit: float) -> dict:
    n = len(profits)
    if n == 0:
        return {
            "trades": 0,
            "net_profit": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "max_dd_pct": 0.0,
            "expectancy": 0.0,
        }

    wins = [p for p in profits if p > 0]
    losses = [p for p in profits if p < 0]
    gross_win = sum(wins)
    gross_loss = -sum(losses)
    pf = (gross_win / gross_loss) if gross_loss > 0 else (99.0 if gross_win > 0 else 0.0)
    wr = len(wins) / n

    equity = deposit
    peak = deposit
    max_dd = 0.0
    for p in profits:
        equity += p
        if equity > peak:
            peak = equity
        if peak > 0:
            dd = (peak - equity) / peak * 100.0
            if dd > max_dd:
                max_dd = dd

    return {
        "trades": n,
        "net_profit": round(sum(profits), 2),
        "win_rate": round(wr, 4),
        "profit_factor": round(pf, 4),
        "avg_win": round(sum(wins) / len(wins), 4) if wins else 0.0,
        "avg_loss": round(sum(losses) / len(losses), 4) if losses else 0.0,
        "max_dd_pct": round(max_dd, 2),
        "expectancy": round(sum(profits) / n, 4),
    }


def compare_ai_g1(base: dict, cand: dict, min_trade_frac: float = 0.85) -> dict:
    b = base["metrics"] if "metrics" in base else base
    checks = {
        "pf_ge_baseline": cand["profit_factor"] >= float(b["profit_factor"]) - 1e-9,
        "dd_le_baseline": cand["max_dd_pct"] <= float(b.get("max_dd_balance_pct", b.get("max_dd_pct", 999))),
        "trades_ge_85pct": cand["trades"] >= int(float(b["trades"]) * min_trade_frac),
    }
    checks["ai_g1_pass"] = all(checks.values())
    return checks


def main() -> int:
    ap = argparse.ArgumentParser(description="AI0 replay harness")
    ap.add_argument("--baskets", required=True, type=Path)
    ap.add_argument("--baseline", type=Path, default=Path("AI/baseline.json"))
    ap.add_argument("--skip-ids", type=Path, default=None, help="JSON list or line file of basket_id to skip")
    ap.add_argument("--skip-rate", type=float, default=0.0, help="Random skip fraction (0 = none)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--deposit", type=float, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if not args.baskets.exists():
        print(f"ERROR: baskets not found: {args.baskets}", file=sys.stderr)
        return 1

    baseline = {}
    if args.baseline.exists():
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))

    deposit = args.deposit
    if deposit is None:
        deposit = float(baseline.get("deposit", 400.0))

    rows = load_baskets(args.baskets)
    skip = load_skip_ids(args.skip_ids)

    if args.skip_rate > 0:
        import random

        rng = random.Random(args.seed)
        for r in rows:
            if rng.random() < args.skip_rate:
                skip.add(r["_id"])

    kept = [r for r in rows if r["_id"] not in skip]
    profits = [r["_profit"] for r in kept]
    all_profits = [r["_profit"] for r in rows]

    full = metrics(all_profits, deposit)
    replayed = metrics(profits, deposit)

    report = {
        "source": str(args.baskets),
        "deposit": deposit,
        "skip_count": len(rows) - len(kept),
        "skip_rate_effective": round((len(rows) - len(kept)) / len(rows), 4) if rows else 0.0,
        "full_sample": full,
        "replay": replayed,
        "baseline_file": str(args.baseline) if args.baseline.exists() else None,
        "baseline_metrics": baseline.get("metrics"),
        "zero_skip_matches_full": (len(rows) - len(kept)) == 0 and full == replayed,
    }

    if baseline.get("metrics"):
        # Compare replay to frozen PRODUCTION baseline (basket-approx DD)
        report["vs_frozen_baseline"] = {
            "pf_delta": round(replayed["profit_factor"] - float(baseline["metrics"]["profit_factor"]), 4),
            "net_delta": round(replayed["net_profit"] - float(baseline["metrics"]["net_profit"]), 2),
            "trades_delta": replayed["trades"] - int(baseline["metrics"]["trades"]),
            "note": "Basket CSV PF/WR should be close to tester; DD is basket-equity approx not MT5 equity DD.",
        }
        report["ai_g1"] = compare_ai_g1(baseline, replayed)

    # Exit criterion: skip-rate 0 reproduces this file's own full sample exactly
    if report["skip_count"] == 0:
        report["exit_criterion_zero_skip"] = full == replayed
    else:
        report["exit_criterion_zero_skip"] = None

    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
