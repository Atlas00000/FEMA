"""Backfill pause false-positive check (EL6-003)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_AI_DIR = Path(__file__).resolve().parent.parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from cert_loader import ladder_label, load_certificate  # noqa: E402
from paths import CERTIFICATE_JSON, LATEST_BASKETS, LIVE_DIR  # noqa: E402

from .health import load_baskets, score_window
from .pause import would_pause_new
from .persistence import PersistenceState, update_persistence


def backfill_pause_check(
    baskets_path: Path | None = None,
    *,
    step: int = 25,
    cert_path: Path | None = None,
) -> dict[str, Any]:
    """Walk expanding history; score primary window at each step; count would_pause rate."""
    cert = load_certificate(cert_path or CERTIFICATE_JSON)
    rows = load_baskets(baskets_path or LATEST_BASKETS)
    primary_n = int(cert.get("primary_window_baskets") or 100)
    pers_cfg = cert.get("persistence") or {}
    det_need = int(pers_cfg.get("deteriorate_windows") or 3)
    rec_need = int(pers_cfg.get("recover_windows") or 2)

    if len(rows) < primary_n + step:
        return {
            "status": "insufficient_rows",
            "n": len(rows),
            "need": primary_n + step,
            "pause_rate": None,
            "ok_not_always_on": None,
        }

    state = PersistenceState()
    snapshots = []
    for end in range(primary_n, len(rows) + 1, step):
        slice_rows = rows[:end]
        block = score_window(slice_rows, primary_n, cert, None)
        health = float(block["health"])
        label = str(block["ladder"]["label"])
        flags = update_persistence(
            state, health, label, deteriorate_need=det_need, recover_need=rec_need
        )
        pause = would_pause_new(health, label, flags)
        snapshots.append(
            {
                "end_i": end,
                "open_last": slice_rows[-1].get("open_time", ""),
                "health": health,
                "label": label,
                "warning_active": flags["warning_active"],
                "would_pause_new": pause["would_pause_new"],
                "reason": pause["reason"],
            }
        )

    n = len(snapshots)
    pause_n = sum(1 for s in snapshots if s["would_pause_new"])
    pause_rate = pause_n / n if n else 0.0
    # Must not be always-on: allow up to 40% on multi-year weak collect
    ok = pause_rate < 0.40
    out = {
        "status": "ok" if ok else "always_on_risk",
        "n_snapshots": n,
        "pause_n": pause_n,
        "pause_rate": round(pause_rate, 4),
        "ok_not_always_on": ok,
        "step": step,
        "primary_window": primary_n,
        "source": str(baskets_path or LATEST_BASKETS).replace("\\", "/"),
        "note": (
            "EL6-003: pause_rate must stay well below 1.0 on backfill. "
            "Wire only if ok_not_always_on and operator trusts demo feel."
        ),
        "snapshots_tail": snapshots[-8:],
    }
    out_path = LIVE_DIR / "pause_check_latest.json"
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    out["artifact"] = str(out_path).replace("\\", "/")
    return out
