#!/usr/bin/env python3
"""Load PRODUCTION edge certificate (INF-CERT)."""

from __future__ import annotations

import json
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parent
DEFAULT_CERT = _AI_DIR / "certificate_PRODUCTION_EURUSD.json"


def load_certificate(path: Path | None = None) -> dict:
    p = path or DEFAULT_CERT
    data = json.loads(p.read_text(encoding="utf-8"))
    w = data.get("health_weights") or {}
    s = sum(float(v) for v in w.values())
    if w and abs(s - 1.0) > 1e-6:
        raise ValueError(f"health_weights must sum to 1.0, got {s}")
    return data


def ladder_label(health: float, cert: dict | None = None) -> dict:
    """Return action_ladder row for a health score 0-100."""
    c = cert or load_certificate()
    rows = sorted(c["action_ladder"], key=lambda r: float(r["health_min"]), reverse=True)
    for row in rows:
        if health >= float(row["health_min"]):
            return row
    return rows[-1]


if __name__ == "__main__":
    cert = load_certificate()
    print(f"preset={cert['preset']} windows={cert['rolling_windows_baskets']}")
    print(f"birth PF={cert['birth_metrics']['profit_factor']} WR={cert['birth_metrics']['win_rate']}")
    print(f"ladder@90={ladder_label(90)['label']} @55={ladder_label(55)['label']} @20={ladder_label(20)['label']}")
