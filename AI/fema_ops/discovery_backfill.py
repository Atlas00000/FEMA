"""EL1 — backfill Discovery table rows into INF-RUN (documented, no basket CSV)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_AI_DIR = Path(__file__).resolve().parent.parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from paths import KB_DIR, KB_RUNS_DIR  # noqa: E402

from .runs import (  # noqa: E402
    load_index,
    make_run_id,
    save_index,
    slugify_preset,
    unique_run_dir,
    window_hash,
)

SEED = KB_DIR / "discovery_rows_seed.json"
MAP_OUT = KB_DIR / "discovery_run_ids.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _role_for(status: str, row: int) -> str:
    if row == 22:
        return "lock"
    s = status.lower()
    if "g3" in s and "fail" in s:
        return "reject"
    if "control" in s:
        return "other"
    if "alternate" in s or "prev" in s or "near" in s:
        return "candidate"
    if "reject" in s or "fail" in s or "inert" in s:
        return "reject"
    if "2025" in s:
        return "other"
    return "other"


def _failure_reason(notes: str, status: str) -> str:
    n = (notes + " " + status).lower()
    if "dd" in n and ("fail" in n or "g1" in n):
        return "dd_breach"
    if "pf" in n and "fail" in n:
        return "pf_breach"
    if "session" in n or "ses_" in n:
        return "session"
    if "adx" in n or "atr" in n or "regime" in n or "htf" in n:
        return "regime"
    if "steamroller" in n or "no sl" in n:
        return "other"
    if "reject" in n or "fail" in n:
        return "other"
    return ""


def register_documented(row: dict[str, Any], runs_dir: Path) -> dict[str, Any]:
    preset = str(row["preset"])
    slug = slugify_preset(preset)
    symbol = str(row.get("symbol") or "EURUSD")
    tf = str(row.get("timeframe") or "M5")
    start = str(row["window_start"])
    end = str(row["window_end"])
    basename = f"discovery_row_{int(row['row'])}"
    wh = window_hash(symbol, tf, start, end, basename)
    base_id = make_run_id(start, slug, wh)

    # Row 22 = PRODUCTION lock already registered from AI0 baskets
    if int(row["row"]) == 22:
        lock_id = "20260101_PRODUCTION_13c52cd9"
        lock_path = runs_dir / lock_id / "metrics.json"
        if lock_path.is_file():
            rec = json.loads(lock_path.read_text(encoding="utf-8"))
            rec["discovery_row"] = 22
            rec["discovery_status"] = row.get("status")
            lock_path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
            return rec

    folder = runs_dir / base_id
    if folder.is_dir() and (folder / "metrics.json").is_file():
        # Refresh role/notes from seed (idempotent EL1 re-backfill)
        rec = json.loads((folder / "metrics.json").read_text(encoding="utf-8"))
        rec["role"] = _role_for(str(row.get("status") or ""), int(row["row"]))
        rec["discovery_row"] = int(row["row"])
        rec["discovery_status"] = row.get("status")
        rec["task_id"] = row.get("task_id")
        rec["failure_reason"] = _failure_reason(
            str(row.get("notes") or ""), str(row.get("status") or "")
        )
        rec["notes"] = str(row.get("notes") or "")
        (folder / "metrics.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        return rec

    run_id, folder = unique_run_dir(runs_dir, base_id)
    role = _role_for(str(row.get("status") or ""), int(row["row"]))

    metrics = {
        "n": int(row.get("trades") or 0),
        "profit_factor": float(row["pf"]) if row.get("pf") is not None else None,
        "win_rate": (float(row["wr"]) / 100.0) if row.get("wr") is not None else None,
        "net": float(row["net"]) if row.get("net") is not None else None,
        "max_dd_pct": row.get("dd"),
        "unit": "mt5_deals_discovery_table",
    }
    record = {
        "run_id": run_id,
        "base_run_id": base_id,
        "registered_at": _utc_now(),
        "preset": preset,
        "preset_slug": slug,
        "symbol": symbol,
        "timeframe": tf,
        "window": {"start": start, "end": end},
        "window_hash": wh,
        "role": role,
        "baskets_path": None,
        "ea_run_id": None,
        "metrics": metrics,
        "status": "documented",
        "discovery_row": int(row["row"]),
        "task_id": row.get("task_id"),
        "discovery_status": row.get("status"),
        "failure_reason": _failure_reason(str(row.get("notes") or ""), str(row.get("status") or "")),
        "notes": str(row.get("notes") or ""),
        "schema": "fema_run_v1",
        "source": "Edge Discovery.md backtest results log (EL1 backfill)",
    }
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "metrics.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    (folder / "SOURCE.txt").write_text(
        f"Edge Discovery.md#row-{int(row['row'])}\n", encoding="utf-8"
    )
    return record


def backfill(seed_path: Path | None = None, runs_dir: Path | None = None) -> dict[str, Any]:
    seed_path = seed_path or SEED
    runs_dir = runs_dir or KB_RUNS_DIR
    rows = json.loads(seed_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("seed must be a JSON array")

    index = load_index(runs_dir)
    # Drop prior documented discovery rows from index; rebuild from seed (keep lock/collect)
    index = [
        e
        for e in index
        if e.get("status") != "documented" and e.get("discovery_row") is None
    ]
    existing_ids = {e.get("run_id") for e in index}
    mapping: list[dict[str, Any]] = []
    created = 0

    for row in rows:
        rec = register_documented(row, runs_dir)
        rid = rec["run_id"]
        mapping.append(
            {
                "row": int(row["row"]),
                "preset": row["preset"],
                "task_id": row.get("task_id"),
                "run_id": rid,
                "role": rec.get("role"),
                "status": rec.get("status"),
            }
        )
        if rid not in existing_ids:
            index.append(
                {
                    "run_id": rid,
                    "registered_at": rec.get("registered_at"),
                    "role": rec.get("role"),
                    "preset": rec.get("preset"),
                    "window": rec.get("window"),
                    "metrics": {
                        "n": (rec.get("metrics") or {}).get("n"),
                        "profit_factor": (rec.get("metrics") or {}).get("profit_factor"),
                        "win_rate": (rec.get("metrics") or {}).get("win_rate"),
                        "net": (rec.get("metrics") or {}).get("net"),
                    },
                    "path": f"runs/{rid}/",
                    "discovery_row": int(row["row"]),
                    "status": rec.get("status") or "documented",
                }
            )
            existing_ids.add(rid)
            created += 1
        else:
            # refresh index role for existing lock linked as row 22
            for e in index:
                if e.get("run_id") == rid:
                    e["discovery_row"] = int(row["row"])
                    e["role"] = rec.get("role")
                    break

    save_index(runs_dir, index)
    out = {
        "generated_at": _utc_now(),
        "seed": str(seed_path).replace("\\", "/"),
        "created_or_linked": len(mapping),
        "new_index_rows": created,
        "rows": mapping,
    }
    MAP_OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out
