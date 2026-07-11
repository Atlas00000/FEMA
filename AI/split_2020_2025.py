#!/usr/bin/env python3
"""Split a repaired AI0 baskets/dataset CSV into 2020-2025 train/holdout windows.

Default (guardrail build):
  train   2020.01.01 → 2023.12.31
  holdout 2024.01.01 → 2025.12.31
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
from repair_basket_ids import metrics, parse_time, repair_baskets  # noqa: E402


def split_rows(rows: list[dict], start: datetime, end: datetime) -> list[dict]:
    out = []
    for r in rows:
        t = parse_time(r["open_time"])
        if start <= t <= end:
            out.append(r)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="AI guardrail window split (2020-2025)")
    ap.add_argument(
        "--baskets",
        type=Path,
        default=Path("AI/data/EURUSD_baskets_2020_2025.csv"),
        help="Raw AI0 baskets CSV from tester (2020-2025 collect)",
    )
    ap.add_argument("--out-dir", type=Path, default=Path("AI/data"))
    ap.add_argument("--train-start", default="2020.01.01")
    ap.add_argument("--train-end", default="2023.12.31")
    ap.add_argument("--holdout-start", default="2024.01.01")
    ap.add_argument("--holdout-end", default="2025.12.31")
    ap.add_argument("--mae-fail", type=float, default=20.0)
    args = ap.parse_args()

    if not args.baskets.exists():
        print(
            f"ERROR: baskets not found: {args.baskets}\n"
            "Run PRODUCTION + InpUseAiEventLog on 2020.01.01→2025.12.31, copy Agent FEMA_AI/*_baskets.csv here.",
            file=sys.stderr,
        )
        return 1

    uid = args.out_dir / "EURUSD_baskets_2020_2025_uid.csv"
    repair_baskets(args.baskets, uid)
    labeled = build_rows(uid, mae_fail=args.mae_fail)
    full_path = args.out_dir / "dataset_2020_2025.csv"
    write_csv(full_path, labeled)

    def parse_day(s: str, eod: bool = False) -> datetime:
        parts = s.strip().replace("-", ".").split(".")
        y, m, day = int(parts[0]), int(parts[1]), int(parts[2])
        if eod:
            return datetime(y, m, day, 23, 59, 59)
        return datetime(y, m, day, 0, 0, 0)

    train = split_rows(labeled, parse_day(args.train_start), parse_day(args.train_end, True))
    hold = split_rows(
        labeled, parse_day(args.holdout_start), parse_day(args.holdout_end, True)
    )

    train_path = args.out_dir / "dataset_train_2020_2023.csv"
    hold_path = args.out_dir / "dataset_holdout_2024_2025.csv"
    write_csv(train_path, train)
    write_csv(hold_path, hold)

    first = labeled[0]["open_time"] if labeled else ""
    last = labeled[-1]["open_time"] if labeled else ""
    report = {
        "philosophy": "guardrails_not_gates",
        "source": str(args.baskets).replace("\\", "/"),
        "span": {"first": first, "last": last, "n": len(labeled)},
        "train_2020_2023": metrics(train),
        "holdout_2024_2025": metrics(hold),
        "all_2020_2025": metrics(labeled),
        "artifacts": {
            "uid_baskets": str(uid).replace("\\", "/"),
            "full": str(full_path).replace("\\", "/"),
            "train": str(train_path).replace("\\", "/"),
            "holdout": str(hold_path).replace("\\", "/"),
        },
        "guardrail_note": (
            "Build AI on train; score guardrail quality on holdout "
            "(bad-path precision, DD cut, pause/skip budget). "
            "Do not require beating live PRODUCTION 2026 demo metrics."
        ),
    }
    if labeled and not last.startswith("2025"):
        report["warning"] = (
            f"Last open_time is {last} — expected 2025 for a full 2020-2025 collect."
        )

    out_json = args.out_dir / "split_2020_2025_report.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
