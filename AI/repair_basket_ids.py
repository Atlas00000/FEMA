#!/usr/bin/env python3
"""Repair pre-v1.23 AI CSVs where basket_id reset to 1 every basket.

Assigns sequential basket_id by open_time order (1..N) so offline AI can skip uniquely.
Also rewrites train/validate splits + full dataset from the repaired baskets.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from build_dataset import build_rows, write_csv  # noqa: E402
from csv_util import read_csv_rows  # noqa: E402


def parse_time(s: str) -> datetime:
    return datetime.strptime(s.strip(), "%Y.%m.%d %H:%M:%S")


def repair_baskets(src: Path, dst: Path) -> list[dict]:
    rows = read_csv_rows(src)
    if not rows:
        raise SystemExit(f"empty baskets: {src}")
    rows.sort(key=lambda r: parse_time(r["open_time"]))
    fields = list(rows[0].keys())
    for i, row in enumerate(rows, start=1):
        row["basket_id"] = str(i)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return rows


def split_dataset(rows: list[dict], train_to: datetime, val_from: datetime, val_to: datetime):
    train, val, other = [], [], []
    for r in rows:
        t = parse_time(r["open_time"])
        if t <= train_to:
            train.append(r)
        elif val_from <= t <= val_to:
            val.append(r)
        else:
            other.append(r)
    return train, val, other


def metrics(rows: list[dict], deposit: float = 400.0) -> dict:
    if not rows:
        return {"n": 0, "net": 0.0, "pf": 0.0, "wr": 0.0, "bsl_rate": 0.0, "max_dd_pct": 0.0}
    profits = [float(r.get("profit", 0) or 0) for r in rows]
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
        "net": round(sum(profits), 2),
        "pf": round(pf, 4),
        "wr": round(len(wins) / len(rows), 4),
        "bsl_rate": round(bsl / len(rows), 4),
        "max_dd_pct": round(max_dd, 2),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--baskets",
        type=Path,
        default=Path("AI/data/EURUSD_20260707_baskets_2024_2026.csv"),
    )
    ap.add_argument("--out-dir", type=Path, default=Path("AI/data"))
    args = ap.parse_args()

    repaired_path = args.out_dir / "EURUSD_20260707_baskets_2024_2026_uid.csv"
    baskets = repair_baskets(args.baskets, repaired_path)

    labeled = build_rows(repaired_path, mae_fail=20.0)
    full_path = args.out_dir / "dataset_2024_2026.csv"
    write_csv(full_path, labeled)

    train_to = datetime(2025, 12, 31, 23, 59, 59)
    val_from = datetime(2026, 1, 1, 0, 0, 0)
    val_to = datetime(2026, 7, 31, 23, 59, 59)
    train, val, other = split_dataset(labeled, train_to, val_from, val_to)

    train_path = args.out_dir / "dataset_train_2024_2025.csv"
    val_path = args.out_dir / "dataset_validate_2026.csv"
    write_csv(train_path, train)
    write_csv(val_path, val)

    report = {
        "repaired_baskets": str(repaired_path).replace("\\", "/"),
        "unique_ids": len({r["basket_id"] for r in baskets}),
        "n": len(baskets),
        "train": metrics(train),
        "validate": metrics(val),
        "other": metrics(other),
        "all": metrics(labeled),
        "note": "Offline sequential IDs; EA v1.23+ logs real sequential basket_id on future collects.",
    }
    (args.out_dir / "basket_uid_repair.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    print(f"wrote {repaired_path}")
    print(f"wrote {full_path}")
    print(f"wrote {train_path} n={len(train)}")
    print(f"wrote {val_path} n={len(val)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
