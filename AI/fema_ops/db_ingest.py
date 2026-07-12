"""Wave 1 — ingest live/drop-zone baskets into artifacts + Postgres."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from csv_util import parse_meta_lines, read_csv_rows
from fema_ops import db_store
from paths import LIVE_DIR, REPO_ROOT

DEFAULT_INCOMING = Path("/var/fema/incoming")
DEFAULT_ARTIFACTS = Path("/var/fema/artifacts")
LOCAL_INCOMING = REPO_ROOT / "ops" / "incoming"
LOCAL_ARTIFACTS = REPO_ROOT / "AI" / "data" / "artifacts"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def resolve_dirs() -> tuple[Path, Path]:
    incoming = DEFAULT_INCOMING if DEFAULT_INCOMING.is_dir() else LOCAL_INCOMING
    artifacts = DEFAULT_ARTIFACTS if DEFAULT_ARTIFACTS.is_dir() else LOCAL_ARTIFACTS
    incoming.mkdir(parents=True, exist_ok=True)
    (incoming / "demo").mkdir(exist_ok=True)
    (incoming / "tester").mkdir(exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "runs").mkdir(exist_ok=True)
    return incoming, artifacts


def _metrics_from_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {"n": 0}
    profits = []
    wins = 0
    for r in rows:
        try:
            p = float(r.get("profit") or 0)
        except (TypeError, ValueError):
            p = 0.0
        profits.append(p)
        if p > 0:
            wins += 1
    gross_win = sum(p for p in profits if p > 0)
    gross_loss = abs(sum(p for p in profits if p < 0))
    pf = (gross_win / gross_loss) if gross_loss > 0 else (99.0 if gross_win > 0 else 0.0)
    return {
        "n": n,
        "net": round(sum(profits), 2),
        "profit_factor": round(pf, 4),
        "win_rate": round(wins / n, 4) if n else 0.0,
    }


def ingest_baskets_file(
    baskets: Path,
    *,
    source: str,
    role: str = "demo",
    run_id: str | None = None,
    url: str | None = None,
    copy_artifacts: bool = True,
) -> dict[str, Any]:
    if not baskets.is_file():
        raise FileNotFoundError(baskets)
    meta = parse_meta_lines(baskets)
    rows = read_csv_rows(baskets)
    rid = run_id or meta.get("run_id") or f"{source}_{_utc()}"
    _, artifacts = resolve_dirs()
    art_dir = artifacts / "runs" / rid
    if copy_artifacts:
        art_dir.mkdir(parents=True, exist_ok=True)
        dest_b = art_dir / "baskets.csv"
        if not dest_b.is_file():
            shutil.copy2(baskets, dest_b)
        stem = (
            baskets.name[: -len("_baskets.csv")]
            if baskets.name.endswith("_baskets.csv")
            else baskets.stem
        )
        for name in (
            f"{stem}_events.csv",
            f"{stem}_run.meta.txt",
            f"{stem}_run_config.json",
        ):
            p = baskets.with_name(name)
            if p.is_file() and not (art_dir / p.name).is_file():
                try:
                    shutil.copy2(p, art_dir / p.name)
                except OSError:
                    pass
        (art_dir / "SOURCE.txt").write_text(
            f"source={source}\nrole={role}\nbaskets={baskets}\n",
            encoding="utf-8",
        )
        try:
            from fema_ops.artifacts import write_manifest

            write_manifest(rid, source=source, role=role)
        except Exception:  # noqa: BLE001
            pass

    metrics = _metrics_from_rows(rows)
    db_store.upsert_run(
        url,
        run_id=rid,
        role=role,
        source=source,
        preset=meta.get("preset_id") or meta.get("preset"),
        symbol=meta.get("symbol") or (rows[0].get("symbol") if rows else None),
        timeframe="M5",
        ea_build=meta.get("ea_build"),
        magic=meta.get("magic"),
        artifact_uri=str(art_dir) if copy_artifacts else None,
        baskets_path=str(baskets),
        notes=f"wave1 db-ingest source={source}",
        metrics=metrics,
        meta=meta,
    )
    n = db_store.replace_baskets(url, rid, rows)
    return {
        "run_id": rid,
        "source": source,
        "role": role,
        "n_baskets": n,
        "metrics": metrics,
        "artifact_uri": str(art_dir) if copy_artifacts else None,
    }


def ingest_from_live(
    *,
    source: str = "demo",
    role: str | None = None,
    url: str | None = None,
) -> dict[str, Any]:
    baskets = LIVE_DIR / "latest_baskets.csv"
    role = role or ("demo" if source == "demo" else "collect")
    out = ingest_baskets_file(baskets, source=source, role=role, url=url)

    hb_path = LIVE_DIR / "sync_heartbeat.json"
    if hb_path.is_file():
        try:
            hb = json.loads(hb_path.read_text(encoding="utf-8"))
            db_store.insert_sync_heartbeat(url, hb)
        except (OSError, json.JSONDecodeError):
            pass

    health_path = LIVE_DIR / "health_latest.json"
    if health_path.is_file():
        try:
            raw = json.loads(health_path.read_text(encoding="utf-8"))
            formula = str(raw.get("formula_version") or "").strip()
            if not formula:
                raise ValueError(
                    "health_latest.json missing formula_version — re-run fema_ops health (RG-VER-02)"
                )
            db_store.insert_health_snapshot(
                url,
                score=raw.get("health"),
                ladder=(raw.get("ladder") or {}).get("label"),
                would_pause_new=raw.get("would_pause_new"),
                source=source,
                run_id=out["run_id"],
                components=raw.get("windows"),
                cert_version=formula,
                raw=raw,
            )
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    return out


def ingest_from_incoming(
    *,
    source: str = "demo",
    role: str | None = None,
    url: str | None = None,
) -> dict[str, Any]:
    incoming, _ = resolve_dirs()
    folder = incoming / source
    files = sorted(folder.glob("*_baskets.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError(f"no *_baskets.csv in {folder}")
    role = role or ("demo" if source == "demo" else "collect")
    return ingest_baskets_file(files[0], source=source, role=role, url=url)
