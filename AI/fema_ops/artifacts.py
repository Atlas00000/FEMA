"""Immutable run artifacts + DB rehydrate (IS-P3-01).

Primary store: AI/data/artifacts/runs/{run_id}/ (or /var/fema/artifacts in Docker).
MinIO is optional later — same layout as an S3 prefix.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from csv_util import parse_meta_lines, read_csv_rows
from fema_ops.db_ingest import resolve_dirs, _metrics_from_rows
from fema_ops import db_store
from paths import REPO_ROOT


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def artifacts_root() -> Path:
    _, art = resolve_dirs()
    return art


def run_dir(run_id: str) -> Path:
    return artifacts_root() / "runs" / run_id


def write_manifest(run_id: str, *, source: str = "", role: str = "", extra: dict | None = None) -> Path:
    d = run_dir(run_id)
    d.mkdir(parents=True, exist_ok=True)
    files = sorted(p.name for p in d.iterdir() if p.is_file() and p.name != "manifest.json")
    man = {
        "schema": "fema_artifact_manifest_v0",
        "run_id": run_id,
        "written_at": _utc_now(),
        "source": source,
        "role": role,
        "files": files,
        "immutable": True,
        "note": "Do not overwrite baskets.csv after first archive; rehydrate DB from these blobs.",
    }
    if extra:
        man.update(extra)
    path = d / "manifest.json"
    path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
    return path


def list_artifact_runs(limit: int = 50) -> list[dict[str, Any]]:
    root = artifacts_root() / "runs"
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for p in sorted(root.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not p.is_dir():
            continue
        baskets = p / "baskets.csv"
        man = p / "manifest.json"
        meta = {}
        if man.is_file():
            try:
                meta = json.loads(man.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                meta = {}
        rows.append(
            {
                "run_id": p.name,
                "path": str(p.relative_to(REPO_ROOT)).replace("\\", "/")
                if str(p).startswith(str(REPO_ROOT))
                else str(p).replace("\\", "/"),
                "has_baskets": baskets.is_file(),
                "bytes": baskets.stat().st_size if baskets.is_file() else 0,
                "manifest": bool(man.is_file()),
                "source": meta.get("source"),
                "role": meta.get("role"),
            }
        )
        if len(rows) >= limit:
            break
    return rows


def archive_from_live(
    *,
    run_id: str | None = None,
    source: str = "demo",
    role: str = "demo",
    baskets: Path | None = None,
) -> dict[str, Any]:
    """Copy live baskets into immutable artifacts/runs/{run_id}/."""
    from paths import LATEST_BASKETS

    src = baskets or LATEST_BASKETS
    if not src.is_file():
        raise FileNotFoundError(src)
    meta = parse_meta_lines(src)
    rid = run_id or meta.get("run_id") or f"{source}_archive"
    d = run_dir(rid)
    d.mkdir(parents=True, exist_ok=True)
    dest = d / "baskets.csv"
    if dest.is_file():
        # immutable: keep first copy; still refresh sidecar meta if missing
        note = "exists_skip_overwrite"
    else:
        shutil.copy2(src, dest)
        note = "copied"
    write_manifest(rid, source=source, role=role, extra={"archive_note": note})
    return {
        "run_id": rid,
        "dir": str(d).replace("\\", "/"),
        "note": note,
        "manifest": True,
    }


def rehydrate_run(
    run_id: str,
    *,
    url: str | None = None,
    role: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """Restore Postgres run+baskets from artifact blobs (DB may be empty)."""
    d = run_dir(run_id)
    baskets = d / "baskets.csv"
    if not baskets.is_file():
        raise FileNotFoundError(f"no baskets.csv under {d}")
    man = {}
    mp = d / "manifest.json"
    if mp.is_file():
        try:
            man = json.loads(mp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            man = {}
    meta = parse_meta_lines(baskets)
    rows = read_csv_rows(baskets)
    metrics = _metrics_from_rows(rows)
    src = source or man.get("source") or meta.get("source") or "artifact"
    rol = role or man.get("role") or "other"
    db_store.upsert_run(
        url,
        run_id=run_id,
        role=rol,
        source=src,
        preset=meta.get("preset_id") or meta.get("preset"),
        symbol=meta.get("symbol") or (rows[0].get("symbol") if rows else None),
        timeframe="M5",
        ea_build=meta.get("ea_build"),
        magic=meta.get("magic"),
        artifact_uri=str(d),
        baskets_path=str(baskets),
        notes="rehydrate from artifacts (IS-P3-01)",
        metrics=metrics,
        meta={**meta, "rehydrated_at": _utc_now()},
    )
    n = db_store.replace_baskets(url, run_id, rows)
    return {
        "run_id": run_id,
        "n_baskets": n,
        "metrics": metrics,
        "source": src,
        "role": rol,
        "artifact_dir": str(d).replace("\\", "/"),
    }
