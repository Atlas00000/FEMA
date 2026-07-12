"""Market Fingerprint v0 — offline from basket CSVs (RG-FP-01/02)."""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_AI_DIR = Path(__file__).resolve().parent.parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from csv_util import read_csv_rows  # noqa: E402
from paths import (  # noqa: E402
    COMPAT_LATEST,
    FINGERPRINT_LATEST,
    GENOME_JSON,
    KB_RUNS_DIR,
    LATEST_BASKETS,
    LINEAGE_JSON,
    LIVE_DIR,
    REPO_ROOT,
)

SCHEMA = "fema_market_fingerprint_v0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _f(row: dict, key: str, default: float | None = None) -> float | None:
    v = row.get(key)
    if v is None or v == "":
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _pct(vals: list[float], p: float) -> float | None:
    if not vals:
        return None
    s = sorted(vals)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] + (s[c] - s[f]) * (k - f)


def _mean(vals: list[float]) -> float | None:
    return None if not vals else sum(vals) / len(vals)


def _parse_time(s: str) -> datetime | None:
    try:
        return datetime.strptime(s.strip(), "%Y.%m.%d %H:%M:%S")
    except (ValueError, AttributeError):
        return None


def _session_bucket(hour: float | None) -> str | None:
    if hour is None:
        return None
    h = int(hour) % 24
    # Broker server hours — approximate Asia / London / NY shares for fingerprint
    if 0 <= h < 7:
        return "asia"
    if 7 <= h < 13:
        return "london"
    if 13 <= h < 22:
        return "ny"
    return "asia"


def compute_fingerprint(
    rows: list[dict[str, Any]],
    *,
    window: int | None = 100,
    run_id: str | None = None,
    source_baskets: str | None = None,
) -> dict[str, Any]:
    notes: list[str] = []
    if not rows:
        notes.append("no baskets")
        return {
            "schema": SCHEMA,
            "computed_at": _utc_now(),
            "run_id": run_id,
            "source_baskets": source_baskets,
            "window": {"n_baskets": 0, "requested": window},
            "volatility": {},
            "trend_persistence": {},
            "liquidity": {},
            "session": {},
            "pullback": {},
            "ema_geometry": {},
            "regime": {},
            "notes": notes,
        }

    use = rows[-window:] if window and window > 0 else rows
    atrs = [v for v in (_f(r, "atr") for r in use) if v is not None]
    maes = [abs(v) for v in (_f(r, "mae") for r in use) if v is not None]
    spreads = [v for v in (_f(r, "spread_points") for r in use) if v is not None]
    depths = [v for v in (_f(r, "max_depth") for r in use) if v is not None]
    levels = [v for v in (_f(r, "open_level") for r in use) if v is not None]
    dists = [abs(v) for v in (_f(r, "dist_ema_trend_atr") for r in use) if v is not None]
    slopes = [v for v in (_f(r, "ema_slope") for r in use) if v is not None]
    seps = [v for v in (_f(r, "ema_sep_atr") for r in use) if v is not None]
    adxs = [v for v in (_f(r, "adx") for r in use) if v is not None]
    hours = [v for v in (_f(r, "hour") for r in use) if v is not None]
    dows = [int(v) for v in (_f(r, "dow") for r in use) if v is not None]

    buys = sum(1 for r in use if str(r.get("direction", "")).upper() == "BUY")
    n = len(use)

    sess = {"asia": 0, "london": 0, "ny": 0}
    for h in hours:
        b = _session_bucket(h)
        if b:
            sess[b] += 1
    hs = sum(sess.values()) or 1

    hour_counts: dict[int, int] = {}
    for h in hours:
        hi = int(h) % 24
        hour_counts[hi] = hour_counts.get(hi, 0) + 1
    hour_top = sorted(
        ({"hour": h, "share": round(c / max(len(hours), 1), 4)} for h, c in hour_counts.items()),
        key=lambda x: -x["share"],
    )[:3]

    dow_hist = {
        str(d): round(dows.count(d) / max(len(dows), 1), 4) for d in sorted(set(dows))
    }

    t0 = _parse_time(str(use[0].get("open_time") or ""))
    t1 = _parse_time(str(use[-1].get("open_time") or ""))
    days = None
    if t0 and t1 and t1 >= t0:
        days = round((t1 - t0).total_seconds() / 86400.0, 2)

    return {
        "schema": SCHEMA,
        "computed_at": _utc_now(),
        "run_id": run_id,
        "source_baskets": source_baskets,
        "window": {
            "n_baskets": n,
            "requested": window,
            "open_first": use[0].get("open_time"),
            "open_last": use[-1].get("open_time"),
            "days": days,
        },
        "volatility": {
            "atr_mean": None if _mean(atrs) is None else round(_mean(atrs), 6),  # type: ignore[arg-type]
            "atr_p50": None if _pct(atrs, 50) is None else round(_pct(atrs, 50), 6),  # type: ignore[arg-type]
            "atr_p90": None if _pct(atrs, 90) is None else round(_pct(atrs, 90), 6),  # type: ignore[arg-type]
            "mae_abs_mean": None if _mean(maes) is None else round(_mean(maes), 3),  # type: ignore[arg-type]
            "mae_abs_p90": None if _pct(maes, 90) is None else round(_pct(maes, 90), 3),  # type: ignore[arg-type]
        },
        "trend_persistence": {
            "buy_share": round(buys / n, 4),
            "ema_slope_abs_mean": None
            if not slopes
            else round(sum(abs(x) for x in slopes) / len(slopes), 8),
            "ema_sep_atr_abs_mean": None
            if not seps
            else round(sum(abs(x) for x in seps) / len(seps), 4),
        },
        "liquidity": {
            "spread_mean": None if _mean(spreads) is None else round(_mean(spreads), 2),  # type: ignore[arg-type]
            "spread_p90": None if _pct(spreads, 90) is None else round(_pct(spreads, 90), 2),  # type: ignore[arg-type]
        },
        "session": {
            "asia_share": round(sess["asia"] / hs, 4),
            "london_share": round(sess["london"] / hs, 4),
            "ny_share": round(sess["ny"] / hs, 4),
            "hour_top3": hour_top,
            "dow_hist": dow_hist,
        },
        "pullback": {
            "avg_depth": None if _mean(depths) is None else round(_mean(depths), 3),  # type: ignore[arg-type]
            "depth_p90": None if _pct(depths, 90) is None else round(_pct(depths, 90), 3),  # type: ignore[arg-type]
            "avg_open_level": None if _mean(levels) is None else round(_mean(levels), 3),  # type: ignore[arg-type]
            "dist_ema_trend_atr_abs_mean": None
            if _mean(dists) is None
            else round(_mean(dists), 4),  # type: ignore[arg-type]
        },
        "ema_geometry": {
            "ema_sep_atr_p50": None if _pct(seps, 50) is None else round(_pct(seps, 50), 4),  # type: ignore[arg-type]
            "ema_sep_atr_p90_abs": None
            if not seps
            else round(_pct([abs(x) for x in seps], 90) or 0.0, 4),
            "slope_pos_share": None
            if not slopes
            else round(sum(1 for x in slopes if x > 0) / len(slopes), 4),
        },
        "regime": {
            "adx_mean": None if _mean(adxs) is None else round(_mean(adxs), 2),  # type: ignore[arg-type]
            "adx_p50": None if _pct(adxs, 50) is None else round(_pct(adxs, 50), 2),  # type: ignore[arg-type]
            "adx_p90": None if _pct(adxs, 90) is None else round(_pct(adxs, 90), 2),  # type: ignore[arg-type]
            "adx_lt_30_share": None
            if not adxs
            else round(sum(1 for a in adxs if a < 30) / len(adxs), 4),
        },
        "notes": notes,
    }


def _nested_get(fp: dict[str, Any], dotted: str) -> float | None:
    cur: Any = fp
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    if cur is None:
        return None
    try:
        return float(cur)
    except (TypeError, ValueError):
        return None


def score_compatibility(
    fingerprint: dict[str, Any],
    genome: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fingerprint × genome → shadow signal (RG-GEN-02). Does not change health score."""
    if genome is None:
        if GENOME_JSON.is_file():
            genome = json.loads(GENOME_JSON.read_text(encoding="utf-8"))
        else:
            genome = {}

    thrive = genome.get("thrive") or {}
    fail = genome.get("fail") or {}
    hints = genome.get("subsystem_hints") or {}

    checks: list[dict[str, Any]] = []
    score_parts: list[float] = []
    mismatches: list[dict[str, Any]] = []

    def add_check(
        key: str,
        value: float | None,
        *,
        thr_min: float | None = None,
        thr_max: float | None = None,
        fail_min: float | None = None,
        fail_max: float | None = None,
        subsystem: str | None = None,
        note: str = "",
    ) -> None:
        if value is None:
            checks.append({"key": key, "ok": None, "value": None, "note": "missing"})
            return
        in_fail = False
        if fail_min is not None and value >= fail_min:
            in_fail = True
        if fail_max is not None and value <= fail_max:
            in_fail = True
        in_thrive = True
        if thr_min is not None and value < thr_min:
            in_thrive = False
        if thr_max is not None and value > thr_max:
            in_thrive = False

        if in_fail:
            pts = 20.0
            ok = False
        elif in_thrive:
            pts = 100.0
            ok = True
        else:
            pts = 55.0
            ok = False
        score_parts.append(pts)
        row = {
            "key": key,
            "ok": ok,
            "value": value,
            "points": pts,
            "note": note,
            "subsystem": subsystem,
        }
        checks.append(row)
        if not ok:
            mismatches.append(row)

    t = thrive
    f = fail

    def band(d: dict, key: str) -> dict:
        return d.get(key) or {}

    add_check(
        "regime.adx_lt_30_share",
        _nested_get(fingerprint, "regime.adx_lt_30_share"),
        thr_min=band(t, "regime.adx_lt_30_share").get("min"),
        fail_max=band(f, "regime.adx_lt_30_share").get("max"),
        subsystem=hints.get("regime_adx", "adx"),
        note=band(t, "regime.adx_lt_30_share").get("note") or "",
    )
    add_check(
        "regime.adx_p50",
        _nested_get(fingerprint, "regime.adx_p50"),
        thr_max=band(t, "regime.adx_p50").get("max"),
        subsystem=hints.get("regime_adx", "adx"),
    )
    add_check(
        "pullback.avg_depth",
        _nested_get(fingerprint, "pullback.avg_depth"),
        thr_min=band(t, "pullback.avg_depth").get("min"),
        thr_max=band(t, "pullback.avg_depth").get("max"),
        fail_min=band(f, "pullback.avg_depth").get("min"),
        subsystem=hints.get("deep_pullback", "grid"),
    )
    add_check(
        "volatility.mae_abs_mean",
        _nested_get(fingerprint, "volatility.mae_abs_mean"),
        thr_max=band(t, "volatility.mae_abs_mean").get("max"),
        fail_min=band(f, "volatility.mae_abs_mean").get("min"),
        subsystem=hints.get("deep_pullback", "grid"),
    )
    add_check(
        "session.asia_share",
        _nested_get(fingerprint, "session.asia_share"),
        thr_min=band(t, "session.asia_share").get("min"),
        subsystem=hints.get("session_skew", "session"),
    )
    add_check(
        "liquidity.spread_p90",
        _nested_get(fingerprint, "liquidity.spread_p90"),
        thr_max=band(t, "liquidity.spread_p90").get("max"),
        subsystem=hints.get("spread_exec", "execution"),
    )

    # London+NY only proxy
    lon = _nested_get(fingerprint, "session.london_share") or 0.0
    ny = _nested_get(fingerprint, "session.ny_share") or 0.0
    ln_proxy = lon + ny
    add_check(
        "session.london_ny_only_proxy",
        ln_proxy,
        fail_min=(band(f, "session.london_ny_only_proxy").get("min") or 0.9),
        subsystem=hints.get("session_skew", "session"),
        note="fail if London+NY dominate",
    )
    # Invert: for this check, "fail_min" means bad when high — already handled.
    # But thrive has no max on proxy; if asia ok, proxy usually fine. Re-score last if asia ok:
    if checks and checks[-1]["key"] == "session.london_ny_only_proxy":
        asia = _nested_get(fingerprint, "session.asia_share")
        if asia is not None and asia >= 0.15 and ln_proxy < 0.9:
            checks[-1]["ok"] = True
            checks[-1]["points"] = 100.0
            if checks[-1] in mismatches:
                mismatches.remove(checks[-1])
            if score_parts:
                score_parts[-1] = 100.0

    overall = round(sum(score_parts) / len(score_parts), 2) if score_parts else None
    if overall is None:
        signal = "insufficient"
    elif overall >= 80:
        signal = "compatible"
    elif overall >= 55:
        signal = "watch"
    else:
        signal = "investigate"

    subsystems: list[str] = []
    for m in mismatches:
        sub = m.get("subsystem")
        if sub and sub not in subsystems:
            subsystems.append(sub)
    subsystems = subsystems[:3]

    return {
        "schema": "fema_compatibility_v0",
        "computed_at": _utc_now(),
        "genome": genome.get("preset") or "PRODUCTION",
        "score": overall,
        "signal": signal,
        "shadow": True,
        "checks": checks,
        "mismatches": mismatches,
        "suggest_subsystems": subsystems,
        "note": "Shadow only — does not change health ladder or pause.",
    }


def write_fingerprint(
    *,
    baskets: Path | None = None,
    window: int = 100,
    run_id: str | None = None,
    attach_run: bool = True,
) -> dict[str, Any]:
    path = baskets or LATEST_BASKETS
    rows = read_csv_rows(path) if path.is_file() else []
    if run_id is None and LINEAGE_JSON.is_file():
        try:
            lin = json.loads(LINEAGE_JSON.read_text(encoding="utf-8"))
            run_id = (lin.get("active_lock") or {}).get("run_id")
        except (OSError, json.JSONDecodeError):
            run_id = None

    fp = compute_fingerprint(
        rows,
        window=window,
        run_id=run_id,
        source_baskets=str(path).replace("\\", "/"),
    )
    compat = score_compatibility(fp)

    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    FINGERPRINT_LATEST.write_text(json.dumps(fp, indent=2) + "\n", encoding="utf-8")
    COMPAT_LATEST.write_text(json.dumps(compat, indent=2) + "\n", encoding="utf-8")

    attached = None
    if attach_run and run_id:
        folder = KB_RUNS_DIR / run_id
        folder.mkdir(parents=True, exist_ok=True)
        out = folder / "fingerprint.json"
        payload = {**fp, "compatibility": compat}
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        metrics_path = folder / "metrics.json"
        if metrics_path.is_file():
            try:
                rec = json.loads(metrics_path.read_text(encoding="utf-8"))
                rec["fingerprint_path"] = str(out.relative_to(REPO_ROOT)).replace("\\", "/")
                rec["compatibility_signal"] = compat.get("signal")
                metrics_path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
            except (OSError, json.JSONDecodeError):
                pass
        attached = str(out.relative_to(REPO_ROOT)).replace("\\", "/")

    return {
        "fingerprint": fp,
        "compatibility": compat,
        "artifacts": {
            "latest": str(FINGERPRINT_LATEST.relative_to(REPO_ROOT)).replace("\\", "/"),
            "compat": str(COMPAT_LATEST.relative_to(REPO_ROOT)).replace("\\", "/"),
            "run": attached,
        },
    }
