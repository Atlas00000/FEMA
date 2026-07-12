"""Certificate-driven rolling health (ESR-W03 / EL5 shadow)."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_AI_DIR = Path(__file__).resolve().parent.parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from cert_loader import ladder_label, load_certificate  # noqa: E402
from csv_util import read_csv_rows  # noqa: E402
from paths import CERTIFICATE_JSON, LATEST_BASKETS, LATEST_EVENTS, LIVE_DIR  # noqa: E402

from . import HEALTH_FORMULA
from .pause import would_pause_new
from .persistence import PersistenceState, update_persistence
from .scoring import (
    score_depth,
    score_duration,
    score_mae_efficiency,
    score_pf,
    score_regime,
    score_spread,
    score_tp_hit,
    score_trade_frequency,
)


HEALTH_STATE_PATH = LIVE_DIR / "health_state.json"
HEALTH_LATEST_JSON = LIVE_DIR / "health_latest.json"
HEALTH_LATEST_MD = LIVE_DIR / "health_latest.md"


def _f(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def _parse_time(s: str) -> datetime:
    return datetime.strptime(s.strip(), "%Y.%m.%d %H:%M:%S")


def load_baskets(path: Path) -> list[dict]:
    rows = read_csv_rows(path)
    if not rows:
        return []
    if "profit" not in rows[0]:
        raise ValueError(f"{path} missing profit column (need basket outcome CSV)")
    rows.sort(key=lambda r: _parse_time(r["open_time"]))
    return rows


def window_metrics(rows: list[dict], birth: dict, fingerprint: dict) -> dict[str, Any]:
    n = len(rows)
    empty = {
        "n": 0,
        "pf": 0.0,
        "wr": 0.0,
        "tp_hit_rate": 0.0,
        "avg_bars_alive": 0.0,
        "avg_depth": 0.0,
        "avg_mae_abs": 0.0,
        "avg_mfe": 0.0,
        "mae_vs_bsl": 0.0,
        "baskets_per_day": 0.0,
        "adx_ok_share": None,
    }
    if n == 0:
        return empty

    profits = [_f(r, "profit") for r in rows]
    wins = [p for p in profits if p > 0]
    losses = [-p for p in profits if p < 0]
    gw, gl = sum(wins), sum(losses)
    pf = (gw / gl) if gl > 0 else (99.0 if gw > 0 else 0.0)
    tp = sum(1 for r in rows if int(_f(r, "hit_tp")) == 1) / n
    wr = len(wins) / n
    bars = [_f(r, "bars_alive") for r in rows]
    depths = [_f(r, "max_depth") for r in rows]
    mae_abs = [abs(_f(r, "mae")) for r in rows]
    mfe = [_f(r, "mfe") for r in rows]
    bsl = float(birth.get("bsl") or fingerprint.get("bsl") or 25.0)

    t0 = _parse_time(rows[0]["open_time"])
    t1 = _parse_time(rows[-1]["open_time"])
    days = max((t1 - t0).total_seconds() / 86400.0, 1.0 / 24.0)
    bpd = n / days

    adx_max = float(fingerprint.get("adx_max") or 30.0)
    adx_vals = [r.get("adx") for r in rows if r.get("adx") not in (None, "")]
    adx_ok = None
    if adx_vals:
        ok = sum(1 for a in adx_vals if _f({"adx": a}, "adx") < adx_max)
        adx_ok = ok / len(adx_vals)

    return {
        "n": n,
        "pf": round(pf, 4),
        "wr": round(wr, 4),
        "tp_hit_rate": round(tp, 4),
        "avg_bars_alive": round(sum(bars) / n, 2),
        "avg_depth": round(sum(depths) / n, 3),
        "avg_mae_abs": round(sum(mae_abs) / n, 3),
        "avg_mfe": round(sum(mfe) / n, 3),
        "mae_vs_bsl": round((sum(mae_abs) / n) / bsl, 4) if bsl else 0.0,
        "baskets_per_day": round(bpd, 4),
        "adx_ok_share": None if adx_ok is None else round(adx_ok, 4),
        "open_first": rows[0]["open_time"],
        "open_last": rows[-1]["open_time"],
        "days": round(days, 2),
    }


def event_reject_rate(events_path: Path | None) -> float | None:
    if events_path is None or not events_path.is_file():
        return None
    rows = read_csv_rows(events_path)
    if not rows:
        return None
    # count order fails / rejects among candidate+fail-like events
    interesting = 0
    rejects = 0
    for r in rows:
        et = str(r.get("event") or r.get("event_type") or "").upper()
        if et in ("ORDER_FAIL", "SKIP"):
            interesting += 1
            rc = str(r.get("reject_class") or "").lower()
            reason = str(r.get("reason") or "").lower()
            if rc in ("reject", "no_money", "other") or "order_fail" in reason or et == "ORDER_FAIL":
                if rc != "transient":
                    rejects += 1
        elif et in ("CANDIDATE", "FILL", "ADD", "BASKET_OPEN"):
            interesting += 1
    if interesting == 0:
        return None
    return rejects / interesting


def component_scores(metrics: dict, cert: dict, reject_rate: float | None) -> dict[str, float]:
    bands = cert["bands"]
    birth = cert["birth_metrics"]
    bsl = float(birth.get("bsl") or cert["fingerprint"].get("bsl") or 25.0)
    birth_bars = float(birth.get("avg_bars_alive") or 0)
    birth_depth = float(birth.get("avg_depth") or 0)
    birth_bpd = float(birth.get("baskets_per_day") or 0)

    return {
        "profit_factor": round(score_pf(metrics["pf"], bands), 2),
        "tp_hit_rate": round(score_tp_hit(metrics["tp_hit_rate"], bands), 2),
        "basket_duration": round(
            score_duration(metrics["avg_bars_alive"], birth_bars, bands), 2
        ),
        "basket_depth": round(score_depth(metrics["avg_depth"], birth_depth, bands), 2),
        "mae_mfe_efficiency": round(
            score_mae_efficiency(
                metrics["avg_mae_abs"], metrics["avg_mfe"], bsl, bands
            ),
            2,
        ),
        "trade_frequency": round(
            score_trade_frequency(metrics["baskets_per_day"], birth_bpd, bands), 2
        ),
        "spread_execution": round(score_spread(reject_rate, bands), 2),
        "regime_match": round(score_regime(metrics.get("adx_ok_share"), bands), 2),
    }


def weighted_health(components: dict[str, float], weights: dict[str, float]) -> float:
    total_w = 0.0
    acc = 0.0
    for k, w in weights.items():
        if k not in components:
            continue
        wf = float(w)
        acc += wf * float(components[k])
        total_w += wf
    if total_w <= 0:
        return 50.0
    return round(acc / total_w, 2)


def score_window(
    rows: list[dict],
    window: int,
    cert: dict,
    reject_rate: float | None,
) -> dict[str, Any]:
    slice_rows = rows[-window:] if len(rows) >= window else rows
    metrics = window_metrics(slice_rows, cert["birth_metrics"], cert["fingerprint"])
    comps = component_scores(metrics, cert, reject_rate)
    health = weighted_health(comps, cert["health_weights"])
    ladder = ladder_label(health, cert)
    return {
        "window": window,
        "sufficient": len(rows) >= window,
        "metrics": metrics,
        "components": comps,
        "health": health,
        "ladder": ladder,
    }


def drift_tags_v0(primary: dict[str, Any], cert: dict) -> list[str]:
    """Rules-only Market / Execution / Performance tags."""
    tags: list[str] = []
    m = primary["metrics"]
    c = primary["components"]
    birth = cert["birth_metrics"]
    if c["profit_factor"] < 55 or c["tp_hit_rate"] < 55:
        tags.append("Performance")
    if c["basket_depth"] < 55 or c["basket_duration"] < 55:
        tags.append("Market")
    if c["spread_execution"] < 55:
        tags.append("Execution")
    if m.get("adx_ok_share") is not None and c["regime_match"] < 55:
        tags.append("Market")
    # de-dupe preserve order
    seen = set()
    out = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    if not out and primary["health"] < 70:
        out.append("Performance")
    _ = birth  # reserved for future birth-delta tags
    return out


def run_health(
    baskets_path: Path | None = None,
    events_path: Path | None = None,
    cert_path: Path | None = None,
    state_path: Path | None = None,
    out_json: Path | None = None,
    out_md: Path | None = None,
    update_state: bool = True,
) -> dict[str, Any]:
    baskets_path = baskets_path or LATEST_BASKETS
    events_path = events_path if events_path is not None else LATEST_EVENTS
    cert = load_certificate(cert_path or CERTIFICATE_JSON)
    rows = load_baskets(baskets_path)
    if not rows:
        raise SystemExit(f"no baskets in {baskets_path}")

    reject_rate = event_reject_rate(events_path if Path(events_path).is_file() else None)
    windows = [int(w) for w in cert["rolling_windows_baskets"]]
    primary_n = int(cert.get("primary_window_baskets") or 100)

    window_reports = {
        str(w): score_window(rows, w, cert, reject_rate) for w in windows
    }
    primary = window_reports[str(primary_n)]
    health = float(primary["health"])
    ladder = primary["ladder"]

    state_file = state_path or HEALTH_STATE_PATH
    state = PersistenceState.from_dict(
        json.loads(state_file.read_text(encoding="utf-8"))
        if state_file.is_file()
        else None
    )
    formula = str(cert.get("health_formula_version") or HEALTH_FORMULA).strip() or HEALTH_FORMULA
    state.formula_version = formula
    pers = cert.get("persistence") or {}
    flags = update_persistence(
        state,
        health,
        str(ladder["label"]),
        deteriorate_need=int(pers.get("deteriorate_windows") or 3),
        recover_need=int(pers.get("recover_windows") or 2),
    )

    if update_state:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")

    tags = drift_tags_v0(primary, cert)
    pause_shadow = would_pause_new(health, str(ladder["label"]), flags)
    report = {
        "phase": "INF-OPS",
        "formula_version": formula,
        "preset": cert.get("preset"),
        "source_baskets": str(baskets_path).replace("\\", "/"),
        "source_events": str(events_path).replace("\\", "/") if events_path else None,
        "n_baskets_total": len(rows),
        "primary_window": primary_n,
        "health": health,
        "ladder": ladder,
        "persistence": flags,
        "drift_tags": tags,
        "would_pause_new": pause_shadow["would_pause_new"],
        "pause": pause_shadow,
        "reject_rate": reject_rate,
        "windows": window_reports,
        "shadow": True,
        "note": "Shadow only — do not wire pause until EL6 opt-in (InpReadPauseNewFlag).",
    }
    if not report.get("formula_version"):
        raise ValueError("health snapshot missing formula_version (RG-VER-02)")

    # Wave 3: attach fingerprint × genome compatibility (shadow)
    try:
        from fema_ops.fingerprint import write_fingerprint

        fp_out = write_fingerprint(
            baskets=baskets_path,
            window=primary_n,
            run_id=None,
            attach_run=True,
        )
        report["fingerprint"] = {
            "schema": (fp_out.get("fingerprint") or {}).get("schema"),
            "window": (fp_out.get("fingerprint") or {}).get("window"),
            "regime": (fp_out.get("fingerprint") or {}).get("regime"),
            "pullback": (fp_out.get("fingerprint") or {}).get("pullback"),
            "session": (fp_out.get("fingerprint") or {}).get("session"),
            "artifact": (fp_out.get("artifacts") or {}).get("latest"),
        }
        report["compatibility"] = fp_out.get("compatibility")
    except Exception as exc:  # noqa: BLE001
        report["fingerprint"] = {"error": str(exc)}
        report["compatibility"] = {"signal": "error", "note": str(exc), "shadow": True}

    out_j = out_json or HEALTH_LATEST_JSON
    out_m = out_md or HEALTH_LATEST_MD
    out_j.parent.mkdir(parents=True, exist_ok=True)
    out_j.write_text(json.dumps(report, indent=2), encoding="utf-8")
    out_m.write_text(render_md(report), encoding="utf-8")
    report["artifacts"] = {
        "json": str(out_j).replace("\\", "/"),
        "md": str(out_m).replace("\\", "/"),
        "state": str(state_file).replace("\\", "/"),
    }
    return report


def render_md(report: dict[str, Any]) -> str:
    ladder = report["ladder"]
    pers = report["persistence"]
    lines = [
        "# Edge health (health_v0)",
        "",
        f"**Health:** {report['health']:.1f} / 100",
        f"**Ladder:** `{ladder['label']}` — {ladder['action']}",
        f"**Primary window:** last {report['primary_window']} baskets",
        f"**Formula:** `{report['formula_version']}`",
        f"**Shadow:** yes",
        f"**Would pause new:** `{report.get('would_pause_new')}` "
        f"({(report.get('pause') or {}).get('reason', '-')})",
        "",
        "## Persistence",
        "",
        f"- Warning active: **{pers['warning_active']}**",
        f"- Consecutive deteriorate: {pers['consecutive_deteriorate']}",
        f"- Consecutive recover: {pers['consecutive_recover']}",
        "",
        "## Drift tags",
        "",
        (", ".join(report["drift_tags"]) if report["drift_tags"] else "none"),
        "",
        "## Windows",
        "",
        "| Window | Health | Label | PF | WR | TP | Depth | Bars |",
        "| ------ | ------ | ----- | -- | -- | -- | ----- | ---- |",
    ]
    for w, block in sorted(report["windows"].items(), key=lambda x: int(x[0])):
        m = block["metrics"]
        lab = block["ladder"]["label"]
        lines.append(
            f"| {w} | {block['health']:.1f} | {lab} | {m['pf']:.2f} | "
            f"{m['wr']:.0%} | {m['tp_hit_rate']:.0%} | {m['avg_depth']:.2f} | "
            f"{m['avg_bars_alive']:.0f} |"
        )
    primary = report["windows"][str(report["primary_window"])]
    lines.extend(
        [
            "",
            "## Components (primary)",
            "",
            "| Component | Score |",
            "| --------- | ----- |",
        ]
    )
    for k, v in primary["components"].items():
        lines.append(f"| {k} | {v:.1f} |")
    compat = report.get("compatibility") or {}
    if compat:
        lines.extend(
            [
                "",
                "## Compatibility (shadow)",
                "",
                f"- Signal: **`{compat.get('signal')}`** · score `{compat.get('score')}`",
                f"- Suggest subsystems: "
                f"{', '.join(compat.get('suggest_subsystems') or []) or 'none'}",
                f"- Note: {compat.get('note') or 'shadow only'}",
                "",
            ]
        )
    lines.extend(["", f"Source: `{report['source_baskets']}`", ""])
    return "\n".join(lines)


def ascii_summary(report: dict[str, Any]) -> str:
    """cp1252-safe one-liner for Windows consoles."""
    lab = report["ladder"]["label"]
    pers = report["persistence"]
    tags = ",".join(report["drift_tags"]) if report["drift_tags"] else "-"
    pause = int(bool(report.get("would_pause_new")))
    sig = (report.get("compatibility") or {}).get("signal") or "-"
    return (
        f"health_v0={report['health']:.1f} ladder={lab} "
        f"warn={int(pers['warning_active'])} "
        f"would_pause={pause} "
        f"det={pers['consecutive_deteriorate']} rec={pers['consecutive_recover']} "
        f"compat={sig} "
        f"tags={tags} n={report['n_baskets_total']}"
    )
