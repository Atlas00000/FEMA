"""Drift detection vs birth / genome (IS-DRIFT-01)."""

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
    LIVE_DIR,
    REPO_ROOT,
)

DRIFT_LATEST = LIVE_DIR / "drift_latest.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def detect_drift() -> dict[str, Any]:
    cert = _load(CERTIFICATE_JSON)
    health = _load(HEALTH_LATEST_JSON)
    fp = _load(FINGERPRINT_LATEST)
    compat = _load(COMPAT_LATEST) or health.get("compatibility") or {}
    birth = cert.get("birth_metrics") or {}
    primary_n = str(cert.get("primary_window_baskets") or 100)
    window = (health.get("windows") or {}).get(primary_n) or {}
    metrics = window.get("metrics") or {}
    components = window.get("components") or {}

    alerts: list[dict[str, Any]] = []

    def alert(kind: str, detail: str, severity: str = "warn") -> None:
        alerts.append({"kind": kind, "detail": detail, "severity": severity})

    # Health component breaches
    for name, score in components.items():
        try:
            s = float(score)
        except (TypeError, ValueError):
            continue
        if s < 55:
            alert("component_low", f"{name}={s:.1f}<55", "warn")
        if s < 40:
            alert("component_critical", f"{name}={s:.1f}<40", "high")

    # Birth deltas
    birth_pf = birth.get("profit_factor")
    live_pf = metrics.get("pf")
    if birth_pf and live_pf is not None and float(live_pf) < float(birth_pf) * 0.85:
        alert(
            "pf_vs_birth",
            f"pf={live_pf} vs birth={birth_pf} (<85%)",
            "high",
        )
    birth_depth = birth.get("avg_depth")
    live_depth = metrics.get("avg_depth") or (fp.get("pullback") or {}).get("avg_depth")
    if birth_depth and live_depth is not None and float(live_depth) > float(birth_depth) * 1.25:
        alert(
            "depth_vs_birth",
            f"depth={live_depth} vs birth={birth_depth} (>125%)",
            "warn",
        )

    # Compatibility / fingerprint
    sig = compat.get("signal")
    if sig == "investigate":
        alert("compat_investigate", f"score={compat.get('score')}", "high")
    elif sig == "watch":
        alert("compat_watch", f"score={compat.get('score')}", "warn")

    for tag in health.get("drift_tags") or []:
        alert("health_tag", str(tag), "warn")

    severity = "ok"
    if any(a["severity"] == "high" for a in alerts):
        severity = "high"
    elif alerts:
        severity = "warn"

    report = {
        "schema": "fema_drift_v0",
        "computed_at": _utc_now(),
        "severity": severity,
        "n_alerts": len(alerts),
        "alerts": alerts,
        "health": {
            "score": health.get("health"),
            "ladder": (health.get("ladder") or {}).get("label"),
            "formula": health.get("formula_version"),
        },
        "compat_signal": sig,
        "suggest_subsystems": compat.get("suggest_subsystems") or [],
        "shadow": True,
        "note": "Shadow drift job — does not pause or retune.",
    }
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    DRIFT_LATEST.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["artifact"] = str(DRIFT_LATEST.relative_to(REPO_ROOT)).replace("\\", "/")
    return report
