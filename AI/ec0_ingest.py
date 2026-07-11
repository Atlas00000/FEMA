#!/usr/bin/env python3
"""EC0 ingest — verify 2020-2025 AI0 baskets, split, zero-skip replay, freeze holdout baseline.

Usage (after tester finishes):
  python AI/ec0_ingest.py --from-agent "C:/.../Agent-.../MQL5/Files/FEMA_AI/EURUSD_*_baskets.csv"

Or if already copied to AI/data/EURUSD_baskets_2020_2025.csv:
  python AI/ec0_ingest.py
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parent
_ROOT = _AI_DIR.parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from build_dataset import build_rows, write_csv  # noqa: E402
from repair_basket_ids import metrics, repair_baskets  # noqa: E402
from split_2020_2025 import split_rows  # noqa: E402


def parse_day(s: str, eod: bool = False) -> datetime:
    parts = s.strip().replace("-", ".").split(".")
    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    if eod:
        return datetime(y, m, d, 23, 59, 59)
    return datetime(y, m, d, 0, 0, 0)


def verify_span(rows: list[dict], expect_start_year: int = 2020, expect_end_year: int = 2025) -> dict:
    if not rows:
        return {"ok": False, "error": "empty baskets"}
    first = rows[0]["open_time"]
    last = rows[-1]["open_time"]
    y0 = int(first[:4])
    y1 = int(last[:4])
    # Require coverage into start year and last basket in end year
    ok = (y0 == expect_start_year) and (y1 == expect_end_year)
    return {
        "ok": ok,
        "first": first,
        "last": last,
        "n": len(rows),
        "year_first": y0,
        "year_last": y1,
        "expect": f"first year {expect_start_year}, last year {expect_end_year}",
        "unique_ids_raw": len({str(r.get("basket_id", "")) for r in rows}),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="EC0 ingest for AI Edge Contain")
    ap.add_argument(
        "--from-agent",
        type=Path,
        default=None,
        help="Path to tester Agent FEMA_AI/*_baskets.csv to copy",
    )
    ap.add_argument(
        "--baskets",
        type=Path,
        default=_ROOT / "AI" / "data" / "EURUSD_baskets_2020_2025.csv",
    )
    ap.add_argument("--out-dir", type=Path, default=_ROOT / "AI" / "data")
    ap.add_argument("--deposit", type=float, default=400.0)
    ap.add_argument("--mae-fail", type=float, default=20.0)
    ap.add_argument("--allow-partial", action="store_true", help="Do not fail if span is incomplete")
    args = ap.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    status: dict = {
        "phase": "EC0-DATA",
        "tasks": {},
    }

    # EC0-003 copy
    if args.from_agent is not None:
        if not args.from_agent.exists():
            print(f"ERROR: agent baskets not found: {args.from_agent}", file=sys.stderr)
            return 1
        shutil.copy2(args.from_agent, args.baskets)
        status["tasks"]["EC0-003"] = {
            "status": "done",
            "src": str(args.from_agent).replace("\\", "/"),
            "dst": str(args.baskets).replace("\\", "/"),
        }
        print(f"copied -> {args.baskets}")
    else:
        status["tasks"]["EC0-003"] = {
            "status": "done" if args.baskets.exists() else "pending",
            "dst": str(args.baskets).replace("\\", "/"),
        }

    if not args.baskets.exists():
        status["tasks"]["EC0-001"] = {"status": "pending", "note": "Run tester 2020.01.01→2025.12.31"}
        status["tasks"]["EC0-002"] = {"status": "blocked"}
        status["exit"] = "blocked_on_collect"
        report_path = out_dir / "ec0_status.json"
        report_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(
            "EC0 blocked: no baskets file.\n"
            "1) Tester: PRODUCTION.set, InpUseAiEventLog=true, 2020.01.01 to 2025.12.31, Every tick, $400\n"
            "2) python AI/ec0_ingest.py --from-agent \"<Agent FEMA_AI/*_baskets.csv>\""
        )
        print(f"wrote {report_path}")
        return 2

    # EC0-004 repair ids + read
    uid_path = out_dir / "EURUSD_baskets_2020_2025_uid.csv"
    raw_rows = repair_baskets(args.baskets, uid_path)
    # sort already done in repair
    span = verify_span(raw_rows)
    status["tasks"]["EC0-002"] = {"status": "done" if span["ok"] else "fail", **span}
    status["tasks"]["EC0-004"] = {
        "status": "done",
        "uid": str(uid_path).replace("\\", "/"),
        "unique_ids": len(raw_rows),
    }

    # Span gate: prefer full 2020-2025; allow multi-year partial with warning
    span_ok_full = span["ok"]
    span_ok_partial = (
        span.get("year_first") == 2020
        and span.get("year_last") is not None
        and int(span["year_last"]) >= 2022
        and int(span["n"]) >= 200
    )
    if not span_ok_full and not (args.allow_partial or span_ok_partial):
        status["exit"] = "span_fail"
        status["tasks"]["EC0-001"] = {
            "status": "fail_or_incomplete",
            "note": f"CSV span {span['first']} -> {span['last']} (need last year 2025, or multi-year partial)",
        }
        report_path = out_dir / "ec0_status.json"
        report_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(f"ERROR: span check failed: {span['first']} -> {span['last']}")
        print("Re-run tester to 2025.12.31 (consider larger deposit if account wipes early).")
        print(f"wrote {report_path}")
        return 3

    if not span_ok_full:
        status["tasks"]["EC0-002"]["status"] = "partial"
        status["tasks"]["EC0-002"]["warning"] = (
            "Full 2020-2025 not present. Using available span; "
            "2024-2025 holdout may be empty if account wiped earlier."
        )
        print(f"WARNING: partial span {span['first']} -> {span['last']}")

    status["tasks"]["EC0-001"] = {"status": "done" if span_ok_full else "partial"}

    # EC0-005 labeled full
    labeled = build_rows(uid_path, mae_fail=args.mae_fail)
    full_path = out_dir / "dataset_2020_2025.csv"
    write_csv(full_path, labeled)
    status["tasks"]["EC0-005"] = {
        "status": "done",
        "path": str(full_path).replace("\\", "/"),
        "n": len(labeled),
        "y_fail": sum(int(r["y_fail"]) for r in labeled),
    }

    # EC0-006 split — prefer plan windows; fall back if holdout empty
    train = split_rows(labeled, parse_day("2020.01.01"), parse_day("2023.12.31", True))
    hold = split_rows(labeled, parse_day("2024.01.01"), parse_day("2025.12.31", True))
    split_mode = "plan_2020_23_train__2024_25_holdout"
    if len(hold) < 30:
        # Account often dies before 2024 on $400 — use mid-span holdout
        train = split_rows(labeled, parse_day("2020.01.01"), parse_day("2021.12.31", True))
        hold = split_rows(labeled, parse_day("2022.01.01"), parse_day("2023.12.31", True))
        split_mode = "fallback_2020_21_train__2022_23_holdout"
        print(
            f"NOTE: plan holdout 2024-2025 empty; using fallback split {split_mode} "
            f"(train n={len(train)}, hold n={len(hold)})"
        )

    if split_mode.startswith("fallback"):
        train_path = out_dir / "dataset_train_2020_2021.csv"
        hold_path = out_dir / "dataset_holdout_2022_2023.csv"
    else:
        train_path = out_dir / "dataset_train_2020_2023.csv"
        hold_path = out_dir / "dataset_holdout_2024_2025.csv"
    write_csv(train_path, train)
    write_csv(hold_path, hold)
    status["tasks"]["EC0-006"] = {
        "status": "done",
        "split_mode": split_mode,
        "train": metrics(train, args.deposit),
        "holdout": metrics(hold, args.deposit),
        "train_path": str(train_path).replace("\\", "/"),
        "holdout_path": str(hold_path).replace("\\", "/"),
    }

    # EC0-007 zero-skip replay via subprocess on uid baskets
    replay_out = out_dir / "ec0_replay.json"
    cmd = [
        sys.executable,
        str(_AI_DIR / "replay.py"),
        "--baskets",
        str(uid_path),
        "--deposit",
        str(args.deposit),
        "--out",
        str(replay_out),
    ]
    # avoid comparing to 2026 demo baseline for zero-skip check
    baseline_stub = out_dir / "ec0_replay_baseline_stub.json"
    baseline_stub.write_text(
        json.dumps({"deposit": args.deposit, "metrics": metrics(labeled, args.deposit)}),
        encoding="utf-8",
    )
    # rewrite stub metrics keys for replay.compare - replay expects profit_factor etc on metrics
    m = metrics(labeled, args.deposit)
    baseline_stub.write_text(
        json.dumps(
            {
                "deposit": args.deposit,
                "metrics": {
                    "profit_factor": m["pf"],
                    "net_profit": m["net"],
                    "max_dd_balance_pct": m["max_dd_pct"],
                    "max_dd_pct": m["max_dd_pct"],
                    "win_rate": m["wr"],
                    "trades": m["n"],
                },
            }
        ),
        encoding="utf-8",
    )
    cmd.extend(["--baseline", str(baseline_stub)])
    proc = subprocess.run(cmd, cwd=str(_ROOT), capture_output=True, text=True)
    zero_ok = False
    if replay_out.exists():
        rep = json.loads(replay_out.read_text(encoding="utf-8"))
        zero_ok = bool(rep.get("zero_skip_matches_full"))
        status["tasks"]["EC0-007"] = {
            "status": "done" if zero_ok else "fail",
            "zero_skip_matches_full": zero_ok,
            "full_sample": rep.get("full_sample"),
            "replay_report": str(replay_out).replace("\\", "/"),
            "stderr": proc.stderr[-500:] if proc.returncode != 0 else "",
        }
    else:
        status["tasks"]["EC0-007"] = {
            "status": "fail",
            "stderr": proc.stderr[-800:],
            "stdout": proc.stdout[-800:],
        }

    # EC0-008 holdout baseline freeze
    hold_m = metrics(hold, args.deposit)
    hold_base = {
        "phase": "EC0-008",
        "role": "AI Edge Contain holdout baseline (guardrail compares)",
        "split_mode": split_mode,
        "window": (
            {"start": "2022.01.01", "end": "2023.12.31"}
            if split_mode.startswith("fallback")
            else {"start": "2024.01.01", "end": "2025.12.31"}
        ),
        "deposit": args.deposit,
        "source_dataset": str(hold_path).replace("\\", "/"),
        "basket_metrics": hold_m,
        "train_window": (
            {"start": "2020.01.01", "end": "2021.12.31", "metrics": metrics(train, args.deposit)}
            if split_mode.startswith("fallback")
            else {"start": "2020.01.01", "end": "2023.12.31", "metrics": metrics(train, args.deposit)}
        ),
        "full_collect": metrics(labeled, args.deposit),
        "span": span,
        "philosophy": "guardrails_not_gates",
        "note": (
            "Not the demo PRODUCTION 2026 freeze. Use for EC1–EC5 holdout scoring. "
            + (
                "Fallback split used because $400 collect wiped before 2024 (order_fail_10019 no money)."
                if split_mode.startswith("fallback")
                else ""
            )
        ),
    }
    hold_base_path = out_dir / "ec0_holdout_baseline.json"
    hold_base_path.write_text(json.dumps(hold_base, indent=2), encoding="utf-8")
    split_report = {
        "philosophy": "guardrails_not_gates",
        "split_mode": split_mode,
        "span": span,
        "train": metrics(train, args.deposit),
        "holdout": hold_m,
        "all": metrics(labeled, args.deposit),
        "artifacts": {
            "raw": str(args.baskets).replace("\\", "/"),
            "uid": str(uid_path).replace("\\", "/"),
            "full": str(full_path).replace("\\", "/"),
            "train": str(train_path).replace("\\", "/"),
            "holdout": str(hold_path).replace("\\", "/"),
            "holdout_baseline": str(hold_base_path).replace("\\", "/"),
        },
    }
    split_report_path = out_dir / "split_2020_2025_report.json"
    split_report_path.write_text(json.dumps(split_report, indent=2), encoding="utf-8")
    status["tasks"]["EC0-008"] = {
        "status": "done",
        "holdout_baseline": str(hold_base_path).replace("\\", "/"),
        "split_report": str(split_report_path).replace("\\", "/"),
        "holdout": hold_m,
    }

    def _ok(st: str) -> bool:
        return st in ("done", "partial")

    all_ok = all(
        _ok(status["tasks"].get(k, {}).get("status", ""))
        for k in ("EC0-001", "EC0-002", "EC0-003", "EC0-004", "EC0-005", "EC0-006", "EC0-007", "EC0-008")
    )
    # EC0-007 must be fully done (zero-skip integrity)
    zero_ok_task = status["tasks"].get("EC0-007", {}).get("status") == "done"
    has_partial = any(
        status["tasks"].get(k, {}).get("status") == "partial"
        for k in ("EC0-001", "EC0-002", "EC0-003", "EC0-004", "EC0-005", "EC0-006", "EC0-007", "EC0-008")
    )
    if all_ok and zero_ok_task:
        status["exit"] = "partial_complete" if has_partial else "complete"
    elif all_ok:
        status["exit"] = "incomplete"
    else:
        status["exit"] = "incomplete"
    status_path = out_dir / "ec0_status.json"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")

    print(json.dumps({"exit": status["exit"], "span": span, "holdout": hold_m, "train_n": len(train), "hold_n": len(hold)}, indent=2))
    print(f"wrote {status_path}")
    return 0 if status["exit"] in ("complete", "partial_complete") else 4


if __name__ == "__main__":
    raise SystemExit(main())
