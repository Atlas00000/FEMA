"""Candidate factory — recommend ≤3 subsystems + optional goal-driven clone (Wave 4)."""

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
    LIVE_DIR,
    REPO_ROOT,
)

from fema_ops.presets import clone_preset, list_subsystems  # noqa: E402

FACTORY_LATEST = LIVE_DIR / "factory_recommend.json"

# Conservative one-axis recipes (human still reviews before Tester)
DEFAULT_RECIPES: dict[str, list[dict[str, str]]] = {
    "adx": [{"InpAdxMax": "28"}, {"InpAdxMax": "25"}],
    "grid": [{"InpMaxEntryDepth": "4"}, {"InpGridLevels": "4"}],
    "session": [{"InpUseSessionBlockFriClose": "true"}],
    "atr": [{"InpAtrMultiplier": "1.2"}],
    "htf": [{"InpUseHtfFilter": "true", "InpHtfEmaPeriod": "200"}],
    "cooldown": [{"InpCooldownBars": "2"}],
    "basket_exit": [{"InpMaxBasketBars": "480"}],
    "regime_extra": [{"InpUseAtrPercentileGate": "true", "InpAtrPercentileMax": "70"}],
    "entry_filter": [{"InpUseCandleConfirm": "true"}],
    "ema": [{"InpEmaFastPeriod": "18"}],
}

# Genome / compat may emit ids not in search_map
ALIAS_TO_SUBSYSTEM = {
    "execution": None,  # no clone axis — note only
    "spread_exec": None,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def normalize_subsystem(sub: str | None) -> str | None:
    if not sub:
        return None
    if sub in ALIAS_TO_SUBSYSTEM:
        return ALIAS_TO_SUBSYSTEM[sub]
    known = set(list_subsystems())
    return sub if sub in known else None


def recommend(
    *,
    compat: dict[str, Any] | None = None,
    max_n: int = 3,
) -> dict[str, Any]:
    """Offline recommender from compatibility mismatches (RG-FAC-01)."""
    compat = compat if compat is not None else _load(COMPAT_LATEST)
    if not compat and FINGERPRINT_LATEST.is_file():
        from fema_ops.fingerprint import score_compatibility, write_fingerprint

        out = write_fingerprint(attach_run=False)
        compat = out.get("compatibility") or {}

    known = set(list_subsystems())
    suggestions: list[dict[str, Any]] = []
    seen: set[str] = set()

    for sub in compat.get("suggest_subsystems") or []:
        mapped = normalize_subsystem(str(sub))
        if mapped is None:
            suggestions.append(
                {
                    "subsystem": sub,
                    "cloneable": False,
                    "reason": f"no search_map axis for '{sub}' — observe only",
                    "recipe": None,
                    "hypothesis": f"Mismatch tagged {sub}; no safe clone key",
                }
            )
            continue
        if mapped in seen or mapped not in known:
            continue
        seen.add(mapped)
        recipe = (DEFAULT_RECIPES.get(mapped) or [{}])[0]
        if not recipe:
            continue
        mismatch = next(
            (
                m
                for m in (compat.get("mismatches") or [])
                if m.get("subsystem") in (sub, mapped)
            ),
            {},
        )
        suggestions.append(
            {
                "subsystem": mapped,
                "cloneable": True,
                "reason": mismatch.get("key") or "genome_mismatch",
                "value": mismatch.get("value"),
                "recipe": recipe,
                "set_args": [f"{k}={v}" for k, v in recipe.items()],
                "hypothesis": (
                    f"Genome mismatch on {mismatch.get('key') or mapped}; "
                    f"try one-axis {mapped} tweak {recipe}"
                ),
            }
        )
        if len([s for s in suggestions if s.get("cloneable")]) >= max_n:
            break

    # If compatible / empty, still offer empty list (do nothing)
    report = {
        "schema": "fema_factory_recommend_v0",
        "computed_at": _utc_now(),
        "compat_signal": compat.get("signal"),
        "compat_score": compat.get("score"),
        "max_n": max_n,
        "suggestions": suggestions[: max_n + 2],  # allow non-cloneable notes
        "cloneable": [s for s in suggestions if s.get("cloneable")][:max_n],
        "rule": "Human clones; Watch may trigger, not author. <=3 candidates.",
        "shadow": True,
    }
    return report


def write_recommend(**kwargs: Any) -> dict[str, Any]:
    report = recommend(**kwargs)
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    FACTORY_LATEST.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["artifact"] = str(FACTORY_LATEST.relative_to(REPO_ROOT)).replace("\\", "/")
    return report


def propose_clone(
    *,
    subsystem: str | None = None,
    hypothesis: str = "",
    index: int = 0,
    dry_run: bool = True,
    candidate_id: str | None = None,
    parent: str = "PRODUCTION",
) -> dict[str, Any]:
    """Goal-driven candidate from recommend list (RG-FAC-02)."""
    rec = write_recommend()
    cloneable = rec.get("cloneable") or []
    if subsystem:
        pick = next((s for s in cloneable if s["subsystem"] == subsystem), None)
        if pick is None:
            # allow explicit subsystem with default recipe even if not in mismatches
            if subsystem not in list_subsystems():
                raise ValueError(f"unknown subsystem {subsystem}")
            recipe = (DEFAULT_RECIPES.get(subsystem) or [None])[0]
            if not recipe:
                raise ValueError(f"no default recipe for {subsystem}")
            pick = {
                "subsystem": subsystem,
                "recipe": recipe,
                "set_args": [f"{k}={v}" for k, v in recipe.items()],
                "hypothesis": hypothesis
                or f"Manual factory propose for {subsystem}: {recipe}",
            }
    else:
        if not cloneable:
            return {
                "ok": False,
                "dry_run": dry_run,
                "reason": "no cloneable suggestions (edge compatible or no axis)",
                "recommend": rec,
            }
        if index < 0 or index >= len(cloneable):
            raise IndexError(f"index {index} out of range 0..{len(cloneable)-1}")
        pick = cloneable[index]

    hyp = hypothesis or pick.get("hypothesis") or ""
    overrides = dict(pick.get("recipe") or {})
    payload = {
        "ok": True,
        "dry_run": dry_run,
        "subsystem": pick["subsystem"],
        "overrides": overrides,
        "set_args": pick.get("set_args"),
        "hypothesis": hyp,
        "parent": parent,
        "candidate_id": candidate_id,
    }
    if dry_run:
        payload["note"] = "dry_run — pass dry_run=False to write Presets/*.set"
        return payload

    cloned = clone_preset(
        candidate_id=candidate_id,
        subsystem=str(pick["subsystem"]),
        overrides=overrides,
        parent_id=parent,
        notes=hyp,
        status="queued",
    )
    payload["cloned"] = cloned
    return payload
