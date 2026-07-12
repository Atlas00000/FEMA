"""Generate AI/STATUS.md for humans and coding agents (INF-STATUS)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_AI_DIR = Path(__file__).resolve().parent.parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from paths import (  # noqa: E402
    CERTIFICATE_JSON,
    COMPAT_LATEST,
    FINGERPRINT_LATEST,
    HEALTH_LATEST_JSON,
    KB_RUNS_DIR,
    LATEST_BASKETS,
    LATEST_SOURCE,
    LINEAGE_JSON,
    LIVE_DIR,
    PAUSE_FLAG_LIVE,
    REPO_ROOT,
    VERSIONS_JSON,
)

STATUS_MD = _AI_DIR / "STATUS.md"
STATUS_JSON = _AI_DIR / "STATUS.json"
HEARTBEAT_JSON = LIVE_DIR / "sync_heartbeat.json"
OBSERVATORY_MD = LIVE_DIR / "observatory_daily.md"

# Operator focus — infrascaleup §16
OPEN_ESR = "Wave 6 park-freeze offline; after demo basket close run pipeline for on_demo_path"
PHASE = "Wave 6 park freeze (no PARK features)"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _last_runs(limit: int = 3) -> list[dict[str, Any]]:
    idx = _load_json(KB_RUNS_DIR / "index.json")
    if not isinstance(idx, list):
        return []
    return idx[-limit:]


def _lock_run(idx: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    rows = idx
    if rows is None:
        raw = _load_json(KB_RUNS_DIR / "index.json")
        rows = raw if isinstance(raw, list) else []
    # Prefer AI0 basket lock (row 22 / known id), not documented cross-symbol rejects
    for r in rows:
        if r.get("run_id") == "20260101_PRODUCTION_13c52cd9":
            return r
    for r in reversed(rows):
        if r.get("role") == "lock" and r.get("discovery_row") in (22, None):
            if r.get("status") != "documented" or r.get("discovery_row") == 22:
                return r
    for r in reversed(rows):
        if r.get("role") == "lock":
            return r
    return None


def gather() -> dict[str, Any]:
    health = _load_json(HEALTH_LATEST_JSON) or {}
    cert = _load_json(CERTIFICATE_JSON) or {}
    idx_raw = _load_json(KB_RUNS_DIR / "index.json")
    idx = idx_raw if isinstance(idx_raw, list) else []
    runs = idx[-3:] if idx else []
    lock_run = _lock_run(idx)

    source = ""
    if LATEST_SOURCE.is_file():
        source = LATEST_SOURCE.read_text(encoding="utf-8", errors="replace").strip()[:400]

    hb = _load_json(HEARTBEAT_JSON) or {}
    src_map: dict[str, str] = {}
    for line in source.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            src_map[k.strip()] = v.strip()

    sync_source = hb.get("source") or src_map.get("source") or "unknown"
    age_hours = hb.get("age_hours")
    if age_hours is None and src_map.get("age_hours") not in (None, "", "None"):
        try:
            age_hours = float(src_map["age_hours"])
        except ValueError:
            age_hours = None
    stale = bool(hb.get("stale") or src_map.get("stale") == "1")
    header_only = bool(hb.get("header_only") or src_map.get("header_only") == "1")
    baskets_rows = hb.get("baskets_rows")
    if baskets_rows is None and src_map.get("baskets_rows"):
        try:
            baskets_rows = int(src_map["baskets_rows"])
        except ValueError:
            baskets_rows = None

    pause_flag = False
    if PAUSE_FLAG_LIVE.is_file():
        body = PAUSE_FLAG_LIVE.read_text(encoding="utf-8", errors="replace").lower()
        pause_flag = "pause_new=1" in body or body.strip().startswith("1")

    health_on_demo = sync_source == "demo" and not header_only and (baskets_rows or 0) > 0

    versions = _load_json(VERSIONS_JSON) or {}
    comps = versions.get("components") or {}
    lineage = _load_json(LINEAGE_JSON) or {}
    active = lineage.get("active_lock") or {}
    formula = (
        health.get("formula_version")
        or (comps.get("health_model") or {}).get("id")
        or cert.get("health_formula_version")
        or "health_v0"
    )
    compat = health.get("compatibility") or _load_json(COMPAT_LATEST) or {}
    fp = health.get("fingerprint") or _load_json(FINGERPRINT_LATEST) or {}

    return {
        "generated_at": _utc_now(),
        "phase": PHASE,
        "open_esr": OPEN_ESR,
        "ea_build_target": "1.26",
        "preset": cert.get("preset") or health.get("preset") or "FEMA_EURUSD_M5_PRODUCTION",
        "certificate": str(CERTIFICATE_JSON.relative_to(REPO_ROOT)).replace("\\", "/"),
        "versions": {
            "file": "AI/kb/versions.json",
            "health_model": (comps.get("health_model") or {}).get("id"),
            "certificate": (comps.get("certificate") or {}).get("version"),
            "gate_rules": (comps.get("gate_rules") or {}).get("id"),
            "kb": (comps.get("kb") or {}).get("id"),
            "preset": (comps.get("preset") or {}).get("version"),
            "feature_store": (comps.get("feature_store") or {}).get("id"),
        },
        "lineage": {
            "file": "AI/kb/lineage.json",
            "active_run_id": active.get("run_id"),
            "parent_preset_id": active.get("parent_preset_id"),
            "retired_run_id": active.get("retired_run_id"),
        },
        "compatibility": {
            "signal": compat.get("signal"),
            "score": compat.get("score"),
            "suggest_subsystems": compat.get("suggest_subsystems") or [],
            "shadow": True,
        },
        "fingerprint": {
            "artifact": "AI/data/live/fingerprint_latest.json"
            if FINGERPRINT_LATEST.is_file()
            else None,
            "n_baskets": (fp.get("window") or {}).get("n_baskets"),
            "adx_lt_30_share": (fp.get("regime") or {}).get("adx_lt_30_share"),
        },
        "health": {
            "score": health.get("health"),
            "ladder": (health.get("ladder") or {}).get("label"),
            "would_pause_new": health.get("would_pause_new"),
            "warning_active": (health.get("persistence") or {}).get("warning_active"),
            "formula": formula,
            "n_baskets": health.get("n_baskets_total"),
            "on_demo_path": health_on_demo,
            "artifact": str(HEALTH_LATEST_JSON.relative_to(REPO_ROOT)).replace("\\", "/")
            if HEALTH_LATEST_JSON.is_file()
            else None,
        },
        "sync": {
            "source": sync_source,
            "age_hours": age_hours,
            "stale": stale,
            "baskets_rows": baskets_rows,
            "baskets_bytes": hb.get("baskets_bytes") or src_map.get("baskets_bytes"),
            "header_only": header_only,
            "baskets_locked": bool(hb.get("baskets_locked") or src_map.get("baskets_locked") == "1"),
            "heartbeat": str(HEARTBEAT_JSON.relative_to(REPO_ROOT)).replace("\\", "/")
            if HEARTBEAT_JSON.is_file()
            else None,
        },
        "runs": {
            "lock_run_id": (lock_run or {}).get("run_id"),
            "recent": [
                {
                    "run_id": r.get("run_id"),
                    "role": r.get("role"),
                    "pf": (r.get("metrics") or {}).get("profit_factor"),
                }
                for r in runs
            ],
        },
        "live": {
            "latest_baskets_exists": LATEST_BASKETS.is_file(),
            "latest_source": source or None,
            "pause_flag_live": pause_flag,
            "observatory": str(OBSERVATORY_MD.relative_to(REPO_ROOT)).replace("\\", "/")
            if OBSERVATORY_MD.is_file()
            else None,
        },
        "wire": {
            "InpReadPauseNewFlag": "false (default - do not wire yet)",
            "pause_policy": "AI/kb/pause_policy.md",
        },
        "governance": {
            "raci": "AI/kb/raci.md",
            "research_sop": "AI/kb/research_loop_sop.md",
            "rediscovery_policy": "AI/kb/retrain_rediscovery_policy.md",
            "genome": "AI/kb/genome_PRODUCTION.json",
            "telemetry_checklist": "AI/kb/telemetry_checklist.md",
            "wave6_park_freeze": "AI/kb/wave6_park_freeze.md",
        },
        "start_here": [
            "edgelifecycle.md",
            "infrascaleup.md",
            "AI/STATUS.md",
            "AI/kb/versions.json",
            "AI/kb/lineage.json",
            "AI/kb/genome_PRODUCTION.md",
            "AI/schemas/market_fingerprint.schema.json",
            "AI/certificate_PRODUCTION_EURUSD.json",
            "System Profile EURUSD.md",
        ],
    }


def render_md(data: dict[str, Any]) -> str:
    h = data["health"]
    r = data["runs"]
    s = data.get("sync") or {}
    lines = [
        "# FEMA STATUS",
        "",
        f"_Generated: `{data['generated_at']}` - refresh with `cd AI && python -m fema_ops status`_",
        "",
        "## At a glance",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| **Phase** | {data['phase']} |",
        f"| **Open ESR** | `{data['open_esr']}` |",
        f"| **EA build** | v{data['ea_build_target']} |",
        f"| **Preset** | `{data['preset']}` |",
        f"| **Health** | {h.get('score') if h.get('score') is not None else 'n/a'} "
        f"/ ladder `{h.get('ladder') or 'n/a'}` / would_pause=`{h.get('would_pause_new')}` "
        f"/ formula=`{h.get('formula') or 'n/a'}` |",
        f"| **Health on demo path** | {h.get('on_demo_path')} |",
        f"| **Versions** | [`kb/versions.json`](kb/versions.json) · "
        f"health=`{(data.get('versions') or {}).get('health_model')}` · "
        f"cert_v=`{(data.get('versions') or {}).get('certificate')}` · "
        f"gates=`{(data.get('versions') or {}).get('gate_rules')}` |",
        f"| **Lineage lock** | `{(data.get('lineage') or {}).get('active_run_id') or 'n/a'}` · "
        f"parent=`{(data.get('lineage') or {}).get('parent_preset_id') or 'n/a'}` |",
        f"| **Compat (shadow)** | `{(data.get('compatibility') or {}).get('signal') or 'n/a'}` · "
        f"score=`{(data.get('compatibility') or {}).get('score')}` |",
        f"| **Sync source** | `{s.get('source')}` · age_h=`{s.get('age_hours')}` · "
        f"stale=`{s.get('stale')}` · locked=`{s.get('baskets_locked')}` · "
        f"rows=`{s.get('baskets_rows')}` · header_only=`{s.get('header_only')}` |",
        f"| **Lock run_id** | `{r.get('lock_run_id') or 'n/a'}` |",
        f"| **Pause wire** | {data['wire']['InpReadPauseNewFlag']} |",
        f"| **Live baskets** | {'yes' if data['live']['latest_baskets_exists'] else 'missing'} |",
        "",
        "## Start here (agents)",
        "",
        "1. [`../edgelifecycle.md`](../edgelifecycle.md) - spine",
        "2. [`../infrascaleup.md`](../infrascaleup.md) - Ops Plane / §16 roadmap",
        "3. This file - glance",
        "4. [`kb/versions.json`](kb/versions.json) · [`kb/lineage.json`](kb/lineage.json) · [`kb/raci.md`](kb/raci.md)",
        "5. [`certificate_PRODUCTION_EURUSD.json`](certificate_PRODUCTION_EURUSD.json) - bands",
        "6. [`data/live/observatory_daily.md`](data/live/observatory_daily.md) - daily note",
        "7. [`data/live/latest_baskets.csv`](data/live/latest_baskets.csv) - telemetry (gitignored)",
        "8. [`../System Profile EURUSD.md`](../System%20Profile%20EURUSD.md) - lock profile",
        "",
        "## Recent runs",
        "",
    ]
    if r.get("recent"):
        lines.append("| run_id | role | PF |")
        lines.append("| ------ | ---- | -- |")
        for row in r["recent"]:
            lines.append(
                f"| `{row.get('run_id')}` | {row.get('role')} | {row.get('pf')} |"
            )
    else:
        lines.append("_No runs in `kb/runs/index.json`._")
    lines.extend(
        [
            "",
            "## Quick commands",
            "",
            "```powershell",
            "cd AI",
            "python -m fema_ops ingest --source demo",
            "python -m fema_ops health",
            "python -m fema_ops fingerprint",
            "python -m fema_ops observatory",
            "python -m fema_ops status",
            "python -m fema_ops ingest --source tester   # Discovery/tester only",
            "```",
            "",
            "## Doc map (spine only)",
            "",
            "| Doc | Role |",
            "| --- | ---- |",
            "| [`edgelifecycle.md`](../edgelifecycle.md) | Spine / TOC |",
            "| [`infrascaleup.md`](../infrascaleup.md) | Ops Plane + §16 roadmap |",
            "| [`edgescaleuproadmap.md`](../edgescaleuproadmap.md) | Weekly ESR |",
            "| [`edgecontainment.md`](../edgecontainment.md) | Vision / bands |",
            "| [`Edge Discovery.md`](../Edge%20Discovery.md) | Lock table |",
            "| [`kb/genome_PRODUCTION.md`](kb/genome_PRODUCTION.md) | Edge Genome v0 |",
            "| [`kb/pause_policy.md`](kb/pause_policy.md) | EL6 pause |",
            "| [`kb/raci.md`](kb/raci.md) | Governance RACI |",
            "| [`kb/research_loop_sop.md`](kb/research_loop_sop.md) | Research loop |",
            "| [`kb/retrain_rediscovery_policy.md`](kb/retrain_rediscovery_policy.md) | EL7 cadence |",
            "| [`templates/daily_health.md`](templates/daily_health.md) | Daily runbook |",
            "| [`aiedgecontain.md`](../aiedgecontain.md) | Contain archive |",
            "| [`ai_enhance.md`](../ai_enhance.md) | Legacy archive |",
            "",
            "## Notes",
            "",
            f"- Health artifact: `{h.get('artifact') or 'run health first'}`",
            f"- Fingerprint: `{(data.get('fingerprint') or {}).get('artifact') or 'run fingerprint'}`",
            f"- Sync heartbeat: `{s.get('heartbeat') or 'run ingest first'}`",
            f"- Observatory: `{data['live'].get('observatory') or 'run observatory'}`",
            f"- Live source excerpt: `{(data['live'].get('latest_source') or 'n/a')[:180]}`",
            f"- Live pause_new.flag present: `{data['live']['pause_flag_live']}`",
            "- Fat CSVs under `AI/data/` are gitignored; schemas + templates are committed.",
            "- **EL4:** prefer `--source demo` (Common `FEMA_AI`). Tester collect is not demo health.",
            "",
        ]
    )
    return "\n".join(lines)


def write_status() -> dict[str, Any]:
    data = gather()
    STATUS_MD.write_text(render_md(data), encoding="utf-8")
    STATUS_JSON.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    data["artifacts"] = {
        "md": str(STATUS_MD).replace("\\", "/"),
        "json": str(STATUS_JSON).replace("\\", "/"),
    }
    return data
