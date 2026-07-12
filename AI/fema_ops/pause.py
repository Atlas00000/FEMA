"""EL6 pause-new shadow helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def would_pause_new(
    health: float,
    ladder_label: str,
    persistence: dict[str, Any] | None,
) -> dict[str, Any]:
    """Shadow decision — does not write EA flag unless operator opts in."""
    pers = persistence or {}
    warning = bool(pers.get("warning_active"))
    label = str(ladder_label or "")

    reason = ""
    pause = False
    if label == "retire":
        pause = True
        reason = "ladder_retire"
    elif label == "re_discovery" and warning:
        pause = True
        reason = "ladder_re_discovery_persistent"
    elif health < 50.0 and warning:
        pause = True
        reason = "health_lt_50_persistent"
    else:
        reason = "keep_running"

    return {
        "would_pause_new": pause,
        "reason": reason,
        "resume_hint": (
            "clear_flag_or_2_recover_windows"
            if pause
            else "n/a"
        ),
    }


def format_flag_body(
    pause: bool,
    *,
    reason: str = "",
    source: str = "health_shadow",
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y.%m.%d %H:%M:%S")
    return (
        f"pause_new={'1' if pause else '0'}\n"
        f"reason={reason}\n"
        f"source={source}\n"
        f"updated={ts}\n"
    )


def write_flag_file(path: Path, pause: bool, reason: str = "", source: str = "human") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_flag_body(pause, reason=reason, source=source), encoding="utf-8")
