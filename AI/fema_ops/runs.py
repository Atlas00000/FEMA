"""Append-only run registry (INF-RUN)."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_AI_DIR = Path(__file__).resolve().parent.parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from csv_util import read_csv_rows  # noqa: E402
from paths import KB_RUNS_DIR, REPO_ROOT  # noqa: E402

INDEX_NAME = "index.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify_preset(preset: str) -> str:
    s = preset.strip()
    for prefix in ("FEMA_EURUSD_M5_", "FEMA_", "EURUSD_M5_"):
        if s.upper().startswith(prefix):
            s = s[len(prefix) :]
            break
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s)
    s = s.strip("_") or "UNKNOWN"
    return s[:48]


def window_hash(
    symbol: str,
    timeframe: str,
    start: str,
    end: str,
    baskets_basename: str,
) -> str:
    raw = f"{symbol}|{timeframe}|{start}|{end}|{baskets_basename}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]


def make_run_id(start: str, preset_slug: str, whash: str) -> str:
    """YYYYMMDD_preset_windowhash8 from window start date."""
    digits = re.sub(r"[^0-9]", "", start)[:8]
    if len(digits) < 8:
        digits = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{digits}_{preset_slug}_{whash}"


def _f(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def basket_metrics(rows: list[dict]) -> dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {"n": 0, "profit_factor": 0.0, "win_rate": 0.0, "net": 0.0}
    profits = [_f(r, "profit") for r in rows]
    wins = [p for p in profits if p > 0]
    losses = [-p for p in profits if p < 0]
    gw, gl = sum(wins), sum(losses)
    pf = (gw / gl) if gl > 0 else (99.0 if gw > 0 else 0.0)
    return {
        "n": n,
        "profit_factor": round(pf, 4),
        "win_rate": round(len(wins) / n, 4),
        "net": round(sum(profits), 2),
        "tp_hit_rate": round(
            sum(1 for r in rows if int(_f(r, "hit_tp")) == 1) / n, 4
        )
        if rows and "hit_tp" in rows[0]
        else None,
        "open_first": rows[0].get("open_time", ""),
        "open_last": rows[-1].get("open_time", ""),
    }


def infer_window_from_rows(rows: list[dict]) -> tuple[str, str]:
    if not rows:
        return ("", "")
    start = str(rows[0].get("open_time", ""))[:10]
    end = str(rows[-1].get("open_time", ""))[:10]
    return start, end


def repo_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def load_index(runs_dir: Path) -> list[dict[str, Any]]:
    p = runs_dir / INDEX_NAME
    if not p.is_file():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def save_index(runs_dir: Path, entries: list[dict[str, Any]]) -> None:
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / INDEX_NAME).write_text(
        json.dumps(entries, indent=2) + "\n", encoding="utf-8"
    )


def unique_run_dir(runs_dir: Path, base_id: str) -> tuple[str, Path]:
    """Never overwrite: return base_id or base_id_02, ..."""
    candidate = base_id
    folder = runs_dir / candidate
    if not folder.exists():
        return candidate, folder
    for n in range(2, 100):
        candidate = f"{base_id}_{n:02d}"
        folder = runs_dir / candidate
        if not folder.exists():
            return candidate, folder
    raise RuntimeError(f"too many collisions for {base_id}")


def read_ea_run_id(meta_path: Path | None) -> str | None:
    if meta_path is None or not meta_path.is_file():
        return None
    for line in meta_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("run_id="):
            return line.split("=", 1)[1].strip() or None
    return None


def register_run(
    baskets_path: Path,
    *,
    preset: str,
    role: str = "other",
    window_start: str | None = None,
    window_end: str | None = None,
    symbol: str = "EURUSD",
    timeframe: str = "M5",
    notes: str = "",
    ea_run_id: str | None = None,
    meta_path: Path | None = None,
    runs_dir: Path | None = None,
    status: str = "recorded",
) -> dict[str, Any]:
    runs_dir = runs_dir or KB_RUNS_DIR
    baskets_path = baskets_path.resolve()
    if not baskets_path.is_file():
        raise FileNotFoundError(baskets_path)

    rows = read_csv_rows(baskets_path)
    rows.sort(key=lambda r: str(r.get("open_time", "")))
    inferred_start, inferred_end = infer_window_from_rows(rows)
    start = window_start or inferred_start
    end = window_end or inferred_end
    if not start or not end:
        raise ValueError("window start/end required (pass --from/--to or use dated baskets)")

    preset_slug = slugify_preset(preset)
    whash = window_hash(symbol, timeframe, start, end, baskets_path.name)
    base_id = make_run_id(start, preset_slug, whash)
    run_id, folder = unique_run_dir(runs_dir, base_id)

    metrics = basket_metrics(rows)
    ea_id = ea_run_id or read_ea_run_id(meta_path)

    record = {
        "run_id": run_id,
        "base_run_id": base_id,
        "registered_at": _utc_now(),
        "preset": preset,
        "preset_slug": preset_slug,
        "symbol": symbol,
        "timeframe": timeframe,
        "window": {"start": start, "end": end},
        "window_hash": whash,
        "role": role,
        "baskets_path": repo_rel(baskets_path),
        "ea_run_id": ea_id,
        "metrics": metrics,
        "status": status,
        "notes": notes,
        "schema": "fema_run_v1",
    }

    folder.mkdir(parents=False)
    (folder / "metrics.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )
    (folder / "SOURCE.txt").write_text(
        repo_rel(baskets_path) + "\n", encoding="utf-8"
    )

    index = load_index(runs_dir)
    index.append(
        {
            "run_id": run_id,
            "registered_at": record["registered_at"],
            "role": role,
            "preset": preset,
            "window": record["window"],
            "metrics": {
                "n": metrics["n"],
                "profit_factor": metrics["profit_factor"],
                "win_rate": metrics["win_rate"],
                "net": metrics["net"],
            },
            "path": f"runs/{run_id}/",
        }
    )
    save_index(runs_dir, index)
    return record


def list_runs(runs_dir: Path | None = None) -> list[dict[str, Any]]:
    return load_index(runs_dir or KB_RUNS_DIR)


def ascii_run_line(rec: dict[str, Any]) -> str:
    m = rec.get("metrics") or {}
    w = rec.get("window") or {}
    return (
        f"{rec.get('run_id')} role={rec.get('role')} "
        f"PF={m.get('profit_factor')} n={m.get('n')} "
        f"window={w.get('start')}..{w.get('end')}"
    )
