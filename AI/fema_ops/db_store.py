"""Postgres helpers for Ops Plane Wave 1 (IS-P1 / IS-P2)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCHEMA = (
    Path(__file__).resolve().parents[2] / "ops" / "postgres" / "init" / "001_schema.sql"
)


def database_url(url: str | None = None) -> str:
    u = url or os.environ.get("FEMA_DATABASE_URL") or ""
    if not u:
        raise RuntimeError(
            "FEMA_DATABASE_URL not set (e.g. postgresql://fema:fema@localhost:5432/fema)"
        )
    return u


def connect(url: str | None = None):
    import psycopg

    return psycopg.connect(database_url(url))


def migrate(url: str | None = None) -> dict[str, Any]:
    sql_path = _SCHEMA
    if not sql_path.is_file():
        # Docker image may mount ops at /work/ops
        alt = Path("/work/ops/postgres/init/001_schema.sql")
        sql_path = alt if alt.is_file() else sql_path
    if not sql_path.is_file():
        raise FileNotFoundError(f"schema not found: {_SCHEMA}")
    sql = sql_path.read_text(encoding="utf-8")
    with connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    return {"ok": True, "schema": str(sql_path)}


def _f(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _i(v: Any) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def upsert_run(
    url: str | None,
    *,
    run_id: str,
    role: str,
    source: str,
    preset: str | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
    window_start: str | None = None,
    window_end: str | None = None,
    ea_build: str | None = None,
    magic: str | None = None,
    artifact_uri: str | None = None,
    baskets_path: str | None = None,
    notes: str = "",
    metrics: dict | None = None,
    meta: dict | None = None,
) -> None:
    with connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO runs (
                    run_id, role, source, preset, symbol, timeframe,
                    window_start, window_end, ea_build, magic,
                    artifact_uri, baskets_path, notes, metrics, meta, registered_at
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb, NOW()
                )
                ON CONFLICT (run_id) DO UPDATE SET
                    role = EXCLUDED.role,
                    source = EXCLUDED.source,
                    preset = COALESCE(EXCLUDED.preset, runs.preset),
                    symbol = COALESCE(EXCLUDED.symbol, runs.symbol),
                    timeframe = COALESCE(EXCLUDED.timeframe, runs.timeframe),
                    window_start = COALESCE(EXCLUDED.window_start, runs.window_start),
                    window_end = COALESCE(EXCLUDED.window_end, runs.window_end),
                    ea_build = COALESCE(EXCLUDED.ea_build, runs.ea_build),
                    magic = COALESCE(EXCLUDED.magic, runs.magic),
                    artifact_uri = COALESCE(EXCLUDED.artifact_uri, runs.artifact_uri),
                    baskets_path = COALESCE(EXCLUDED.baskets_path, runs.baskets_path),
                    notes = EXCLUDED.notes,
                    metrics = COALESCE(EXCLUDED.metrics, runs.metrics),
                    meta = COALESCE(EXCLUDED.meta, runs.meta)
                """,
                (
                    run_id,
                    role,
                    source,
                    preset,
                    symbol,
                    timeframe,
                    window_start,
                    window_end,
                    ea_build,
                    magic,
                    artifact_uri,
                    baskets_path,
                    notes,
                    json.dumps(metrics or {}),
                    json.dumps(meta or {}),
                ),
            )
        conn.commit()


def replace_baskets(url: str | None, run_id: str, rows: list[dict[str, Any]]) -> int:
    with connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM baskets WHERE run_id = %s", (run_id,))
            n = 0
            for r in rows:
                bid = str(r.get("basket_id") or "").strip()
                if not bid:
                    continue
                cur.execute(
                    """
                    INSERT INTO baskets (
                        run_id, basket_id, open_time, close_time, symbol, direction,
                        open_level, max_depth, profit, exit_reason, hit_tp, hit_bsl,
                        mae, mfe, bars_alive, spread_points, payload, schema_version
                    ) VALUES (
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s
                    )
                    """,
                    (
                        run_id,
                        bid,
                        r.get("open_time"),
                        r.get("close_time"),
                        r.get("symbol"),
                        r.get("direction"),
                        _i(r.get("open_level")),
                        _i(r.get("max_depth")),
                        _f(r.get("profit")),
                        r.get("exit_reason"),
                        _i(r.get("hit_tp")),
                        _i(r.get("hit_bsl")),
                        _f(r.get("mae")),
                        _f(r.get("mfe")),
                        _i(r.get("bars_alive")),
                        _i(r.get("spread_points")),
                        json.dumps(r),
                        "fema_baskets_v2",
                    ),
                )
                n += 1
        conn.commit()
    return n


def insert_health_snapshot(
    url: str | None,
    *,
    score: float | None,
    ladder: str | None,
    would_pause_new: bool | None,
    source: str,
    run_id: str | None,
    components: dict | None,
    cert_version: str | None,
    raw: dict | None,
) -> None:
    with connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO health_snapshots (
                    source, run_id, score, ladder, would_pause_new,
                    components, cert_version, raw
                ) VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb)
                """,
                (
                    source,
                    run_id,
                    score,
                    ladder,
                    would_pause_new,
                    json.dumps(components or {}),
                    cert_version,
                    json.dumps(raw or {}),
                ),
            )
        conn.commit()


def insert_sync_heartbeat(url: str | None, detail: dict[str, Any]) -> None:
    with connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sync_heartbeats (source, last_mtime, bytes, rows, ok, detail)
                VALUES (%s,%s,%s,%s,%s,%s::jsonb)
                """,
                (
                    detail.get("source") or "unknown",
                    detail.get("baskets_mtime"),
                    detail.get("baskets_bytes"),
                    detail.get("baskets_rows"),
                    not bool(detail.get("partial") or detail.get("baskets_locked")),
                    json.dumps(detail),
                ),
            )
        conn.commit()


def list_runs(
    url: str | None,
    *,
    role: str | None = None,
    source: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    q = "SELECT run_id, role, source, preset, symbol, ea_build, magic, metrics, registered_at FROM runs WHERE 1=1"
    args: list[Any] = []
    if role:
        q += " AND role = %s"
        args.append(role)
    if source:
        q += " AND source = %s"
        args.append(source)
    q += " ORDER BY registered_at DESC LIMIT %s"
    args.append(limit)
    with connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(q, args)
            cols = [d.name for d in cur.description]
            out = []
            for row in cur.fetchall():
                d = dict(zip(cols, row))
                if hasattr(d.get("registered_at"), "isoformat"):
                    d["registered_at"] = d["registered_at"].isoformat()
                out.append(d)
            return out


def get_run(url: str | None, run_id: str) -> dict[str, Any] | None:
    with connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM runs WHERE run_id = %s", (run_id,))
            row = cur.fetchone()
            if not row:
                return None
            cols = [d.name for d in cur.description]
            d = dict(zip(cols, row))
            if hasattr(d.get("registered_at"), "isoformat"):
                d["registered_at"] = d["registered_at"].isoformat()
            return d


def list_baskets(url: str | None, run_id: str, limit: int = 100) -> list[dict[str, Any]]:
    with connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT basket_id, open_time, close_time, symbol, direction,
                       max_depth, profit, exit_reason, bars_alive
                FROM baskets WHERE run_id = %s
                ORDER BY basket_id
                LIMIT %s
                """,
                (run_id, limit),
            )
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]


def fetch_latest_health(url: str | None) -> dict[str, Any] | None:
    with connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ts, run_id, source, score, ladder, would_pause_new, components, raw
                FROM health_snapshots ORDER BY ts DESC LIMIT 1
                """
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [d.name for d in cur.description]
            d = dict(zip(cols, row))
            if hasattr(d.get("ts"), "isoformat"):
                d["ts"] = d["ts"].isoformat()
            return d


def fetch_status_summary(url: str | None) -> dict[str, Any]:
    health = fetch_latest_health(url) or {}
    runs = list_runs(url, limit=5)
    with connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT source, last_mtime, bytes, rows, ok, detail, ts
                FROM sync_heartbeats ORDER BY ts DESC LIMIT 1
                """
            )
            hb = cur.fetchone()
            sync: dict[str, Any] = {}
            if hb:
                cols = [d.name for d in cur.description]
                sync = dict(zip(cols, hb))
                if hasattr(sync.get("ts"), "isoformat"):
                    sync["ts"] = sync["ts"].isoformat()
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plane": "wave1",
        "health": {
            "score": health.get("score"),
            "ladder": health.get("ladder"),
            "would_pause_new": health.get("would_pause_new"),
            "source": health.get("source"),
        },
        "sync": sync,
        "runs_recent": runs,
    }
