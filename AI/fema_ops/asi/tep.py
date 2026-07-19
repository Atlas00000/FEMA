"""ASI-P2 — offline Trend Expansion Predictor (TEP)."""

from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from csv_util import read_csv_rows
from fema_ops.asi.dataset import basket_run_metrics, shadow_skip_v0
from fema_ops.asi.features import TEP_DERIVED, TEP_INTERACTIONS

STATIC_FEATURES = [
    "ema_sep_atr",
    "ema_slope",
    "atr",
    "adx",
    "dist_ema_trend_atr",
    "spread_points",
    "hour",
    "dow",
    "roll_wr",
    "roll_pf",
    "roll_n",
]

ACCEL_FEATURES = list(TEP_DERIVED)

TEP_FEATURES = STATIC_FEATURES + ACCEL_FEATURES

ADX_ONLY_FEATURES = ["adx", "adx_accel", "atr", "ema_slope", "dist_ema_trend_atr"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _f(row: dict, key: str, default: float = 0.0) -> float:
    try:
        v = float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default
    # Cap no-loss PF sentinel (legacy logs used 99) so TEP features stay in-distribution
    if key == "roll_pf" and v > 5.0:
        return 5.0
    return v


def featurize(rows: list[dict], feature_names: list[str]) -> tuple[np.ndarray, np.ndarray]:
    X, y = [], []
    for row in rows:
        vec = [_f(row, c) for c in feature_names]
        if "is_sell" in feature_names:
            vec[feature_names.index("is_sell")] = (
                1.0 if str(row.get("direction", "")).upper() == "SELL" else 0.0
            )
        X.append(vec)
        y.append(int(float(row.get("y_steamroller", 0) or 0)))
    return np.asarray(X, dtype=float), np.asarray(y, dtype=int)


def build_model() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    C=0.35,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def predict_proba(model: Pipeline, X: np.ndarray) -> np.ndarray:
    return model.predict_proba(X)[:, 1]


def skip_metrics(rows: list[dict], skip_mask: np.ndarray) -> dict[str, Any]:
    skipped = [r for r, s in zip(rows, skip_mask) if s]
    kept = [r for r, s in zip(rows, skip_mask) if not s]
    n = len(rows)
    false_win = sum(
        1 for r in skipped if int(r.get("y_steamroller", 0)) == 0 and _f(r, "profit") > 0
    )
    true_steam = sum(int(r.get("y_steamroller", 0)) for r in skipped)
    total_steam = sum(int(r.get("y_steamroller", 0)) for r in rows)
    return {
        "n": n,
        "skip_n": len(skipped),
        "skip_rate": round(len(skipped) / n, 4) if n else 0.0,
        "steamroller_precision": round(true_steam / len(skipped), 4) if skipped else 0.0,
        "steamroller_recall": round(true_steam / total_steam, 4) if total_steam else 0.0,
        "false_skip_winners": false_win,
        "skipped_steamrollers": true_steam,
        "net_skipped": round(sum(_f(r, "profit") for r in skipped), 2),
        "net_kept": round(sum(_f(r, "profit") for r in kept), 2),
        "kept_pf": basket_run_metrics(kept).get("profit_factor", 0.0) if kept else 0.0,
        "kept_n": len(kept),
        "kept_wr": basket_run_metrics(kept).get("win_rate", 0.0) if kept else 0.0,
    }


def evaluate_threshold(
    rows: list[dict], proba: np.ndarray, threshold: float
) -> dict[str, Any]:
    mask = proba >= threshold
    m = skip_metrics(rows, mask)
    m["threshold"] = round(float(threshold), 6)
    return m


def select_permissive_threshold(
    rows: list[dict],
    proba: np.ndarray,
    *,
    max_skip: float = 0.10,
    min_trade_frac: float = 0.90,
    min_precision: float = 0.35,
    strict: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Lock skip policy on calibration — precision-first, ≤max_skip."""
    if strict:
        return select_strict_threshold(
            rows,
            proba,
            max_skip=max_skip,
            min_trade_frac=min_trade_frac,
            min_precision=max(min_precision, 0.40),
        )

    n = len(rows)
    if n == 0:
        empty = {"threshold": 1.0, "skip_rate": 0.0, "note": "empty calibrate"}
        return empty, []

    targets = [0.03, 0.05, 0.08, 0.10]
    candidates: list[dict[str, Any]] = []
    for t in targets:
        if t > max_skip + 1e-9:
            continue
        thr = float(np.quantile(proba, 1.0 - t))
        ev = evaluate_threshold(rows, proba, thr)
        if ev["skip_n"] == 0:
            continue
        kept_frac = ev["kept_n"] / n
        prec = ev["steamroller_precision"]
        net_ok = ev["net_skipped"] <= 0.0
        eligible = (
            kept_frac >= min_trade_frac - 1e-9
            and prec >= 0.35
            and net_ok
            and ev["false_skip_winners"] <= ev["skipped_steamrollers"] * 2
        )
        score = (
            80.0 * prec
            + 30.0 * ev["steamroller_recall"]
            + (20.0 if net_ok else -30.0)
            - 5.0 * ev["false_skip_winners"]
            - 10.0 * abs(ev["skip_rate"] - min(t, max_skip))
        )
        ev["score"] = round(score, 4)
        ev["skip_quantile"] = t
        ev["cal_eligible"] = eligible
        candidates.append(ev)

    eligible = [c for c in candidates if c.get("cal_eligible")]
    pool = eligible if eligible else candidates
    if not pool:
        return {
            "threshold": 1.0,
            "skip_rate": 0.0,
            "skip_n": 0,
            "note": "no policy met gates; empty skip",
            "cal_eligible": True,
        }, candidates

    pool.sort(key=lambda d: d["score"], reverse=True)
    return pool[0], candidates


def select_strict_threshold(
    rows: list[dict],
    proba: np.ndarray,
    *,
    max_skip: float = 0.05,
    min_trade_frac: float = 0.90,
    min_precision: float = 0.40,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Scan proba levels — precision-first, no net-positive skips, cap false winners."""
    n = len(rows)
    if n == 0:
        return {"threshold": 1.0, "skip_rate": 0.0, "note": "empty calibrate"}, []

    # Unique thresholds (high → low) plus quantile anchors
    anchors = [float(np.quantile(proba, q)) for q in (0.99, 0.95, 0.90, 0.85, 0.80, 0.75)]
    thresholds = sorted({float(t) for t in np.unique(proba)} | set(anchors), reverse=True)

    candidates: list[dict[str, Any]] = []
    for thr in thresholds:
        ev = evaluate_threshold(rows, proba, thr)
        if ev["skip_n"] == 0:
            continue
        if ev["skip_rate"] > max_skip + 1e-9:
            continue
        if ev["kept_n"] / n < min_trade_frac - 1e-9:
            continue
        prec = ev["steamroller_precision"]
        net_ok = ev["net_skipped"] <= 0.0
        false_ok = ev["false_skip_winners"] <= ev["skipped_steamrollers"]
        eligible = prec >= min_precision and net_ok and false_ok
        score = (
            100.0 * prec
            + 25.0 * ev["steamroller_recall"]
            + (30.0 if net_ok else -50.0)
            - 8.0 * ev["false_skip_winners"]
            - 15.0 * ev["skip_rate"]
        )
        ev["score"] = round(score, 4)
        ev["skip_quantile"] = ev["skip_rate"]
        ev["cal_eligible"] = eligible
        ev["mode"] = "strict"
        candidates.append(ev)

    eligible = [c for c in candidates if c.get("cal_eligible")]
    if eligible:
        eligible.sort(key=lambda d: d["score"], reverse=True)
        return eligible[0], candidates

    # No strict policy — empty skip (observe)
    empty = {
        "threshold": 1.0,
        "skip_rate": 0.0,
        "skip_n": 0,
        "note": "strict: no threshold met gates; empty skip",
        "cal_eligible": True,
        "mode": "strict_empty",
    }
    return empty, candidates


def safe_auc(y: np.ndarray, p: np.ndarray) -> float | None:
    if len(np.unique(y)) < 2:
        return None
    try:
        return round(float(roc_auc_score(y, p)), 4)
    except ValueError:
        return None


def train_tep_variant(
    train_rows: list[dict],
    cal_rows: list[dict],
    feature_names: list[str],
    *,
    max_skip: float = 0.10,
    strict: bool = False,
) -> dict[str, Any]:
    names = list(feature_names)
    if "is_sell" not in names:
        names = names + ["is_sell"]

    X_train, y_train = featurize(train_rows, names)
    model = build_model()
    model.fit(X_train, y_train)

    X_cal, y_cal = featurize(cal_rows, names)
    p_train = predict_proba(model, X_train)
    p_cal = predict_proba(model, X_cal)

    selected, candidates = select_permissive_threshold(
        cal_rows, p_cal, max_skip=max_skip, strict=strict
    )
    thr = float(selected.get("threshold", 1.0))

    return {
        "feature_names": names,
        "model": model,
        "auc_train": safe_auc(y_train, p_train),
        "auc_calibrate": safe_auc(y_cal, p_cal),
        "threshold": thr,
        "skip_quantile": selected.get("skip_quantile", 0.0),
        "calibrate_eval": evaluate_threshold(cal_rows, p_cal, thr),
        "calibrate_candidates": candidates,
        "proba_calibrate": p_cal,
    }


def ablation_note(
    results: dict[str, dict[str, Any]],
    *,
    prefer_policy: bool = False,
) -> dict[str, Any]:
    full = results.get("tep_full") or {}
    static = results.get("static_only") or {}
    adx = results.get("adx_only") or {}

    def _rank(k: str) -> tuple:
        r = results[k]
        ev = r.get("calibrate_eval") or {}
        skip_n = int(ev.get("skip_n") or 0)
        prec = float(ev.get("steamroller_precision") or 0.0)
        net = float(ev.get("net_skipped") or 0.0)
        auc = float(r.get("auc_calibrate") or 0.0)
        # Guardrail: prefer a real skip policy that cuts losses over empty AUC winner
        if prefer_policy:
            has_policy = 1 if skip_n > 0 else 0
            net_ok = 1 if net <= 0.0 else 0
            return (has_policy, net_ok, prec, skip_n, auc)
        return (auc, float(ev.get("score") or 0.0))

    return {
        "tep_full_auc_cal": full.get("auc_calibrate"),
        "static_only_auc_cal": static.get("auc_calibrate"),
        "adx_only_auc_cal": adx.get("auc_calibrate"),
        "tep_beats_static": (full.get("auc_calibrate") or 0) >= (static.get("auc_calibrate") or 0),
        "tep_beats_adx": (full.get("auc_calibrate") or 0) >= (adx.get("auc_calibrate") or 0),
        "prefer_policy": prefer_policy,
        "winner": max(results.keys(), key=_rank),
    }


def write_model_card(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def train_tep(
    *,
    asi_dir: Path,
    max_skip: float = 0.10,
    strict: bool = False,
    guardrail: bool = False,
) -> dict[str, Any]:
    asi_dir = Path(asi_dir)
    train_rows = read_csv_rows(asi_dir / "dataset_train.csv")
    cal_rows = read_csv_rows(asi_dir / "dataset_calibrate.csv")
    promote_path = asi_dir / "dataset_promote_frozen.csv"
    promote_rows = read_csv_rows(promote_path) if promote_path.is_file() else []

    if not train_rows or not cal_rows:
        raise FileNotFoundError("Run asi-build first (dataset_train + dataset_calibrate)")

    variants = {
        "tep_full": TEP_FEATURES,
        "static_only": STATIC_FEATURES,
        "adx_only": ADX_ONLY_FEATURES,
    }
    trained: dict[str, dict[str, Any]] = {}
    for name, feats in variants.items():
        trained[name] = train_tep_variant(
            train_rows, cal_rows, feats, max_skip=max_skip, strict=strict
        )

    best_name = ablation_note(trained, prefer_policy=guardrail)["winner"]
    best = trained[best_name]
    model = best["model"]
    feature_names = best["feature_names"]
    threshold = best["threshold"]

    def eval_split(rows: list[dict], label: str) -> dict[str, Any] | None:
        if not rows:
            return None
        X, y = featurize(rows, feature_names)
        p = predict_proba(model, X)
        ev = evaluate_threshold(rows, p, threshold)
        ev["auc"] = safe_auc(y, p)
        ev["baseline"] = basket_run_metrics(rows)
        ev["split"] = label
        return ev

    promote_eval = eval_split(promote_rows, "promote_frozen")
    threshold_guard: dict[str, Any] | None = None
    calibrate_threshold = threshold
    if strict and promote_eval and not guardrail:
        from fema_ops.asi.shadow import kill_criteria

        prom_kill = kill_criteria(promote_eval)
        if prom_kill["status"] == "kill":
            threshold = 1.0
            threshold_guard = {
                "action": "downgrade_empty_skip",
                "calibrate_threshold": calibrate_threshold,
                "promote_kill": prom_kill,
            }
            promote_eval = eval_split(promote_rows, "promote_frozen")

    # Compare to impulse shadow v0 on calibrate
    impulse_shadow = shadow_skip_v0(cal_rows, train_rows=train_rows, skip_quantile=0.90)

    report: dict[str, Any] = {
        "schema": "fema_asi_tep_model_card_v1",
        "computed_at": _utc_now(),
        "phase": "ASI-P2" + ("_strict" if strict else ""),
        "label": "y_steamroller",
        "model_kind": "logistic_regression",
        "tune_mode": "strict" if strict else "permissive",
        "guardrail_mode": guardrail,
        "variant_selected": best_name,
        "feature_names": feature_names,
        "threshold": threshold,
        "calibrate_threshold": calibrate_threshold,
        "threshold_guard": threshold_guard,
        "skip_quantile_cal": best.get("skip_quantile"),
        "max_skip": max_skip,
        "auc_train": best.get("auc_train"),
        "auc_calibrate": best.get("auc_calibrate"),
        "calibrate_eval": best.get("calibrate_eval"),
        "promote_frozen_eval": promote_eval,
        "ablation": ablation_note(trained, prefer_policy=guardrail),
        "ablation_detail": {
            k: {
                "auc_train": v.get("auc_train"),
                "auc_calibrate": v.get("auc_calibrate"),
                "calibrate_eval": v.get("calibrate_eval"),
            }
            for k, v in trained.items()
        },
        "impulse_v0_calibrate": {
            "skip_rate": impulse_shadow.get("skip_rate"),
            "skipped_steamrollers": impulse_shadow.get("skipped_steamrollers"),
            "false_skip_winners": impulse_shadow.get("skipped_winners_false"),
        },
        "non_goals": [
            "no live MT5 gate (P4)",
            "no threshold tune on promote_frozen",
            "permissive skip only",
        ],
        "next": "ASI-P3 shadow ops",
    }

    model_path = asi_dir / "tep_model.pkl"
    with model_path.open("wb") as fh:
        pickle.dump({"model": model, "feature_names": feature_names, "threshold": threshold}, fh)

    write_model_card(asi_dir / "tep_model_card.json", report)
    (asi_dir / "tep_train_log.json").write_text(
        json.dumps(
            {
                "computed_at": report["computed_at"],
                "train_n": len(train_rows),
                "calibrate_n": len(cal_rows),
                "promote_n": len(promote_rows),
                "calibrate_candidates": best.get("calibrate_candidates"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # TEP shadow report (replaces v0 for P3 prep)
    def tep_shadow(rows: list[dict]) -> dict[str, Any] | None:
        if not rows:
            return None
        X, _ = featurize(rows, feature_names)
        p = predict_proba(model, X)
        ev = evaluate_threshold(rows, p, threshold)
        ev["method"] = f"TEP P(steamroller) >= {threshold}"
        return ev

    shadow_report = {
        "schema": "fema_asi_shadow_tep_v1",
        "computed_at": report["computed_at"],
        "model_card": "tep_model_card.json",
        "calibrate": tep_shadow(cal_rows),
        "promote_frozen": tep_shadow(promote_rows),
    }
    (asi_dir / "asi_shadow_tep.json").write_text(
        json.dumps(shadow_report, indent=2), encoding="utf-8"
    )

    return {
        "ok": True,
        "variant": best_name,
        "threshold": threshold,
        "auc_calibrate": best.get("auc_calibrate"),
        "calibrate": best.get("calibrate_eval"),
        "promote_frozen": promote_eval,
        "ablation": report["ablation"],
        "paths": {
            "model": str(model_path),
            "card": str(asi_dir / "tep_model_card.json"),
            "shadow": str(asi_dir / "asi_shadow_tep.json"),
        },
    }


def write_tep_train_report(report: dict[str, Any]) -> str:
    cal = report.get("calibrate") or {}
    prom = report.get("promote_frozen") or {}
    ab = report.get("ablation") or {}
    lines = [
        "# ASI-P2 TEP train report",
        "",
        f"- variant: **{report.get('variant')}**",
        f"- threshold: **{report.get('threshold')}**",
        f"- AUC calibrate: **{report.get('auc_calibrate')}**",
        "",
        "## Calibrate (threshold tuned here)",
        "",
        f"- skip rate: **{cal.get('skip_rate')}**",
        f"- steamroller precision: **{cal.get('steamroller_precision')}**",
        f"- false-skip winners: **{cal.get('false_skip_winners')}**",
        f"- net skipped: **{cal.get('net_skipped')}**",
        "",
        "## Promote frozen (one-shot — not tuned)",
        "",
    ]
    if prom:
        lines.extend(
            [
                f"- skip rate: **{prom.get('skip_rate')}**",
                f"- steamroller precision: **{prom.get('steamroller_precision')}**",
                f"- false-skip winners: **{prom.get('false_skip_winners')}**",
                f"- kept PF: **{prom.get('kept_pf')}** | kept n: **{prom.get('kept_n')}**",
            ]
        )
    else:
        lines.append("- (no promote_frozen split)")
    lines.extend(
        [
            "",
            "## Ablation",
            "",
            f"- TEP beats static: **{ab.get('tep_beats_static')}**",
            f"- TEP beats ADX-only: **{ab.get('tep_beats_adx')}**",
            f"- winner: **{ab.get('winner')}**",
        ]
    )
    return "\n".join(lines) + "\n"
