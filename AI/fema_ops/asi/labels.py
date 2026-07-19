"""ASI-P1-01 — steamroller / expansion-fail labels from basket outcomes."""

from __future__ import annotations

from typing import Any


def _f(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def _i(row: dict, key: str, default: int = 0) -> int:
    try:
        return int(float(row.get(key, default) or default))
    except (TypeError, ValueError):
        return default


def classify_basket(row: dict, *, stress_depth: int = 4) -> dict[str, Any]:
    """Return label fields for one closed basket (outcome known — not for open-time inference)."""
    hit_bsl = _i(row, "hit_bsl")
    hit_tp = _i(row, "hit_tp")
    profit = _f(row, "profit")
    max_depth = _i(row, "max_depth")
    mae = _f(row, "mae")
    exit_reason = str(row.get("exit_reason", "") or "")

    if hit_bsl == 1 or exit_reason == "BASKET_SL":
        label_class = "steamroller_bsl"
        y_steamroller = 1
    elif max_depth >= stress_depth and profit < 0:
        label_class = "expansion_stress"
        y_steamroller = 1
    elif hit_tp == 1 or profit > 0:
        label_class = "winner"
        y_steamroller = 0
    else:
        label_class = "other_loss"
        y_steamroller = 0

    # Legacy EC0 / AI2 compat
    y_fail = 1 if hit_bsl == 1 or mae <= -20.0 else 0

    return {
        "label_class": label_class,
        "y_steamroller": y_steamroller,
        "y_fail": y_fail,
    }


def label_summary(rows: list[dict]) -> dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {"n": 0}
    classes: dict[str, int] = {}
    y_steam = 0
    y_fail = 0
    for row in rows:
        lab = classify_basket(row)
        classes[lab["label_class"]] = classes.get(lab["label_class"], 0) + 1
        y_steam += lab["y_steamroller"]
        y_fail += lab["y_fail"]
    return {
        "n": n,
        "y_steamroller": y_steam,
        "y_steamroller_rate": round(y_steam / n, 4),
        "y_fail": y_fail,
        "y_fail_rate": round(y_fail / n, 4),
        "label_class": classes,
    }
