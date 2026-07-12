"""Edge Observatory daily note — health + fingerprint + lineage (RG-OBS-02)."""

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
    COMPAT_LATEST,
    FINGERPRINT_LATEST,
    HEALTH_LATEST_JSON,
    HEALTH_LATEST_MD,
    LATEST_BASKETS,
    LATEST_SOURCE,
    LINEAGE_JSON,
    LIVE_DIR,
    REPO_ROOT,
)

OUT_MD = LIVE_DIR / "observatory_daily.md"
OUT_JSON = LIVE_DIR / "observatory_daily.json"
HEARTBEAT = LIVE_DIR / "sync_heartbeat.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _parse_source_txt() -> dict[str, str]:
    out: dict[str, str] = {}
    if not LATEST_SOURCE.is_file():
        return out
    for line in LATEST_SOURCE.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def build_report() -> dict[str, Any]:
    health = _load(HEALTH_LATEST_JSON)
    hb = _load(HEARTBEAT)
    src = _parse_source_txt()
    fp = _load(FINGERPRINT_LATEST) or health.get("fingerprint") or {}
    compat = _load(COMPAT_LATEST) or health.get("compatibility") or {}
    lineage = _load(LINEAGE_JSON)
    active = lineage.get("active_lock") or {}
    drift = _load(LIVE_DIR / "drift_latest.json")

    ladder = (health.get("ladder") or {}).get("label")
    score = health.get("health")
    would_pause = health.get("would_pause_new")
    source = hb.get("source") or src.get("source") or "unknown"
    rows = hb.get("baskets_rows")
    if rows is None and src.get("baskets_rows"):
        try:
            rows = int(src["baskets_rows"])
        except ValueError:
            rows = None
    age = hb.get("age_hours")
    if age is None and src.get("age_hours") not in (None, "", "None"):
        try:
            age = float(src["age_hours"])
        except ValueError:
            age = None
    stale = bool(hb.get("stale") or src.get("stale") == "1")
    header_only = bool(hb.get("header_only") or src.get("header_only") == "1")

    action = "do_nothing"
    notes: list[str] = []
    if not LATEST_BASKETS.is_file():
        action = "sync_required"
        notes.append("latest_baskets.csv missing — run ingest --source demo|tester")
    elif hb.get("baskets_locked") or src.get("baskets_locked") == "1":
        action = "sync_partial_locked"
        notes.append(
            "Demo baskets.csv exclusive-locked by MT5; meta/config synced. "
            "Re-ingest after basket close (not Sunday-forced)."
        )
    elif header_only or (isinstance(rows, int) and rows == 0):
        action = "wait_for_basket_close"
        notes.append(
            "CSV header-only or zero closed baskets — Observatory health not meaningful yet"
        )
    elif source == "tester" and action == "do_nothing":
        notes.append(
            "WARNING: live pointer source=tester — not demo EL4 path; "
            "prefer `fema_ops ingest --source demo`"
        )
    elif stale:
        action = "investigate_stale"
        notes.append(f"Basket file age_hours={age} (>24h) while expecting updates")
    elif ladder in ("re_discovery", "retire"):
        action = "human_review"
        notes.append(f"Ladder={ladder} — review pause policy / EL7; do not auto-retune")
    elif ladder in ("watch", "investigate"):
        action = "human_review"
        notes.append(f"Ladder={ladder} — continue PRODUCTION; queue offline notes only")

    sig = compat.get("signal")
    if sig == "investigate" and action == "do_nothing":
        action = "human_review"
        notes.append(
            f"Compatibility signal=investigate — review genome mismatches "
            f"(suggest: {', '.join(compat.get('suggest_subsystems') or []) or 'n/a'}); "
            "shadow only, no EA change"
        )
    elif sig == "watch":
        notes.append("Compatibility=watch — fingerprint drifting vs PRODUCTION genome")

    if drift.get("severity") in ("warn", "high"):
        notes.append(
            f"Drift severity={drift.get('severity')} "
            f"n_alerts={drift.get('n_alerts')} — see drift_latest.json"
        )
        if drift.get("severity") == "high" and action == "do_nothing":
            action = "human_review"

    report = {
        "phase": "RG-OBS-02",
        "generated_at": _utc_now(),
        "action": action,
        "source": source,
        "health": {
            "score": score,
            "ladder": ladder,
            "would_pause_new": would_pause,
            "n_baskets": health.get("n_baskets_total"),
            "formula": health.get("formula_version"),
        },
        "sync": {
            "age_hours": age,
            "stale": stale,
            "baskets_rows": rows,
            "baskets_bytes": hb.get("baskets_bytes") or src.get("baskets_bytes"),
            "header_only": header_only,
            "baskets_src": hb.get("baskets_src") or src.get("baskets_src"),
        },
        "lineage": {
            "active_run_id": active.get("run_id"),
            "parent_preset_id": active.get("parent_preset_id"),
            "retired_run_id": active.get("retired_run_id"),
            "preset_id": active.get("preset_id"),
        },
        "fingerprint": {
            "schema": fp.get("schema"),
            "n_baskets": (fp.get("window") or {}).get("n_baskets"),
            "adx_lt_30_share": (fp.get("regime") or {}).get("adx_lt_30_share"),
            "avg_depth": (fp.get("pullback") or {}).get("avg_depth"),
            "asia_share": (fp.get("session") or {}).get("asia_share"),
            "mae_abs_mean": (fp.get("volatility") or {}).get("mae_abs_mean"),
        },
        "compatibility": {
            "score": compat.get("score"),
            "signal": sig,
            "suggest_subsystems": compat.get("suggest_subsystems") or [],
            "shadow": True,
        },
        "drift": {
            "severity": drift.get("severity"),
            "n_alerts": drift.get("n_alerts"),
            "alerts": (drift.get("alerts") or [])[:5],
        },
        "notes": notes,
        "default": "do nothing unless persistence warning / retire ladder / compat investigate",
    }
    return report


def render_md(report: dict[str, Any]) -> str:
    h = report["health"]
    s = report["sync"]
    lin = report.get("lineage") or {}
    fp = report.get("fingerprint") or {}
    c = report.get("compatibility") or {}
    lines = [
        "# Edge Observatory — daily",
        "",
        f"**Generated:** `{report['generated_at']}`  ",
        f"**Phase:** `{report['phase']}`  ",
        f"**Action:** `{report['action']}`  ",
        f"**Source:** `{report['source']}`  ",
        f"**Default:** {report['default']}",
        "",
        "## Health",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| Score | {h.get('score')} |",
        f"| Ladder | `{h.get('ladder')}` |",
        f"| would_pause_new | {h.get('would_pause_new')} |",
        f"| n_baskets | {h.get('n_baskets')} |",
        f"| formula | {h.get('formula')} |",
        "",
        "## Lineage",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| Lock | `{lin.get('preset_id')}` / `{lin.get('active_run_id')}` |",
        f"| Parent | `{lin.get('parent_preset_id')}` |",
        f"| Retired | `{lin.get('retired_run_id')}` |",
        "",
        "## Fingerprint (window)",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| n_baskets | {fp.get('n_baskets')} |",
        f"| adx_lt_30_share | {fp.get('adx_lt_30_share')} |",
        f"| avg_depth | {fp.get('avg_depth')} |",
        f"| asia_share | {fp.get('asia_share')} |",
        f"| mae_abs_mean | {fp.get('mae_abs_mean')} |",
        "",
        "## Compatibility (shadow)",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| Signal | `{c.get('signal')}` |",
        f"| Score | {c.get('score')} |",
        f"| Suggest | {', '.join(c.get('suggest_subsystems') or []) or 'none'} |",
        "",
        "## Drift",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| Severity | `{(report.get('drift') or {}).get('severity')}` |",
        f"| n_alerts | {(report.get('drift') or {}).get('n_alerts')} |",
        "",
        "## Sync heartbeat",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| age_hours | {s.get('age_hours')} |",
        f"| stale | {s.get('stale')} |",
        f"| baskets_rows | {s.get('baskets_rows')} |",
        f"| baskets_bytes | {s.get('baskets_bytes')} |",
        f"| header_only | {s.get('header_only')} |",
        "",
        "## Notes",
        "",
    ]
    if report["notes"]:
        for n in report["notes"]:
            lines.append(f"- {n}")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Commands",
            "",
            "```powershell",
            "cd AI",
            "python -m fema_ops ingest --source demo",
            "python -m fema_ops health",
            "python -m fema_ops fingerprint",
            "python -m fema_ops drift",
            "python -m fema_ops observatory",
            "python -m fema_ops status",
            "```",
            "",
            f"Health MD: `{HEALTH_LATEST_MD.relative_to(REPO_ROOT).as_posix() if HEALTH_LATEST_MD.is_file() else 'n/a'}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_observatory() -> dict[str, Any]:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    # Refresh FP if missing so Observatory is self-contained
    if not FINGERPRINT_LATEST.is_file() and LATEST_BASKETS.is_file():
        try:
            from fema_ops.fingerprint import write_fingerprint

            write_fingerprint(attach_run=True)
        except Exception:  # noqa: BLE001
            pass
    if not (LIVE_DIR / "drift_latest.json").is_file():
        try:
            from fema_ops.drift import detect_drift

            detect_drift()
        except Exception:  # noqa: BLE001
            pass
    report = build_report()
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(report), encoding="utf-8")
    report["wrote"] = {
        "md": str(OUT_MD.relative_to(REPO_ROOT)).replace("\\", "/"),
        "json": str(OUT_JSON.relative_to(REPO_ROOT)).replace("\\", "/"),
    }
    return report
