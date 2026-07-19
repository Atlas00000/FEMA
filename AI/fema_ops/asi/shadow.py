"""ASI-P3 — TEP shadow scoring on registered runs (no live skip)."""

from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from csv_util import read_csv_rows
from fema_ops.asi.dataset import basket_run_metrics, merge_labeled_rows
from fema_ops.asi.tep import evaluate_threshold, featurize, predict_proba
from paths import KB_DIR, KB_RUNS_DIR, REPO_ROOT

ASI_DIR = KB_DIR / "asi"
DEFAULT_MODEL = ASI_DIR / "tep_model.pkl"
DEFAULT_CARD = ASI_DIR / "tep_model_card.json"
SHADOWS_DIR = ASI_DIR / "shadows"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _f(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def _rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(p).replace("\\", "/")


def load_tep_bundle(model_path: Path | None = None) -> dict[str, Any]:
    path = Path(model_path) if model_path else DEFAULT_MODEL
    if not path.is_file():
        raise FileNotFoundError(f"TEP model missing: {path} — run asi-train first")
    with path.open("rb") as fh:
        bundle = pickle.load(fh)
    if "model" not in bundle or "feature_names" not in bundle:
        raise ValueError("invalid tep_model.pkl")
    thr = float(bundle.get("threshold", 1.0))
    if DEFAULT_CARD.is_file():
        card = json.loads(DEFAULT_CARD.read_text(encoding="utf-8"))
        thr = float(card.get("threshold", thr))
    return {
        "model": bundle["model"],
        "feature_names": list(bundle["feature_names"]),
        "threshold": thr,
        "model_path": _rel(path),
    }


def equity_dd_pct(profits: list[float], deposit: float = 400.0) -> float:
    """Max balance drawdown % from sequential basket PnL (shadow proxy)."""
    if not profits or deposit <= 0:
        return 0.0
    bal = deposit
    peak = bal
    max_dd = 0.0
    for p in profits:
        bal += p
        if bal > peak:
            peak = bal
        if peak > 0:
            dd = (peak - bal) / peak * 100.0
            if dd > max_dd:
                max_dd = dd
    return round(max_dd, 2)


def kill_criteria(
    shadow: dict[str, Any],
    *,
    max_false_win_ratio: float = 2.0,
    min_steamroller_precision: float = 0.30,
    max_skip: float = 0.12,
) -> dict[str, Any]:
    """ASI-P3-04 — if false-skip winners dominate, retune or stop."""
    skip_n = int(shadow.get("skip_n") or 0)
    false_w = int(shadow.get("false_skip_winners") or 0)
    steam = int(shadow.get("skipped_steamrollers") or 0)
    skip_rate = float(shadow.get("skip_rate") or 0.0)
    prec = float(shadow.get("steamroller_precision") or 0.0)
    net_skipped = float(shadow.get("net_skipped") or 0.0)

    reasons: list[str] = []
    if skip_n == 0:
        status = "empty_skip"
        reasons.append("no baskets above threshold")
    else:
        if skip_rate > max_skip + 1e-9:
            reasons.append(f"skip_rate {skip_rate:.1%} > {max_skip:.0%}")
        if prec < min_steamroller_precision:
            reasons.append(f"precision {prec:.1%} < {min_steamroller_precision:.0%}")
        if steam > 0 and false_w > steam * max_false_win_ratio:
            reasons.append(
                f"false_skip_winners {false_w} > {max_false_win_ratio}x steamrollers {steam}"
            )
        elif steam == 0 and false_w > 0:
            reasons.append(f"skipped only winners ({false_w})")
        if net_skipped > 0:
            reasons.append(f"net_skipped {net_skipped:+.2f} > 0 (cutting winners)")

        status = "kill" if reasons else "ok"

    return {
        "status": status,
        "action": (
            "retune_threshold_or_stop"
            if status == "kill"
            else ("observe" if status == "empty_skip" else "continue_shadow")
        ),
        "reasons": reasons,
        "gates": {
            "max_false_win_ratio": max_false_win_ratio,
            "min_steamroller_precision": min_steamroller_precision,
            "max_skip": max_skip,
        },
    }


def score_baskets(
    baskets_path: Path,
    *,
    model_path: Path | None = None,
    deposit: float = 400.0,
) -> dict[str, Any]:
    bundle = load_tep_bundle(model_path)
    raw = read_csv_rows(baskets_path)
    labeled = merge_labeled_rows(raw)
    if not labeled:
        raise ValueError(f"no baskets in {baskets_path}")

    names = bundle["feature_names"]
    X, _y = featurize(labeled, names)
    proba = predict_proba(bundle["model"], X)
    thr = bundle["threshold"]
    mask = proba >= thr
    metrics = evaluate_threshold(labeled, proba, thr)

    all_profits = [_f(r, "profit") for r in labeled]
    kept_profits = [_f(r, "profit") for r, s in zip(labeled, mask) if not s]
    skipped_profits = [_f(r, "profit") for r, s in zip(labeled, mask) if s]

    baseline = basket_run_metrics(labeled)
    kept_rows = [r for r, s in zip(labeled, mask) if not s]
    kept_m = basket_run_metrics(kept_rows) if kept_rows else {}

    shadow = {
        **metrics,
        "skipped_pnl": metrics.get("net_skipped"),
        "dd_all_pct": equity_dd_pct(all_profits, deposit),
        "dd_if_skipped_pct": equity_dd_pct(kept_profits, deposit),
        "dd_delta_pct": round(
            equity_dd_pct(all_profits, deposit) - equity_dd_pct(kept_profits, deposit),
            2,
        ),
        "baseline": baseline,
        "kept": kept_m,
        "net_delta": round(
            float(kept_m.get("net", 0) or 0) - float(baseline.get("net", 0) or 0),
            2,
        ),
    }
    kill = kill_criteria(shadow)

    return {
        "schema": "fema_asi_shadow_run_v1",
        "computed_at": _utc_now(),
        "asi_track": "tep",
        "baskets_path": _rel(baskets_path),
        "model_path": bundle["model_path"],
        "threshold": thr,
        "deposit": deposit,
        "shadow": shadow,
        "kill": kill,
        "skipped_ids": [
            str(r.get("basket_id", ""))
            for r, s in zip(labeled, mask)
            if s
        ],
        "proba_summary": {
            "min": round(float(np.min(proba)), 4),
            "max": round(float(np.max(proba)), 4),
            "mean": round(float(np.mean(proba)), 4),
            "p90": round(float(np.quantile(proba, 0.90)), 4),
        },
    }


def score_run(
    run_id: str,
    *,
    runs_dir: Path | None = None,
    model_path: Path | None = None,
    deposit: float = 400.0,
) -> dict[str, Any]:
    runs_dir = runs_dir or KB_RUNS_DIR
    folder = runs_dir / run_id
    metrics_path = folder / "metrics.json"
    if not metrics_path.is_file():
        raise FileNotFoundError(f"run not found: {folder}")

    meta = json.loads(metrics_path.read_text(encoding="utf-8"))
    baskets_rel = meta.get("baskets_path") or ""
    baskets = (REPO_ROOT / baskets_rel).resolve() if baskets_rel else None
    if baskets is None or not baskets.is_file():
        # try live pointer
        from paths import LATEST_BASKETS

        baskets = LATEST_BASKETS
    if not baskets.is_file():
        raise FileNotFoundError(f"baskets missing for {run_id}: {baskets_rel}")

    report = score_baskets(baskets, model_path=model_path, deposit=deposit)
    report["run_id"] = run_id
    report["preset"] = meta.get("preset")
    report["role"] = meta.get("role")
    report["window"] = meta.get("window")
    report["run_metrics"] = meta.get("metrics")

    # Write under run dir + shadows index
    out_run = folder / f"asi_shadow_{run_id}.json"
    out_run.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    SHADOWS_DIR.mkdir(parents=True, exist_ok=True)
    out_shadow = SHADOWS_DIR / f"asi_shadow_{run_id}.json"
    out_shadow.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    # Stamp metrics.json with shadow summary (non-breaking)
    meta["asi_shadow"] = {
        "schema": "fema_asi_shadow_stamp_v1",
        "computed_at": report["computed_at"],
        "skip_n": report["shadow"]["skip_n"],
        "skip_rate": report["shadow"]["skip_rate"],
        "skipped_pnl": report["shadow"]["skipped_pnl"],
        "dd_if_skipped_pct": report["shadow"]["dd_if_skipped_pct"],
        "dd_all_pct": report["shadow"]["dd_all_pct"],
        "false_skip_winners": report["shadow"]["false_skip_winners"],
        "steamroller_precision": report["shadow"]["steamroller_precision"],
        "kill_status": report["kill"]["status"],
        "path": _rel(out_run),
    }
    metrics_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    report["paths"] = {"run": _rel(out_run), "shadows": _rel(out_shadow)}
    return report


def write_review_pack(
    *,
    production_run_id: str | None = None,
    asi_dir: Path | None = None,
) -> dict[str, Any]:
    """ASI-P3-03 — compare TEP shadow vs PRODUCTION on canonical window."""
    asi_dir = asi_dir or ASI_DIR
    promote = asi_dir / "dataset_promote_frozen.csv"
    if not promote.is_file():
        raise FileNotFoundError("dataset_promote_frozen.csv missing — run asi-build")

    shadow = score_baskets(promote)
    kill = shadow["kill"]
    sh = shadow["shadow"]
    base = sh.get("baseline") or {}
    kept = sh.get("kept") or {}

    pack = {
        "schema": "fema_asi_p3_review_pack_v1",
        "computed_at": _utc_now(),
        "production_run_id": production_run_id or "20260101_PRODUCTION_bcc8b9b0_02",
        "threshold": shadow["threshold"],
        "compare": {
            "baseline_pf": base.get("profit_factor"),
            "baseline_n": base.get("n"),
            "baseline_net": base.get("net"),
            "baseline_wr": base.get("win_rate"),
            "kept_pf": kept.get("profit_factor"),
            "kept_n": kept.get("n"),
            "kept_net": kept.get("net"),
            "kept_wr": kept.get("win_rate"),
            "skip_n": sh.get("skip_n"),
            "skip_rate": sh.get("skip_rate"),
            "skipped_pnl": sh.get("skipped_pnl"),
            "dd_all_pct": sh.get("dd_all_pct"),
            "dd_if_skipped_pct": sh.get("dd_if_skipped_pct"),
            "dd_delta_pct": sh.get("dd_delta_pct"),
            "false_skip_winners": sh.get("false_skip_winners"),
            "skipped_steamrollers": sh.get("skipped_steamrollers"),
            "steamroller_precision": sh.get("steamroller_precision"),
        },
        "kill": kill,
        "operator_signoff": {
            "shadow_net_positive": None,
            "signed_by": None,
            "signed_at": None,
            "notes": "Human must set shadow_net_positive true/false before ASI-P4",
        },
        "verdict_hint": (
            "KILL — do not proceed to live gate"
            if kill["status"] == "kill"
            else "SHADOW OK — operator may sign for P4 if DD/PF story holds"
        ),
    }

    out_json = asi_dir / "asi_p3_review_pack.json"
    out_md = asi_dir / "asi_p3_review_pack.md"
    out_json.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")

    c = pack["compare"]
    md = "\n".join(
        [
            "# ASI-P3 review pack — TEP shadow vs PRODUCTION canon",
            "",
            f"Generated: `{pack['computed_at']}`",
            f"Threshold: **{pack['threshold']}** (frozen from P2 calibrate)",
            "",
            "## Compare (canonical 2026.01–07)",
            "",
            "| Slice | n | PF | WR | Net | DD% (equity proxy) |",
            "| ----- | -: | --: | --: | ---: | ---: |",
            f"| Baseline (all) | {c['baseline_n']} | {c['baseline_pf']} | {c['baseline_wr']} | {c['baseline_net']} | {c['dd_all_pct']} |",
            f"| After TEP skip | {c['kept_n']} | {c['kept_pf']} | {c['kept_wr']} | {c['kept_net']} | {c['dd_if_skipped_pct']} |",
            "",
            f"- skip_n / rate: **{c['skip_n']}** / **{c['skip_rate']}**",
            f"- skipped_pnl: **{c['skipped_pnl']}**",
            f"- steamrollers skipped: **{c['skipped_steamrollers']}** · false-skip winners: **{c['false_skip_winners']}**",
            f"- precision: **{c['steamroller_precision']}**",
            "",
            "## Kill criteria",
            "",
            f"- status: **`{kill['status']}`** → `{kill['action']}`",
            f"- reasons: {kill['reasons'] or '_(none)_'}",
            "",
            f"**Verdict hint:** {pack['verdict_hint']}",
            "",
            "## Sign-off (human)",
            "",
            "- [ ] Shadow looks net-positive (PF/DD/n)",
            "- [ ] False-skip winners acceptable",
            "- [ ] Proceed to ASI-P4 design **or** retune / stop",
            "",
            "NO AUTO-PROMOTE · no live skip until P4 + human promote.",
            "",
        ]
    )
    out_md.write_text(md, encoding="utf-8")
    pack["paths"] = {"json": _rel(out_json), "md": _rel(out_md)}
    return pack


def _guardrail_slice_row(label: str, report: dict[str, Any]) -> dict[str, Any]:
    sh = report.get("shadow") or {}
    base = sh.get("baseline") or {}
    kept = sh.get("kept") or {}
    kill = report.get("kill") or {}
    return {
        "slice": label,
        "window": report.get("window"),
        "n": base.get("n"),
        "skip_n": sh.get("skip_n"),
        "skip_rate": sh.get("skip_rate"),
        "steamroller_precision": sh.get("steamroller_precision"),
        "false_skip_winners": sh.get("false_skip_winners"),
        "skipped_steamrollers": sh.get("skipped_steamrollers"),
        "net_skipped": sh.get("net_skipped"),
        "dd_all_pct": sh.get("dd_all_pct"),
        "dd_if_skipped_pct": sh.get("dd_if_skipped_pct"),
        "dd_delta_pct": sh.get("dd_delta_pct"),
        "kept_pf": kept.get("profit_factor"),
        "kept_n": kept.get("n"),
        "kill_status": kill.get("status"),
    }


def write_guardrail_review_pack(*, asi_dir: Path | None = None) -> dict[str, Any]:
    """Guardrail-first review: holdout kill gates, not production parity."""
    asi_dir = asi_dir or ASI_DIR
    splits_path = asi_dir / "splits.json"
    splits: dict[str, Any] = {}
    if splits_path.is_file():
        splits = json.loads(splits_path.read_text(encoding="utf-8"))

    holdout = asi_dir / "dataset_calibrate.csv"
    train_path = asi_dir / "dataset_train.csv"
    full_path = asi_dir / "dataset_full.csv"
    if not holdout.is_file():
        raise FileNotFoundError("dataset_calibrate.csv missing — run asi-build first")

    cal_window = splits.get("calibrate") or {}
    holdout_report = score_baskets(holdout)
    holdout_report["window"] = (
        f"{cal_window.get('start', '?')}–{cal_window.get('end', '?')}"
    )

    slices: list[dict[str, Any]] = [_guardrail_slice_row("holdout_calibrate", holdout_report)]
    optional: dict[str, Any] = {}
    if train_path.is_file():
        train_window = splits.get("train") or {}
        train_report = score_baskets(train_path)
        train_report["window"] = (
            f"{train_window.get('start', '?')}–{train_window.get('end', '?')}"
        )
        slices.append(_guardrail_slice_row("train_in_sample", train_report))
        optional["train"] = train_report
    if full_path.is_file():
        full_report = score_baskets(full_path)
        full_report["window"] = "research_full"
        slices.append(_guardrail_slice_row("research_full", full_report))
        optional["full"] = full_report

    holdout_kill = holdout_report["kill"]
    profile = splits.get("profile") or "default"
    pack = {
        "schema": "fema_asi_guardrail_review_v1",
        "computed_at": _utc_now(),
        "philosophy": "guardrails_not_gates",
        "split_profile": profile,
        "threshold": holdout_report["threshold"],
        "holdout": _guardrail_slice_row("holdout_calibrate", holdout_report),
        "slices": slices,
        "kill": holdout_kill,
        "operator_signoff": {
            "guardrails_acceptable": None,
            "signed_by": None,
            "signed_at": None,
            "notes": "Pass = holdout kill ok or empty_skip observe; not production PF parity",
        },
        "verdict_hint": (
            "GUARDRAIL KILL — retune threshold or stop"
            if holdout_kill["status"] == "kill"
            else (
                "GUARDRAIL OBSERVE — empty skip; model scores but skips nothing"
                if holdout_kill["status"] == "empty_skip"
                else "GUARDRAIL OK — holdout passes kill gates"
            )
        ),
    }

    out_json = asi_dir / "asi_guardrail_review_pack.json"
    out_md = asi_dir / "asi_guardrail_review_pack.md"
    out_json.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")

    h = pack["holdout"]
    md_lines = [
        "# ASI guardrail review — TEP holdout (not production parity)",
        "",
        f"Generated: `{pack['computed_at']}`",
        f"Split profile: **{profile}**",
        f"Threshold: **{pack['threshold']}** (frozen from calibrate tune)",
        "",
        "## Philosophy",
        "",
        "Candidate must pass **kill gates** on the guardrail holdout window. "
        "We do **not** require beating or matching live PRODUCTION PF/WR.",
        "",
        f"## Holdout ({holdout_report.get('window', 'calibrate')})",
        "",
        "| Metric | Value |",
        "| ------ | ----: |",
        f"| n | {h['n']} |",
        f"| skip_n / rate | {h['skip_n']} / {h['skip_rate']} |",
        f"| steamroller precision | {h['steamroller_precision']} |",
        f"| false-skip winners | {h['false_skip_winners']} |",
        f"| skipped steamrollers | {h['skipped_steamrollers']} |",
        f"| net skipped | {h['net_skipped']} |",
        f"| DD all → if skipped | {h['dd_all_pct']}% → {h['dd_if_skipped_pct']}% (Δ {h['dd_delta_pct']}%) |",
        "",
        "## Kill criteria (holdout)",
        "",
        f"- status: **`{holdout_kill['status']}`** → `{holdout_kill['action']}`",
        f"- reasons: {holdout_kill['reasons'] or '_(none)_'}",
        "",
        f"**Verdict:** {pack['verdict_hint']}",
        "",
        "## All slices",
        "",
        "| Slice | window | n | skip | precision | false wins | net skip | DD Δ% | kill |",
        "| ----- | ------ | -: | ---: | --------: | ---------: | -------: | ----: | ---- |",
    ]
    for row in slices:
        md_lines.append(
            f"| {row['slice']} | {row.get('window', '')} | {row['n']} | "
            f"{row['skip_n']} ({row['skip_rate']}) | {row['steamroller_precision']} | "
            f"{row['false_skip_winners']} | {row['net_skipped']} | {row['dd_delta_pct']} | "
            f"{row['kill_status']} |"
        )
    md_lines.extend(
        [
            "",
            "NO AUTO-PROMOTE · guardrail candidate ≠ production lock.",
            "",
        ]
    )
    out_md.write_text("\n".join(md_lines), encoding="utf-8")
    pack["paths"] = {"json": _rel(out_json), "md": _rel(out_md)}
    return pack


def patch_model_card_kill(asi_dir: Path | None = None) -> None:
    """Write kill criteria into tep_model_card.json (ASI-P3-04)."""
    asi_dir = asi_dir or ASI_DIR
    card_path = asi_dir / "tep_model_card.json"
    if not card_path.is_file():
        return
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card["kill_criteria"] = {
        "schema": "fema_asi_kill_v1",
        "rules": [
            "skip_rate > 12% → kill",
            "steamroller_precision < 30% → kill",
            "false_skip_winners > 2× skipped_steamrollers → kill",
            "net_skipped > 0 (cutting winners) → kill",
            "empty skip → observe only",
        ],
        "action_on_kill": "retune threshold on calibrate or stop Track A gate",
        "updated_at": _utc_now(),
    }
    card["next"] = "ASI-P4 after operator signs asi_p3_review_pack"
    card_path.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
