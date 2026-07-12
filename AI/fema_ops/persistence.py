"""Persistence flags for health ladder (3 deteriorate / 2 recover)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class PersistenceState:
    formula_version: str = "health_v0"
    history: list[dict[str, Any]] = field(default_factory=list)
    warning_active: bool = False
    consecutive_deteriorate: int = 0
    consecutive_recover: int = 0
    last_health: float | None = None
    last_label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> PersistenceState:
        if not raw:
            return cls()
        return cls(
            formula_version=str(raw.get("formula_version") or "health_v0"),
            history=list(raw.get("history") or []),
            warning_active=bool(raw.get("warning_active")),
            consecutive_deteriorate=int(raw.get("consecutive_deteriorate") or 0),
            consecutive_recover=int(raw.get("consecutive_recover") or 0),
            last_health=(
                float(raw["last_health"]) if raw.get("last_health") is not None else None
            ),
            last_label=raw.get("last_label"),
        )


# Ladder severity (higher = worse)
_LABEL_RANK = {
    "normal": 0,
    "investigate": 1,
    "watch": 2,
    "re_discovery": 3,
    "retire": 4,
}


def label_rank(label: str) -> int:
    return _LABEL_RANK.get(label, 2)


def update_persistence(
    state: PersistenceState,
    health: float,
    label: str,
    *,
    deteriorate_need: int = 3,
    recover_need: int = 2,
    max_history: int = 60,
) -> dict[str, Any]:
    """Append one update; return flags for this snapshot.

    Deteriorating = health fell vs prior update OR ladder rank worsened.
    Warning latches after `deteriorate_need` consecutive deteriorations;
    clears after `recover_need` consecutive recoveries (health up and rank not worse).
    """
    deteriorated = False
    recovered = False

    if state.last_health is not None:
        prev_rank = label_rank(state.last_label or "normal")
        cur_rank = label_rank(label)
        if health < state.last_health - 1e-9 or cur_rank > prev_rank:
            deteriorated = True
        elif health > state.last_health + 1e-9 and cur_rank <= prev_rank:
            recovered = True
        # flat day: neither (ignore_single_bad_day handled by requiring streaks)

    if deteriorated:
        state.consecutive_deteriorate += 1
        state.consecutive_recover = 0
    elif recovered:
        state.consecutive_recover += 1
        state.consecutive_deteriorate = 0
    else:
        # flat — do not extend either streak (single-day noise)
        pass

    trigger_warning = state.consecutive_deteriorate >= deteriorate_need
    if trigger_warning:
        state.warning_active = True

    clear_warning = False
    if state.warning_active and state.consecutive_recover >= recover_need:
        state.warning_active = False
        clear_warning = True
        state.consecutive_recover = 0

    entry = {
        "ts": _utc_now(),
        "health": round(health, 2),
        "label": label,
        "formula_version": state.formula_version,
        "deteriorated": deteriorated,
        "recovered": recovered,
        "warning_active": state.warning_active,
        "consecutive_deteriorate": state.consecutive_deteriorate,
        "consecutive_recover": state.consecutive_recover,
    }
    state.history.append(entry)
    if len(state.history) > max_history:
        state.history = state.history[-max_history:]

    state.last_health = health
    state.last_label = label

    return {
        "deteriorated": deteriorated,
        "recovered": recovered,
        "consecutive_deteriorate": state.consecutive_deteriorate,
        "consecutive_recover": state.consecutive_recover,
        "warning_active": state.warning_active,
        "trigger_warning": trigger_warning and not clear_warning,
        "clear_warning": clear_warning,
        "persistence_met": state.warning_active,
    }
