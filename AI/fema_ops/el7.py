"""EL7 dry-run + experiment index (Wave 4)."""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_AI_DIR = Path(__file__).resolve().parent.parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from paths import (  # noqa: E402
    CANDIDATES_CSV,
    HEALTH_LATEST_JSON,
    KB_DIR,
    KB_RUNS_DIR,
    LINEAGE_JSON,
    LIVE_DIR,
    REPO_ROOT,
)

EL7_DRY_RUN = KB_DIR / "el7_dry_run_latest.json"
EXPERIMENTS_INDEX = KB_DIR / "experiments_index.json"
SCORECARD = KB_DIR / "el2_gate_scorecard.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def evaluate_el7_trigger(health: dict[str, Any] | None = None) -> dict[str, Any]:
    """IS-EL7-01 — map ladder + persistence → Discovery open recommendation."""
    health = health if health is not None else (_load(HEALTH_LATEST_JSON) or {})
    ladder = (health.get("ladder") or {}).get("label") or "unknown"
    pers = health.get("persistence") or {}
    warn = bool(pers.get("warning_active"))
    det = int(pers.get("consecutive_deteriorate") or 0)
    score = health.get("health")

    # Trigger table (also documented in edgelifecycle / el7_trigger_table.md)
    open_discovery = False
    reason = "none"
    priority = "none"
    if ladder == "retire":
        open_discovery = True
        reason = "ladder_retire"
        priority = "high"
    elif ladder == "re_discovery" and warn:
        open_discovery = True
        reason = "re_discovery_and_persistence"
        priority = "high"
    elif ladder == "re_discovery":
        open_discovery = False
        reason = "re_discovery_without_persistence_wait"
        priority = "medium"
    elif ladder == "watch" and warn and det >= 3:
        open_discovery = True
        reason = "watch_persistence_met"
        priority = "medium"
    elif ladder in ("watch", "investigate"):
        reason = "queue_offline_notes_only"
        priority = "low"

    return {
        "schema": "fema_el7_trigger_v0",
        "computed_at": _utc_now(),
        "ladder": ladder,
        "health": score,
        "warning_active": warn,
        "consecutive_deteriorate": det,
        "open_discovery": open_discovery,
        "reason": reason,
        "priority": priority,
        "pause_hint": bool(health.get("would_pause_new")),
        "note": "Human opens Discovery; this is a recommendation only.",
    }


def el7_dry_run(*, apply_lineage: bool = False) -> dict[str, Any]:
    """IS-EL7-02 dry-run: snapshot plan without mutating lock unless apply_lineage."""
    trigger = evaluate_el7_trigger()
    lineage = _load(LINEAGE_JSON) or {}
    active = dict(lineage.get("active_lock") or {})
    lock_run = active.get("run_id")

    plan = {
        "schema": "fema_el7_dry_run_v0",
        "computed_at": _utc_now(),
        "trigger": trigger,
        "steps": [
            {
                "id": "EL7-002",
                "action": "snapshot_lock_as_retired_parent",
                "set_retired_run_id": lock_run,
                "parent_preset_id": active.get("preset_id") or "PRODUCTION",
            },
            {
                "id": "EL7-003",
                "action": "open_EL1_canonical_window",
                "window": {"start": "2026.01.01", "end": "2026.07.31"},
                "max_candidates": 3,
                "factory": "python -m fema_ops recommend && python -m fema_ops factory --apply --index 0",
            },
            {
                "id": "EL7-004",
                "action": "promote_via_EL2_checklist_only",
                "gates": "AI/kb/gate_rules.json",
                "checklist": "AI/templates/promotion_checklist.md",
            },
            {
                "id": "EL7-005",
                "action": "if_no_promote_keep_last_acceptable_lock",
                "lock_run_id": lock_run,
            },
        ],
        "lineage_before": {
            "active_run_id": lock_run,
            "retired_run_id": active.get("retired_run_id"),
            "parent_preset_id": active.get("parent_preset_id"),
        },
        "applied": False,
        "dry_run": True,
    }

    if apply_lineage and trigger.get("open_discovery") and lock_run:
        active["retired_run_id"] = lock_run
        lineage["active_lock"] = active
        lineage["updated"] = _utc_now()[:10]
        LINEAGE_JSON.write_text(json.dumps(lineage, indent=2) + "\n", encoding="utf-8")
        plan["applied"] = True
        plan["dry_run"] = False
        plan["note"] = "Lineage retired_run_id set — complete EL1/EL2 manually"
    else:
        plan["note"] = (
            "Dry-run only — lineage not mutated. "
            "Use --apply only when human opens Re-Discovery."
        )

    KB_DIR.mkdir(parents=True, exist_ok=True)
    EL7_DRY_RUN.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    plan["artifact"] = str(EL7_DRY_RUN.relative_to(REPO_ROOT)).replace("\\", "/")
    return plan


def build_experiments_index() -> dict[str, Any]:
    """RG-KB-02 — join scorecard + fingerprint + lineage parent + failure_reason."""
    scorecard = _load(SCORECARD) or {}
    lineage = _load(LINEAGE_JSON) or {}
    active = lineage.get("active_lock") or {}
    parent_lock = active.get("run_id")

    cand_by_id: dict[str, dict[str, str]] = {}
    if CANDIDATES_CSV.is_file():
        with CANDIDATES_CSV.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                cand_by_id[str(row.get("id") or "")] = row

    experiments: list[dict[str, Any]] = []
    for row in scorecard.get("rows") or []:
        run_id = row.get("run_id")
        preset = row.get("preset")
        fp_path = KB_RUNS_DIR / str(run_id) / "fingerprint.json" if run_id else None
        cand = cand_by_id.get(str(preset) or "", {})
        experiments.append(
            {
                "preset": preset,
                "run_id": run_id,
                "status": row.get("status") or row.get("decision"),
                "failure_reason": row.get("failure_reason")
                or (row.get("g1") or {}).get("failure_reason")
                or cand.get("failure_reason")
                or "",
                "parent_lock_run_id": parent_lock,
                "lineage_parent_preset": active.get("parent_preset_id"),
                "fingerprint": bool(fp_path.is_file()) if fp_path else False,
                "fingerprint_path": (
                    str(fp_path.relative_to(REPO_ROOT)).replace("\\", "/")
                    if fp_path and fp_path.is_file()
                    else None
                ),
                "subsystem": cand.get("subsystem") or "",
            }
        )

    out = {
        "schema": "fema_experiments_index_v0",
        "computed_at": _utc_now(),
        "n": len(experiments),
        "with_fingerprint": sum(1 for e in experiments if e.get("fingerprint")),
        "with_failure_reason": sum(1 for e in experiments if e.get("failure_reason")),
        "active_lock_run_id": parent_lock,
        "experiments": experiments,
        "gap": "Fingerprint present only where fema_ops fingerprint --run-id was run; lock has FP from Wave 3.",
    }
    EXPERIMENTS_INDEX.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    out["artifact"] = str(EXPERIMENTS_INDEX.relative_to(REPO_ROOT)).replace("\\", "/")
    return out
