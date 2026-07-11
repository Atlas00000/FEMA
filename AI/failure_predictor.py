#!/usr/bin/env python3
"""AI2 — Failure predictor (offline, soft-skip, high precision on skips).

Train on 2024–2025; lock threshold on a late-train calibration slice;
evaluate once on 2026 Jan–Jul (AI-G1). Approve by default.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

_AI_DIR = Path(__file__).resolve().parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from regime_atlas import assign_regime, metrics as basket_metrics  # noqa: E402


NUMERIC_FEATURES = [
    "open_level",
    "ema_sep",
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

REGIME_FLAGS = [
    "late_session",
    "asia_open",
    "wide_spread",
    "high_adx",
    "expansion",
    "compression",
    "shallow_pullback",
    "grinding",
    "transition",
]


def f(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def load_dataset(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def atr_percentiles(rows: list[dict]) -> tuple[float, float]:
    atrs = sorted(f(r, "atr") for r in rows if f(r, "atr") > 0)
    if not atrs:
        return 0.0, 1.0
    n = len(atrs)
    return atrs[max(0, n // 4)], atrs[min(n - 1, (3 * n) // 4)]


def featurize(
    rows: list[dict],
    atr_p25: float,
    atr_p75: float,
    use_regime: bool,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    names = list(NUMERIC_FEATURES) + ["is_sell"]
    if use_regime:
        names += [f"reg_{r}" for r in REGIME_FLAGS]
    X, y = [], []
    for row in rows:
        vec = [f(row, c) for c in NUMERIC_FEATURES]
        vec.append(1.0 if str(row.get("direction", "")).upper() == "SELL" else 0.0)
        if use_regime:
            regime = assign_regime(row, atr_p25, atr_p75)
            vec.extend(1.0 if regime == r else 0.0 for r in REGIME_FLAGS)
        X.append(vec)
        y.append(int(float(row.get("y_fail", 0) or 0)))
    return np.asarray(X, dtype=float), np.asarray(y, dtype=int), names


def build_model(kind: str, calibrate: bool = False) -> Pipeline:
    if kind == "gbdt":
        clf = GradientBoostingClassifier(
            n_estimators=60,
            max_depth=1,
            learning_rate=0.05,
            subsample=0.85,
            min_samples_leaf=12,
            random_state=42,
        )
        return Pipeline([("clf", clf)])
    base = LogisticRegression(max_iter=2000, C=0.35, class_weight="balanced", random_state=42)
    clf: object = CalibratedClassifierCV(base, method="sigmoid", cv=3) if calibrate else base
    return Pipeline([("scaler", StandardScaler()), ("clf", clf)])


def equity_metrics(rows: list[dict], skip_ids: set[str], deposit: float = 400.0) -> dict:
    kept = [r for r in rows if str(r.get("basket_id", "")) not in skip_ids]
    m = basket_metrics(kept, deposit=deposit)
    m["skip_n"] = len(rows) - len(kept)
    m["skip_rate"] = round((len(rows) - len(kept)) / len(rows), 4) if rows else 0.0
    return m


def skip_precision(rows: list[dict], skip_ids: set[str]) -> dict:
    skipped = [r for r in rows if str(r.get("basket_id", "")) in skip_ids]
    if not skipped:
        return {
            "n": 0,
            "precision_y_fail": 0.0,
            "precision_loser": 0.0,
            "bsl_rate": 0.0,
            "net_avoided": 0.0,
            "avg_profit": 0.0,
        }
    yf = sum(1 for r in skipped if int(float(r.get("y_fail", 0) or 0)) == 1)
    losers = sum(1 for r in skipped if f(r, "profit") < 0)
    bsl = sum(1 for r in skipped if int(float(r.get("hit_bsl", 0) or 0)) == 1)
    profits = [f(r, "profit") for r in skipped]
    return {
        "n": len(skipped),
        "precision_y_fail": round(yf / len(skipped), 4),
        "precision_loser": round(losers / len(skipped), 4),
        "bsl_rate": round(bsl / len(skipped), 4),
        "net_avoided": round(sum(profits), 2),
        "avg_profit": round(sum(profits) / len(skipped), 4),
    }


def ai_g1(base: dict, cand: dict, min_trade_frac: float = 0.85) -> dict:
    checks = {
        "pf_ge_baseline": cand["pf"] + 1e-12 >= float(base["pf"]),
        "dd_le_baseline": cand["max_dd_pct"] <= float(base["max_dd_pct"]) + 1e-9,
        "trades_ge_85pct": cand["n"] >= int(math.ceil(float(base["n"]) * min_trade_frac)),
        "wr_ge_baseline": cand["wr"] + 1e-12 >= float(base["wr"]),
    }
    checks["ai_g1_pass"] = (
        checks["pf_ge_baseline"] and checks["dd_le_baseline"] and checks["trades_ge_85pct"]
    )
    return checks


def evaluate_threshold(rows: list[dict], p_fail: np.ndarray, thr: float, deposit: float) -> dict:
    ids = [str(r.get("basket_id", "")) for r in rows]
    skip_ids = {ids[i] for i, p in enumerate(p_fail) if p >= thr}
    if len(skip_ids) != sum(1 for p in p_fail if p >= thr):
        raise RuntimeError(
            "basket_id collision — run AI/repair_basket_ids.py before AI2."
        )
    kept = equity_metrics(rows, skip_ids, deposit)
    skip = skip_precision(rows, skip_ids)
    return {
        "threshold": round(float(thr), 6),
        "skip_rate": kept["skip_rate"],
        "skip_n": kept["skip_n"],
        "kept": kept,
        "skip": skip,
        "skip_ids": sorted(skip_ids, key=lambda x: int(x) if x.isdigit() else x),
    }


def select_policy_on_cal(
    rows: list[dict],
    p_fail: np.ndarray,
    max_skip: float,
    min_skip: float,
    deposit: float,
) -> tuple[dict, list[dict]]:
    """Lock a skip *quantile* on calibration (rank policy), not a brittle absolute P cutoff."""
    targets = [0.05, 0.08, 0.10, 0.12, 0.15]
    candidates = []
    for t in targets:
        if t < min_skip - 1e-12 or t > max_skip + 1e-12:
            continue
        thr = float(np.quantile(p_fail, 1.0 - t))
        ev = evaluate_threshold(rows, p_fail, thr, deposit)
        if ev["skip_n"] == 0:
            continue
        score = (
            100.0 * ev["skip"]["precision_y_fail"]
            + 40.0 * ev["skip"]["precision_loser"]
            + (25.0 if ev["skip"]["net_avoided"] < 0 else -40.0)
            - 3.0 * abs(ev["skip_rate"] - 0.10)
        )
        ev["score"] = round(score, 4)
        ev["skip_quantile"] = t
        candidates.append(ev)
    if not candidates:
        raise RuntimeError("no calibration policies in skip budget")
    candidates.sort(key=lambda d: d["score"], reverse=True)
    return candidates[0], candidates


def evaluate_quantile(
    rows: list[dict], p_fail: np.ndarray, skip_quantile: float, deposit: float
) -> dict:
    """Skip the top skip_quantile fraction by P(fail) (rank policy)."""
    thr = float(np.quantile(p_fail, 1.0 - skip_quantile))
    ev = evaluate_threshold(rows, p_fail, thr, deposit)
    ev["skip_quantile"] = skip_quantile
    return ev


def feature_importance(model: Pipeline, names: list[str], kind: str) -> list[dict]:
    try:
        if kind == "gbdt":
            coef = model.named_steps["clf"].feature_importances_
        else:
            clf = model.named_steps["clf"]
            coefs = []
            if hasattr(clf, "calibrated_classifiers_"):
                for c in clf.calibrated_classifiers_:
                    est = getattr(c, "estimator", None) or getattr(c, "base_estimator", None)
                    if est is not None and hasattr(est, "coef_"):
                        coefs.append(est.coef_.ravel())
            if not coefs and hasattr(clf, "coef_"):
                coefs = [clf.coef_.ravel()]
            if not coefs:
                return []
            coef = np.mean(np.vstack(coefs), axis=0)
        order = np.argsort(np.abs(coef))[::-1]
        return [{"feature": names[i], "weight": round(float(coef[i]), 4)} for i in order[:12]]
    except Exception:
        return []


def write_md(path: Path, report: dict) -> None:
    best = report["validate_eval"]
    status = report["status"]
    lines = [
        "# AI2 — Failure predictor report",
        "",
        f"**Status:** `{status}`",
        f"**Model:** `{report['model']}` · **Locked skip quantile (train-cal):** top **{report['locked_skip_quantile']:.0%}** by P(fail)",
        f"**Skip rate (validate):** {best['skip_rate']:.1%} ({best['skip_n']} baskets)",
        f"**AI-G1:** {'PASS' if best['ai_g1']['ai_g1_pass'] else 'FAIL'}",
        f"**Skip-precision gate:** {'PASS' if report['skip_precision_pass'] else 'FAIL'}",
        f"**AUC train / validate:** {report['auc_train']:.3f} / {report['auc_validate']:.3f}",
        "",
        "## Validate 2026 Jan–Jul (single eval)",
        "",
        "| Slice | N | PF | Net | DD% | WR | BSL% |",
        "| ----- | - | -- | --- | --- | -- | ---- |",
    ]
    b = report["validate_baseline"]
    k = best["kept"]
    s = best["skip"]
    lines.append(
        f"| Baseline (all) | {b['n']} | {b['pf']:.2f} | {b['net']:+.1f} | {b['max_dd_pct']:.1f} | {b['wr']:.2%} | {b['bsl_rate']:.1%} |"
    )
    lines.append(
        f"| After soft-skip | {k['n']} | {k['pf']:.2f} | {k['net']:+.1f} | {k['max_dd_pct']:.1f} | {k['wr']:.2%} | {k['bsl_rate']:.1%} |"
    )
    lines += [
        "",
        "## Skip quality (precision-first)",
        "",
        f"- Skip precision `y_fail`: **{s['precision_y_fail']:.1%}**",
        f"- Skip precision loser (profit<0): **{s['precision_loser']:.1%}**",
        f"- Skip BSL rate: **{s['bsl_rate']:.1%}**",
        f"- Net PnL of skipped set: **{s['net_avoided']:+.2f}** (negative = good avoidance)",
        "",
        "## Threshold lock (late-train calibration)",
        "",
    ]
    cal = report["cal_selected"]
    lines.append(
        f"Cal slice n={report['cal_n']}: skip {cal['skip_rate']:.1%}, "
        f"y_fail prec {cal['skip']['precision_y_fail']:.1%}, "
        f"loser prec {cal['skip']['precision_loser']:.1%}, "
        f"net_avoided {cal['skip']['net_avoided']:+.2f}"
    )
    lines += ["", "## Top features", ""]
    for row in report.get("feature_importance", [])[:8]:
        lines.append(f"- `{row['feature']}`: {row['weight']}")
    lines += [
        "",
        "## Policy",
        "",
        "Shadow only. Wire only if status is `promote_candidate` (AI-G1 + majority-fail skips).",
        "Approve by default; skip only when P(fail) ≥ locked threshold.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="AI2 failure predictor")
    ap.add_argument("--train", type=Path, default=Path("AI/data/dataset_train_2024_2025.csv"))
    ap.add_argument("--validate", type=Path, default=Path("AI/data/dataset_validate_2026.csv"))
    ap.add_argument("--model", choices=("logistic", "gbdt"), default="gbdt")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--use-regime", action="store_true", help="Include AI1 regime one-hots")
    ap.add_argument("--cal-frac", type=float, default=0.25, help="Late-train fraction for threshold lock")
    ap.add_argument("--max-skip", type=float, default=0.15)
    ap.add_argument("--min-skip", type=float, default=0.05)
    ap.add_argument("--deposit", type=float, default=400.0)
    ap.add_argument("--out-dir", type=Path, default=Path("AI/data"))
    args = ap.parse_args()

    train_rows = load_dataset(args.train)
    val_rows = load_dataset(args.validate)
    if not train_rows or not val_rows:
        print("ERROR: empty train/validate", file=sys.stderr)
        return 1

    all_ids = [str(r.get("basket_id", "")) for r in train_rows + val_rows]
    if len(set(all_ids)) < len(all_ids):
        print(
            "ERROR: basket_id not unique. Run: python AI/repair_basket_ids.py",
            file=sys.stderr,
        )
        return 1

    # Time-ordered train is already chronological; late slice = threshold cal
    split = max(1, int(len(train_rows) * (1.0 - args.cal_frac)))
    fit_rows = train_rows[:split]
    cal_rows = train_rows[split:]
    if len(cal_rows) < 20:
        print("ERROR: calibration slice too small", file=sys.stderr)
        return 1

    atr_p25, atr_p75 = atr_percentiles(fit_rows)
    X_fit, y_fit, names = featurize(fit_rows, atr_p25, atr_p75, args.use_regime)
    X_cal, _, _ = featurize(cal_rows, atr_p25, atr_p75, args.use_regime)
    X_tr, y_tr, _ = featurize(train_rows, atr_p25, atr_p75, args.use_regime)
    X_va, y_va, _ = featurize(val_rows, atr_p25, atr_p75, args.use_regime)

    # 1) Fit on early train → lock skip quantile on late train
    model_cal = build_model(args.model, calibrate=args.calibrate)
    model_cal.fit(X_fit, y_fit)
    p_cal = model_cal.predict_proba(X_cal)[:, 1]
    cal_selected, cal_candidates = select_policy_on_cal(
        cal_rows, p_cal, args.max_skip, args.min_skip, args.deposit
    )
    skip_q = float(cal_selected["skip_quantile"])

    # 2) Refit on full train; freeze quantile; single validate eval
    model = build_model(args.model, calibrate=args.calibrate)
    model.fit(X_tr, y_tr)
    p_tr = model.predict_proba(X_tr)[:, 1]
    p_va = model.predict_proba(X_va)[:, 1]

    train_base = basket_metrics(train_rows, deposit=args.deposit)
    val_base = basket_metrics(val_rows, deposit=args.deposit)
    train_eval = evaluate_quantile(train_rows, p_tr, skip_q, args.deposit)
    val_eval = evaluate_quantile(val_rows, p_va, skip_q, args.deposit)
    val_eval["ai_g1"] = ai_g1(val_base, val_eval["kept"])

    auc_train = float(roc_auc_score(y_tr, p_tr)) if len(set(y_tr)) > 1 else 0.0
    auc_val = float(roc_auc_score(y_va, p_va)) if len(set(y_va)) > 1 else 0.0

    skip_prec_pass = (
        val_eval["skip"]["precision_y_fail"] >= 0.50
        or val_eval["skip"]["precision_loser"] >= 0.50
    ) and val_eval["skip"]["net_avoided"] <= 0.0
    rank_ok = auc_val >= 0.55 and val_eval["skip_n"] >= 8
    if val_eval["ai_g1"]["ai_g1_pass"] and skip_prec_pass and rank_ok:
        status = "promote_candidate"
    elif val_eval["ai_g1"]["ai_g1_pass"] and skip_prec_pass:
        status = "fragile_shadow_g1_thin_sample"
    elif val_eval["ai_g1"]["ai_g1_pass"]:
        status = "shadow_watch_g1_pass_weak_precision"
    elif skip_prec_pass:
        status = "shadow_precision_ok_g1_fail"
    else:
        status = "reject_shadow"

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    skip_set = set(val_eval["skip_ids"])
    shadow_path = out_dir / "ai2_shadow.csv"
    with shadow_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "basket_id",
                "open_time",
                "p_fail",
                "would_skip",
                "y_fail",
                "hit_bsl",
                "profit",
                "regime",
            ],
        )
        w.writeheader()
        for row, p in zip(val_rows, p_va):
            bid = str(row.get("basket_id", ""))
            w.writerow(
                {
                    "basket_id": bid,
                    "open_time": row.get("open_time", ""),
                    "p_fail": f"{p:.6f}",
                    "would_skip": 1 if bid in skip_set else 0,
                    "y_fail": row.get("y_fail", ""),
                    "hit_bsl": row.get("hit_bsl", ""),
                    "profit": row.get("profit", ""),
                    "regime": assign_regime(row, atr_p25, atr_p75),
                }
            )

    skip_path = out_dir / "ai2_skip_ids.txt"
    skip_path.write_text(
        "\n".join(val_eval["skip_ids"]) + ("\n" if val_eval["skip_ids"] else ""),
        encoding="utf-8",
    )

    report = {
        "phase": "AI2-FAIL",
        "status": status,
        "model": args.model,
        "calibrate": bool(args.calibrate),
        "use_regime": bool(args.use_regime),
        "train_path": str(args.train).replace("\\", "/"),
        "validate_path": str(args.validate).replace("\\", "/"),
        "fit_n": len(fit_rows),
        "cal_n": len(cal_rows),
        "train_n": len(train_rows),
        "validate_n": len(val_rows),
        "train_y_fail_rate": round(float(y_tr.mean()), 4),
        "validate_y_fail_rate": round(float(y_va.mean()), 4),
        "auc_train": round(auc_train, 4),
        "auc_validate": round(auc_val, 4),
        "locked_skip_quantile": skip_q,
        "locked_threshold_on_validate": val_eval["threshold"],
        "max_skip": args.max_skip,
        "min_skip": args.min_skip,
        "train_baseline": train_base,
        "validate_baseline": val_base,
        "cal_selected": {k: v for k, v in cal_selected.items() if k != "skip_ids"},
        "cal_candidates": [
            {k: v for k, v in c.items() if k != "skip_ids"} for c in cal_candidates
        ],
        "train_at_locked": {k: v for k, v in train_eval.items() if k != "skip_ids"},
        "validate_eval": val_eval,
        "skip_precision_pass": skip_prec_pass,
        "feature_importance": feature_importance(model, names, args.model),
        "artifacts": {
            "skip_ids": str(skip_path).replace("\\", "/"),
            "shadow": str(shadow_path).replace("\\", "/"),
        },
        "note": (
            "Skip quantile locked on late-train calibration; validate is a single holdout eval. "
            "promote_candidate requires AI-G1 + majority-fail skips with net_avoided<=0."
        ),
    }

    json_path = out_dir / "ai2_report.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path = out_dir / "ai2_report.md"
    write_md(md_path, report)

    print(
        f"AI2 {args.model} | status={status} | skip_q={skip_q:.0%} | "
        f"skip={val_eval['skip_rate']:.1%} ({val_eval['skip_n']}) | "
        f"prec_yfail={val_eval['skip']['precision_y_fail']:.1%} | "
        f"prec_loser={val_eval['skip']['precision_loser']:.1%} | "
        f"net_avoided={val_eval['skip']['net_avoided']:+.1f} | "
        f"auc={auc_val:.3f} | "
        f"val PF {val_base['pf']:.2f}->{val_eval['kept']['pf']:.2f} | "
        f"DD {val_base['max_dd_pct']:.1f}->{val_eval['kept']['max_dd_pct']:.1f} | "
        f"AI-G1={'PASS' if val_eval['ai_g1']['ai_g1_pass'] else 'FAIL'}"
    )
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    print(f"wrote {skip_path}")
    print(f"wrote {shadow_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
