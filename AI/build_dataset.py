#!/usr/bin/env python3
"""AI0-004 — Build a labeled offline dataset from FEMA AI CSV logs.

Reads baskets.csv (+ optional events.csv) produced by InpUseAiEventLog.
Writes a clean features+labels CSV (and optional Parquet if pyarrow/pandas present).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from csv_util import read_csv_rows  # noqa: E402


FEATURE_COLS = [
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

LABEL_COLS = [
    "close_time",
    "profit",
    "exit_reason",
    "hit_tp",
    "hit_bsl",
    "mae",
    "mfe",
    "bars_alive",
    "max_depth",
    "y_fail",  # 1 if BSL or deep MAE
]


def _f(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except ValueError:
        return default


def build_rows(baskets_path: Path, mae_fail: float) -> list[dict]:
    rows: list[dict] = []
    for raw in read_csv_rows(baskets_path):
        hit_bsl = int(float(raw.get("hit_bsl", 0) or 0))
        mae = _f(raw, "mae")
        y_fail = 1 if hit_bsl == 1 or mae <= -abs(mae_fail) else 0
        out = {c: raw.get(c, "") for c in FEATURE_COLS + LABEL_COLS if c != "y_fail"}
        out["y_fail"] = y_fail
        rows.append(out)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = FEATURE_COLS + LABEL_COLS
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def maybe_parquet(path: Path, rows: list[dict]) -> None:
    try:
        import pandas as pd  # type: ignore
    except ImportError:
        return
    df = pd.DataFrame(rows)
    df.to_parquet(path, index=False)


def main() -> int:
    ap = argparse.ArgumentParser(description="AI0 dataset builder")
    ap.add_argument(
        "--baskets",
        required=True,
        type=Path,
        help="Path to *_baskets.csv from Common/Files/FEMA_AI/",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("AI/data/dataset.csv"),
        help="Output labeled CSV",
    )
    ap.add_argument(
        "--mae-fail",
        type=float,
        default=20.0,
        help="MAE threshold for y_fail when not BSL (absolute $)",
    )
    ap.add_argument(
        "--meta",
        type=Path,
        default=None,
        help="Optional JSON sidecar with row counts",
    )
    args = ap.parse_args()

    if not args.baskets.exists():
        print(f"ERROR: baskets file not found: {args.baskets}", file=sys.stderr)
        return 1

    rows = build_rows(args.baskets, args.mae_fail)
    write_csv(args.out, rows)
    parquet_path = args.out.with_suffix(".parquet")
    maybe_parquet(parquet_path, rows)

    fail_n = sum(int(r["y_fail"]) for r in rows)
    meta = {
        "source": str(args.baskets),
        "rows": len(rows),
        "y_fail": fail_n,
        "y_fail_rate": (fail_n / len(rows)) if rows else 0.0,
        "mae_fail_threshold": args.mae_fail,
        "csv": str(args.out),
        "parquet": str(parquet_path) if parquet_path.exists() else None,
    }
    meta_path = args.meta or args.out.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
