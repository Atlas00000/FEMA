"""ASI-P8 — regime intelligence (offline taxonomy + scorecard + permissive policy).

Rule-based labels at basket-open (no outcome leakage). Historical PF/DD per regime
drives allow / caution / skip recommendations. Default = shadow only.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from csv_util import read_csv_rows
from fema_ops.asi.dataset import (
    basket_run_metrics,
    merge_labeled_rows,
    resolve_splits,
)
from fema_ops.asi.features import parse_open_time
from fema_ops.asi.shadow import equity_dd_pct

# Taxonomy from failureimprove Track G (ordered match priority)
REGIME_ORDER = [
    "liquidity_vacuum",
    "impulse",
    "expansion",
    "exhaustion",
    "false_breakout",
    "compression",
    "grind",
    "pullback_trend",
    "rotation",
]

REGIME_DESC = {
    "liquidity_vacuum": "Thin hours and/or wide spread — microstructure hostile",
    "impulse": "Strong impulse / acceleration — breakout-like path risk",
    "expansion": "ATR expanding with elevated ADX — steamroller climate",
    "exhaustion": "High ADX but decelerating after long same-dir run",
    "false_breakout": "Far from EMA with weak/falling ADX — extension without trend fuel",
    "compression": "ATR contracting, quiet ADX — coiled / low energy",
    "grind": "Modest slope, mid ADX, shallow pullback — slow trend grind",
    "pullback_trend": "FEMA home: mid ADX, pullback-to-EMA geometry",
    "rotation": "Low ADX chop / residual — range rotation",
}

DATASET_FIELDS = [
    "basket_id",
    "open_time",
    "symbol",
    "direction",
    "regime",
    "adx",
    "atr",
    "atr_expansion_rate",
    "impulse_score",
    "dist_ema_abs",
    "spread_points",
    "hour",
    "adx_accel",
    "consecutive_same_dir",
    "ema_slope",
    "profit",
    "hit_bsl",
    "hit_tp",
    "mae",
    "max_depth",
    "label_class",
    "y_steamroller",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _f(row: dict, key: str, default: float = 0.0) -> float:
    try:
        v = float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default
    if key == "roll_pf" and v > 5.0:
        return 5.0
    return v


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    values = sorted(values)
    k = (len(values) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(values) - 1)
    frac = k - lo
    return values[lo] * (1 - frac) + values[hi] * frac


def calibrate_thresholds(rows: list[dict]) -> dict[str, float]:
    """Percentile thresholds from train opens (reproducible, no outcome use)."""
    def col(key: str) -> list[float]:
        return [_f(r, key) for r in rows]

    abs_slope = [abs(_f(r, "ema_slope")) for r in rows]
    return {
        "impulse_score_hi": round(_percentile(col("impulse_score"), 0.85), 4),
        "atr_expand_hi": round(_percentile(col("atr_expansion_rate"), 0.75), 4),
        "atr_expand_lo": round(_percentile(col("atr_expansion_rate"), 0.25), 4),
        "adx_hi": round(_percentile(col("adx"), 0.75), 4),
        "adx_mid": round(_percentile(col("adx"), 0.50), 4),
        "adx_lo": round(_percentile(col("adx"), 0.35), 4),
        "adx_accel_hi": round(_percentile(col("adx_accel"), 0.70), 4),
        "adx_accel_lo": round(_percentile(col("adx_accel"), 0.30), 4),
        "dist_hi": round(_percentile(col("dist_ema_abs"), 0.75), 4),
        "dist_mid": round(_percentile(col("dist_ema_abs"), 0.45), 4),
        "dist_lo": round(_percentile(col("dist_ema_abs"), 0.35), 4),
        "spread_hi": round(_percentile(col("spread_points"), 0.90), 4),
        "slope_hi": round(_percentile(abs_slope, 0.65), 8),
        "slope_lo": round(_percentile(abs_slope, 0.35), 8),
        "consec_hi": round(_percentile(col("consecutive_same_dir"), 0.75), 2),
        "thin_hour_end": 7.0,  # UTC-ish Asian/early London thin
    }


DEFAULT_THRESHOLDS = {
    "impulse_score_hi": 22.0,
    "atr_expand_hi": 0.56,
    "atr_expand_lo": -0.37,
    "adx_hi": 27.0,
    "adx_mid": 23.7,
    "adx_lo": 21.0,
    "adx_accel_hi": 4.0,
    "adx_accel_lo": -4.0,
    "dist_hi": 4.0,
    "dist_mid": 2.0,
    "dist_lo": 1.2,
    "spread_hi": 8.0,
    "slope_hi": 3e-5,
    "slope_lo": 1.5e-5,
    "consec_hi": 4.0,
    "thin_hour_end": 7.0,
}


def classify_regime(row: dict, thr: dict[str, float] | None = None) -> str:
    """Assign one regime label from open-time features only."""
    t = thr or DEFAULT_THRESHOLDS
    adx = _f(row, "adx")
    atr_e = _f(row, "atr_expansion_rate")
    impulse = _f(row, "impulse_score")
    dist = _f(row, "dist_ema_abs") or abs(_f(row, "dist_ema_trend_atr"))
    spread = _f(row, "spread_points")
    hour = _f(row, "hour")
    adx_a = _f(row, "adx_accel")
    consec = _f(row, "consecutive_same_dir", 1.0)
    slope_abs = abs(_f(row, "ema_slope"))

    # 1) microstructure
    if hour < t["thin_hour_end"] or spread >= t["spread_hi"]:
        return "liquidity_vacuum"

    # 2) impulse / expansion / exhaustion / false break
    if impulse >= t["impulse_score_hi"] and (adx_a >= t["adx_accel_hi"] or atr_e >= t["atr_expand_hi"]):
        return "impulse"
    if atr_e >= t["atr_expand_hi"] and adx >= t["adx_mid"]:
        return "expansion"
    if adx >= t["adx_hi"] and adx_a <= t["adx_accel_lo"] and consec >= t["consec_hi"]:
        return "exhaustion"
    if dist >= t["dist_hi"] and adx <= t["adx_mid"] and adx_a <= 0:
        return "false_breakout"

    # 3) compression / grind / pullback / rotation
    if atr_e <= t["atr_expand_lo"] and adx <= t["adx_mid"]:
        return "compression"
    if (
        t["adx_lo"] <= adx <= t["adx_hi"]
        and slope_abs <= t["slope_hi"]
        and dist <= t["dist_mid"]
    ):
        return "grind"
    if (
        t["adx_lo"] <= adx <= t["adx_hi"]
        and t["dist_lo"] <= dist <= t["dist_hi"]
        and slope_abs >= t["slope_lo"]
    ):
        return "pullback_trend"
    if adx < t["adx_lo"]:
        return "rotation"
    return "pullback_trend"  # residual mid-ADX with geometry → home regime


def attach_regimes(rows: list[dict], thr: dict[str, float]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        r = dict(row)
        r["regime"] = classify_regime(r, thr)
        out.append(r)
    return out


def write_regime_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=DATASET_FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in DATASET_FIELDS})


def regime_metrics(rows: list[dict], *, deposit: float = 400.0) -> dict[str, Any]:
    m = basket_run_metrics(rows)
    if int(m.get("n") or 0) == 0:
        m.setdefault("steamroller_rate", 0.0)
        m.setdefault("win_rate", 0.0)
        m.setdefault("profit_factor", 0.0)
        m.setdefault("net", 0.0)
    profits = [_f(r, "profit") for r in rows]
    m["dd_pct"] = equity_dd_pct(profits, deposit=deposit) if rows else 0.0
    return m


def build_scorecard(
    rows: list[dict],
    *,
    deposit: float = 400.0,
    label: str = "",
) -> dict[str, Any]:
    by: dict[str, list[dict]] = {k: [] for k in REGIME_ORDER}
    for row in rows:
        reg = str(row.get("regime", "rotation") or "rotation")
        if reg not in by:
            by[reg] = []
        by[reg].append(row)

    regimes: dict[str, Any] = {}
    for name in REGIME_ORDER:
        part = by.get(name) or []
        meta = regime_metrics(part, deposit=deposit)
        meta["description"] = REGIME_DESC.get(name, "")
        regimes[name] = meta

    overall = regime_metrics(rows, deposit=deposit)
    return {
        "label": label,
        "n": len(rows),
        "overall": overall,
        "regimes": regimes,
    }


def derive_policy(
    research_scorecard: dict[str, Any],
    calibrate_scorecard: dict[str, Any] | None = None,
    lock_scorecard: dict[str, Any] | None = None,
    *,
    min_n: int = 40,
    skip_pf_max: float = 0.85,
    caution_pf_max: float = 1.0,
    steam_mult: float = 1.25,
) -> dict[str, Any]:
    """Map regimes → allow / caution / skip (permissive; lock can upgrade/downgrade)."""
    base_steam = float((research_scorecard.get("overall") or {}).get("steamroller_rate") or 0.0)
    cal_regs = (calibrate_scorecard or {}).get("regimes") or {}
    lock_regs = (lock_scorecard or {}).get("regimes") or {}
    table: dict[str, Any] = {}

    for name in REGIME_ORDER:
        r = (research_scorecard.get("regimes") or {}).get(name) or {}
        n = int(r.get("n") or 0)
        pf = float(r.get("profit_factor") or 0.0)
        steam = float(r.get("steamroller_rate") or 0.0)
        net = float(r.get("net") or 0.0)

        action = "allow"
        reason = "default allow (permissive)"

        if n < min_n and n > 0:
            action = "allow"
            reason = f"n={n} < min_n={min_n} — too few to skip"
        elif n == 0:
            action = "allow"
            reason = "no samples — allow by default"
        elif pf < skip_pf_max and steam >= base_steam * steam_mult and net < 0:
            action = "skip"
            reason = (
                f"research PF={pf} < {skip_pf_max}, steam={steam} "
                f">= {round(base_steam * steam_mult, 4)}, net={net}"
            )
            c = cal_regs.get(name) or {}
            c_n = int(c.get("n") or 0)
            c_pf = float(c.get("profit_factor") or 0.0)
            if c_n >= max(15, min_n // 3) and c_pf >= 1.0:
                action = "caution"
                reason += f" | calibrate veto PF={c_pf} → caution"
        elif pf < caution_pf_max or steam >= base_steam * steam_mult or net < 0:
            action = "caution"
            reason = f"mixed research: PF={pf}, steam={steam}, net={net}"

        # Lock / PRODUCTION slice overrides (charter: scorecard on lock data)
        lk = lock_regs.get(name) or {}
        lk_n = int(lk.get("n") or 0)
        lk_pf = float(lk.get("profit_factor") or 0.0)
        lk_net = float(lk.get("net") or 0.0)
        if lk_n >= 15:
            if lk_pf >= 1.1 and lk_net > 0 and action in ("caution", "skip"):
                action = "allow"
                reason += f" | lock upgrade PF={lk_pf} n={lk_n} → allow"
            elif lk_pf < skip_pf_max and lk_net < 0 and action == "allow":
                action = "caution"
                reason += f" | lock downgrade PF={lk_pf} n={lk_n} → caution"

        table[name] = {
            "action": action,
            "reason": reason,
            "research": {
                "n": n,
                "profit_factor": pf,
                "steamroller_rate": steam,
                "net": net,
                "dd_pct": r.get("dd_pct"),
                "win_rate": r.get("win_rate"),
            },
            "calibrate": {
                "n": int((cal_regs.get(name) or {}).get("n") or 0),
                "profit_factor": (cal_regs.get(name) or {}).get("profit_factor"),
                "steamroller_rate": (cal_regs.get(name) or {}).get("steamroller_rate"),
                "net": (cal_regs.get(name) or {}).get("net"),
            },
            "lock": {
                "n": lk_n,
                "profit_factor": lk.get("profit_factor"),
                "steamroller_rate": lk.get("steamroller_rate"),
                "net": lk.get("net"),
            },
        }

    skip_regs = [k for k, v in table.items() if v["action"] == "skip"]
    caution_regs = [k for k, v in table.items() if v["action"] == "caution"]
    allow_regs = [k for k, v in table.items() if v["action"] == "allow"]

    return {
        "schema": "fema_asi_regime_policy_v1",
        "computed_at": _utc_now(),
        "phase": "ASI-P8",
        "philosophy": "permissive — prefer missed skips; skip only toxic regimes; lock can upgrade",
        "baseline_steamroller_rate": base_steam,
        "min_n": min_n,
        "skip_pf_max": skip_pf_max,
        "caution_pf_max": caution_pf_max,
        "steam_mult": steam_mult,
        "allow": allow_regs,
        "caution": caution_regs,
        "skip": skip_regs,
        "table": table,
        "non_goals": [
            "no MQL wire in P8 MVP",
            "no hard blacklist of sessions alone",
            "no threshold tune on 2026 canon",
            "do not mash with TEP/mid in one unlogged candidate",
        ],
    }


def build_regime_pack(
    *,
    baskets_path: Path,
    out_dir: Path,
    lock_baskets_path: Path | None = None,
    split_profile: str = "long",
    deposit: float = 400.0,
) -> dict[str, Any]:
    raw = read_csv_rows(baskets_path)
    labeled = merge_labeled_rows(raw)
    splits = resolve_splits(split_profile)

    # Calibrate thresholds on train window only
    train_rows = []
    cal_rows = []
    all_for_thr = []
    for row in labeled:
        ot = str(row.get("open_time", ""))
        t = parse_open_time(ot)
        sp = splits["train"]
        lo = parse_open_time(f"{sp['start']} 00:00:00")
        hi = parse_open_time(f"{sp['end']} 23:59:59")
        if lo <= t <= hi:
            train_rows.append(row)
            all_for_thr.append(row)
        spc = splits["calibrate"]
        clo = parse_open_time(f"{spc['start']} 00:00:00")
        chi = parse_open_time(f"{spc['end']} 23:59:59")
        if clo <= t <= chi:
            cal_rows.append(row)

    thr = calibrate_thresholds(all_for_thr) if all_for_thr else dict(DEFAULT_THRESHOLDS)
    labeled = attach_regimes(labeled, thr)
    train_rows = attach_regimes(train_rows, thr)
    cal_rows = attach_regimes(cal_rows, thr)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_regime_csv(out_dir / "regime_dataset_full.csv", labeled)
    write_regime_csv(out_dir / "regime_dataset_train.csv", train_rows)
    write_regime_csv(out_dir / "regime_dataset_calibrate.csv", cal_rows)

    research = build_scorecard(labeled, deposit=deposit, label="research_full")
    train_sc = build_scorecard(train_rows, deposit=deposit, label="train")
    cal_sc = build_scorecard(cal_rows, deposit=deposit, label="calibrate")

    lock_sc = None
    lock_rows: list[dict] = []
    if lock_baskets_path and Path(lock_baskets_path).is_file():
        lock_rows = attach_regimes(merge_labeled_rows(read_csv_rows(lock_baskets_path)), thr)
        write_regime_csv(out_dir / "regime_dataset_lock.csv", lock_rows)
        lock_sc = build_scorecard(lock_rows, deposit=deposit, label="lock_production")

    policy = derive_policy(research, cal_sc, lock_sc)

    counts = {k: 0 for k in REGIME_ORDER}
    for row in labeled:
        counts[str(row["regime"])] = counts.get(str(row["regime"]), 0) + 1

    report = {
        "schema": "fema_asi_regime_build_v1",
        "computed_at": _utc_now(),
        "phase": "ASI-P8",
        "source_baskets": str(baskets_path).replace("\\", "/"),
        "lock_baskets": str(lock_baskets_path).replace("\\", "/") if lock_baskets_path else None,
        "split_profile": splits.get("profile", split_profile),
        "n_baskets": len(labeled),
        "regime_counts": counts,
        "thresholds": thr,
        "taxonomy": REGIME_ORDER,
        "descriptions": REGIME_DESC,
    }

    scorecard = {
        "schema": "fema_asi_regime_scorecard_v1",
        "computed_at": report["computed_at"],
        "deposit": deposit,
        "research": research,
        "train": train_sc,
        "calibrate": cal_sc,
        "lock": lock_sc,
    }

    (out_dir / "regime_thresholds.json").write_text(json.dumps(thr, indent=2) + "\n", encoding="utf-8")
    (out_dir / "regime_build_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out_dir / "regime_scorecard.json").write_text(json.dumps(scorecard, indent=2) + "\n", encoding="utf-8")
    (out_dir / "regime_policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

    # Markdown scorecard
    md_lines = [
        "# ASI-P8 regime scorecard",
        "",
        f"Generated: `{report['computed_at']}`",
        f"Source: `{report['source_baskets']}`",
        f"n baskets: **{len(labeled)}**",
        "",
        "## Policy summary",
        "",
        f"- **allow:** {', '.join(policy['allow']) or '(none)'}",
        f"- **caution:** {', '.join(policy['caution']) or '(none)'}",
        f"- **skip:** {', '.join(policy['skip']) or '(none)'}",
        "",
        "## Research (full source)",
        "",
        "| Regime | n | PF | WR | Net | Steam% | DD% | Action |",
        "| ------ | -: | --: | --: | ---: | -----: | --: | ------ |",
    ]
    for name in REGIME_ORDER:
        r = research["regimes"][name]
        act = policy["table"][name]["action"]
        md_lines.append(
            f"| `{name}` | {r.get('n', 0)} | {r.get('profit_factor', 0)} | {r.get('win_rate', 0)} | "
            f"{r.get('net', 0)} | {r.get('steamroller_rate', 0)} | {r.get('dd_pct', 0)} | **{act}** |"
        )
    md_lines.extend(
        [
            "",
            f"Overall PF **{research['overall']['profit_factor']}** · "
            f"steam **{research['overall']['steamroller_rate']}** · "
            f"DD **{research['overall']['dd_pct']}%**",
            "",
        ]
    )
    if lock_sc:
        md_lines.extend(
            [
                "## Lock / PRODUCTION slice",
                "",
                "| Regime | n | PF | Net | Steam% | DD% |",
                "| ------ | -: | --: | ---: | -----: | --: |",
            ]
        )
        for name in REGIME_ORDER:
            r = lock_sc["regimes"][name]
            if int(r["n"]) == 0:
                continue
            md_lines.append(
                f"| `{name}` | {r['n']} | {r['profit_factor']} | {r['net']} | "
                f"{r['steamroller_rate']} | {r['dd_pct']} |"
            )
        md_lines.append("")

    md_path = out_dir / "regime_scorecard.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # Policy ADR markdown
    adr = "\n".join(
        [
            "# ASI-P8 policy ADR — regime allow / caution / skip",
            "",
            "**ADR id:** `asi_regime_policy_v1`",
            "**Phase:** `ASI-P8-03`",
            f"**Status:** Accepted (shadow only) · {report['computed_at'][:10]}",
            "**Charter:** MT5 executes · Python scores · Human promotes",
            "",
            "## Decision",
            "",
            "| Action | Regimes | Live behaviour |",
            "| ------ | ------- | -------------- |",
            f"| **allow** | {', '.join(f'`{x}`' for x in policy['allow']) or '—'} | Trade normally |",
            f"| **caution** | {', '.join(f'`{x}`' for x in policy['caution']) or '—'} | Log only; no skip |",
            f"| **skip** | {', '.join(f'`{x}`' for x in policy['skip']) or '—'} | Shadow recommend skip at open |",
            "",
            "Default: **live filter** = caution ∪ skip via `InpUseAiRegimeGate` + `regime_gate_v1.txt`.",
            "",
            "## Rules",
            "",
            f"- Policy skip if research n≥{policy['min_n']}, PF<{policy['skip_pf_max']}, "
            f"steam≥{policy['steam_mult']}× baseline, net<0",
            "- Calibrate PF≥1.0 vetoes skip → caution",
            "- **Live filter also blocks caution regimes** (Tester opt-in)",
            "- Prefer missed skips over false blocks on allow set",
            "",
            "## Non-goals",
            "",
            "- No silent lot / architecture thaw",
            "- Do not merge into PRODUCTION without G1 decision",
            "- No tune on 2026 canon",
            "",
        ]
    )
    (out_dir / "regime_policy_adr.md").write_text(adr, encoding="utf-8")

    report["paths"] = {
        "scorecard_json": str(out_dir / "regime_scorecard.json"),
        "scorecard_md": str(md_path),
        "policy": str(out_dir / "regime_policy.json"),
        "policy_adr": str(out_dir / "regime_policy_adr.md"),
        "thresholds": str(out_dir / "regime_thresholds.json"),
    }
    report["policy_summary"] = {
        "allow": policy["allow"],
        "caution": policy["caution"],
        "skip": policy["skip"],
        "live_filter": sorted(set(policy["caution"]) | set(policy["skip"])),
    }
    return report


def export_regime_gate(
    *,
    asi_dir: Path,
    out_name: str = "regime_gate_v1.txt",
    include_caution: bool = True,
) -> dict[str, Any]:
    """Export thresholds + filter regimes for MT5 AiRegimeGate.mqh.

    Live filter = skip ∪ caution (when include_caution=True).
    """
    asi_dir = Path(asi_dir)
    policy_path = asi_dir / "regime_policy.json"
    thr_path = asi_dir / "regime_thresholds.json"
    if not policy_path.is_file() or not thr_path.is_file():
        raise FileNotFoundError("Run asi-regime-build first")

    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    thr = json.loads(thr_path.read_text(encoding="utf-8"))
    filters = sorted(set(policy.get("skip") or []))
    if include_caution:
        filters = sorted(set(filters) | set(policy.get("caution") or []))
    if not filters:
        raise ValueError("No caution/skip regimes to export — nothing to filter")

    lines = [
        "fema_regime_gate_v1",
        f"exported_at\t{_utc_now()}",
        "filter_mode\tcaution_and_skip" if include_caution else "filter_mode\tskip_only",
    ]
    for name in filters:
        lines.append(f"filter\t{name}")
    for key, val in sorted(thr.items()):
        lines.append(f"thr.{key}\t{val}")

    out_txt = asi_dir / out_name
    out_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    meta = {
        "schema": "fema_regime_gate_v1",
        "exported_at": _utc_now(),
        "phase": "ASI-P8",
        "filters": filters,
        "include_caution": include_caution,
        "thresholds": thr,
        "paths": {"txt": str(out_txt)},
    }
    (asi_dir / "regime_gate.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    meta["ok"] = True
    meta["n_filters"] = len(filters)
    return meta


def score_regime_shadow(
    baskets_path: Path,
    *,
    asi_dir: Path,
    deposit: float = 400.0,
    filter_caution: bool = True,
) -> dict[str, Any]:
    asi_dir = Path(asi_dir)
    policy_path = asi_dir / "regime_policy.json"
    thr_path = asi_dir / "regime_thresholds.json"
    if not policy_path.is_file() or not thr_path.is_file():
        raise FileNotFoundError("Run asi-regime-build first")

    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    thr = json.loads(thr_path.read_text(encoding="utf-8"))
    skip_set = set(policy.get("skip") or [])
    if filter_caution:
        skip_set |= set(policy.get("caution") or [])

    rows = attach_regimes(merge_labeled_rows(read_csv_rows(baskets_path)), thr)
    skipped = [r for r in rows if str(r.get("regime")) in skip_set]
    kept = [r for r in rows if str(r.get("regime")) not in skip_set]

    false_skip_winners = sum(
        1 for r in skipped if int(float(r.get("y_steamroller", 0) or 0)) == 0 and _f(r, "profit") > 0
    )
    skipped_steam = sum(int(float(r.get("y_steamroller", 0) or 0)) for r in skipped)
    skip_n = len(skipped)

    base = regime_metrics(rows, deposit=deposit)
    kept_m = regime_metrics(kept, deposit=deposit)
    shadow = {
        "skip_regimes": sorted(skip_set),
        "filter_caution": filter_caution,
        "skip_n": skip_n,
        "skip_rate": round(skip_n / len(rows), 4) if rows else 0.0,
        "skipped_steamrollers": skipped_steam,
        "false_skip_winners": false_skip_winners,
        "steamroller_precision": round(skipped_steam / skip_n, 4) if skip_n else 0.0,
        "net_skipped": round(sum(_f(r, "profit") for r in skipped), 2),
        "baseline": base,
        "kept": kept_m,
        "dd_baseline_pct": base.get("dd_pct"),
        "dd_kept_pct": kept_m.get("dd_pct"),
    }

    out = {
        "schema": "fema_asi_regime_shadow_v1",
        "computed_at": _utc_now(),
        "baskets_path": str(baskets_path).replace("\\", "/"),
        "n_baskets": len(rows),
        "shadow": shadow,
        "policy": "live_filter_caution_and_skip" if filter_caution else "shadow_skip_only",
    }
    return out


def write_regime_review(asi_dir: Path) -> dict[str, Any]:
    asi_dir = Path(asi_dir)
    scorecard = json.loads((asi_dir / "regime_scorecard.json").read_text(encoding="utf-8"))
    policy = json.loads((asi_dir / "regime_policy.json").read_text(encoding="utf-8"))
    skip = policy.get("skip") or []
    caution = policy.get("caution") or []
    live_filter = sorted(set(skip) | set(caution))

    shadow_path = asi_dir / "asi_shadow_regime.json"
    shadow = None
    if shadow_path.is_file():
        shadow = json.loads(shadow_path.read_text(encoding="utf-8"))

    verdict = "REGIME OK - live filter Alternate (caution+skip)"
    if not live_filter:
        verdict = "REGIME WEAK - no caution/skip to filter"
    elif shadow:
        sh = shadow.get("shadow") or {}
        if float(sh.get("net_skipped") or 0) > 50 and int(sh.get("false_skip_winners") or 0) > int(
            sh.get("skipped_steamrollers") or 0
        ):
            verdict = "REGIME CAUTION - filter may cut winners; Tester required"

    pack = {
        "schema": "fema_asi_p8_review_pack_v1",
        "computed_at": _utc_now(),
        "philosophy": "live_filter_caution_and_skip",
        "allow": policy.get("allow"),
        "caution": caution,
        "skip": skip,
        "live_filter": live_filter,
        "research_overall": (scorecard.get("research") or {}).get("overall"),
        "lock_overall": (scorecard.get("lock") or {}).get("overall") if scorecard.get("lock") else None,
        "shadow": (shadow or {}).get("shadow"),
        "verdict_hint": verdict,
        "policy": "InpUseAiRegimeGate",
    }
    out_json = asi_dir / "asi_p8_review_pack.json"
    out_md = asi_dir / "asi_p8_review_pack.md"
    out_json.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
    md = "\n".join(
        [
            "# ASI-P8 review — regime intelligence",
            "",
            f"Generated: `{pack['computed_at']}`",
            "",
            f"- allow: `{', '.join(pack.get('allow') or [])}`",
            f"- caution: `{', '.join(caution)}`",
            f"- skip: `{', '.join(skip)}`",
            f"- **live filter:** `{', '.join(live_filter)}`",
            "",
            f"**Verdict:** {verdict}",
            "",
            "Live: `InpUseAiRegimeGate=true` + `regime_gate_v1.txt` (caution ∪ skip).",
            "",
            "See `regime_scorecard.md` · `regime_policy_adr.md`.",
            "",
        ]
    )
    out_md.write_text(md, encoding="utf-8")
    pack["paths"] = {"json": str(out_json), "md": str(out_md)}
    return pack
