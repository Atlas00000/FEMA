"""Ops daily/offline pipeline — runs without waiting for demo health (Wave 5+)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

_AI_DIR = Path(__file__).resolve().parent.parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from csv_util import read_csv_rows  # noqa: E402
from paths import LATEST_BASKETS, LIVE_DIR, REPO_ROOT  # noqa: E402

PIPELINE_LATEST = LIVE_DIR / "pipeline_latest.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _step(name: str, fn: Callable[[], Any]) -> dict[str, Any]:
    try:
        out = fn()
        return {"name": name, "ok": True, "result": out}
    except SystemExit as e:
        return {"name": name, "ok": False, "error": f"SystemExit:{e}"}
    except Exception as e:  # noqa: BLE001
        return {"name": name, "ok": False, "error": str(e)}


def _basket_rows() -> int:
    if not LATEST_BASKETS.is_file():
        return 0
    try:
        return len(read_csv_rows(LATEST_BASKETS))
    except OSError:
        return 0


def run_pipeline(
    *,
    source: str = "demo",
    allow_empty: bool = True,
    with_db: bool = False,
    with_ci: bool = False,
    with_archive: bool = True,
) -> dict[str, Any]:
    """Ingest → (health if rows) → FP → drift → recommend → observatory → status.

    Health is skipped cleanly when demo CSV is header-only — finish Wave 0 later.
    """
    steps: list[dict[str, Any]] = []
    notes: list[str] = []

    def ingest() -> dict[str, Any]:
        from fema_ops.ingest import run_ingest

        code = run_ingest(source=source, magic="", from_dir=None, allow_empty=allow_empty)
        return {"exit": code, "source": source}

    steps.append(_step("ingest", ingest))

    n = _basket_rows()
    health_ran = False
    if n > 0:
        def health() -> dict[str, Any]:
            from fema_ops.health import ascii_summary, run_health

            report = run_health(update_state=True)
            return {
                "summary": ascii_summary(report),
                "score": report.get("health"),
                "ladder": (report.get("ladder") or {}).get("label"),
                "compat": (report.get("compatibility") or {}).get("signal"),
            }

        steps.append(_step("health", health))
        health_ran = True

        def fingerprint() -> dict[str, Any]:
            from fema_ops.fingerprint import write_fingerprint

            out = write_fingerprint(window=100, attach_run=True)
            c = out.get("compatibility") or {}
            return {"compat": c.get("signal"), "score": c.get("score")}

        steps.append(_step("fingerprint", fingerprint))
    else:
        notes.append(
            f"health/fingerprint skipped — latest_baskets has {n} rows "
            "(header-only or missing). Re-run after demo basket close."
        )
        steps.append(
            {
                "name": "health",
                "ok": True,
                "skipped": True,
                "reason": "no_closed_baskets",
            }
        )
        steps.append(
            {
                "name": "fingerprint",
                "ok": True,
                "skipped": True,
                "reason": "no_closed_baskets",
            }
        )

    def drift() -> dict[str, Any]:
        from fema_ops.drift import detect_drift

        r = detect_drift()
        return {"severity": r.get("severity"), "n_alerts": r.get("n_alerts")}

    steps.append(_step("drift", drift))

    def recommend() -> dict[str, Any]:
        from fema_ops.factory import write_recommend

        r = write_recommend()
        return {
            "compat": r.get("compat_signal"),
            "cloneable": len(r.get("cloneable") or []),
        }

    steps.append(_step("recommend", recommend))

    if with_archive and LATEST_BASKETS.is_file():
        def archive() -> dict[str, Any]:
            from fema_ops.artifacts import archive_from_live

            return archive_from_live(source=source, role="demo" if source == "demo" else "collect")

        steps.append(_step("artifacts_archive", archive))

    if with_db:
        def db_ingest() -> dict[str, Any]:
            from fema_ops.db_ingest import ingest_from_live

            return ingest_from_live(source=source)

        steps.append(_step("db_ingest", db_ingest))

    if with_ci:
        def ci() -> dict[str, Any]:
            from fema_ops.ci_gates import run_ci_gates

            out = run_ci_gates(refresh_openapi=True)
            return {"ok": out.get("ok")}

        steps.append(_step("ci_gates", ci))

    def observatory() -> dict[str, Any]:
        from fema_ops.observatory import write_observatory

        r = write_observatory()
        return {"action": r.get("action"), "source": r.get("source")}

    steps.append(_step("observatory", observatory))

    def status() -> dict[str, Any]:
        from fema_ops.status import write_status

        data = write_status()
        return {
            "phase": data.get("phase"),
            "on_demo_path": (data.get("health") or {}).get("on_demo_path"),
            "header_only": (data.get("sync") or {}).get("header_only"),
            "locked": (data.get("sync") or {}).get("baskets_locked"),
        }

    steps.append(_step("status", status))

    failed = [s["name"] for s in steps if not s.get("ok") and not s.get("skipped")]
    report = {
        "schema": "fema_pipeline_v0",
        "computed_at": _utc_now(),
        "source": source,
        "basket_rows": n,
        "health_ran": health_ran,
        "ok": len(failed) == 0,
        "failed": failed,
        "notes": notes,
        "steps": [
            {
                "name": s["name"],
                "ok": s.get("ok"),
                "skipped": s.get("skipped"),
                "reason": s.get("reason"),
                "error": s.get("error"),
                "result": s.get("result") if s.get("ok") and not s.get("skipped") else None,
            }
            for s in steps
        ],
    }
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    PIPELINE_LATEST.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["artifact"] = str(PIPELINE_LATEST.relative_to(REPO_ROOT)).replace("\\", "/")
    return report
