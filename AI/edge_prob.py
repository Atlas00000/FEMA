#!/usr/bin/env python3
"""AI4 — Edge probability / confidence (offline, permissive).

Predict P(hit TP / winner path) at basket open.
Low P(TP) alone must NOT skip — only logging, or mild assist when AI2 also flags.
Train 2024–2025; single eval on 2026 validate.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

_AI_DIR = Path(__file__).resolve().parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from failure_predictor import (  # noqa: E402
    NUMERIC_FEATURES,
    atr_percentiles,
    featurize as _featurize_fail,
)
from regime_atlas import assign_regime, metrics as basket_metrics  # noqa: E402


def f(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def load_dataset(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def featurize(rows, atr_p25, atr_p75, use_regime: bool = False):
    # reuse AI2 feature builder (y_fail label ignored — we rebuild y_tp)
    X, _, names = _featurize_fail(rows, atr_p25, atr_p75, use_regime)
    y_tp = np.asarray(
        [
            1
            if int(float(r.get("hit_tp", 0) or 0)) == 1
            or (int(float(r.get("hit_tp", 0) or 0)) == 0 and f(r, "profit") > 0)
            else 0
            for r in rows
        ],
        dtype=int,
    )
    # Prefer explicit hit_tp when present; fallback profit>0 already in above.
    # Tighten: primary label = hit_tp if column used; else profit>0
    y_hit = np.asarray([int(float(r.get("hit_tp", 0) or 0)) for r in rows], dtype=int)
    if y_hit.sum() > 0:
        y_tp = y_hit
    return X, y_tp, names


def build_model(kind: str) -> Pipeline:
    if kind == "gbdt":
        return Pipeline(
            [
                (
                    "clf",
                    GradientBoostingClassifier(
                        n_estimators=60,
                        max_depth=1,
                        learning_rate=0.05,
                        subsample=0.85,
                        min_samples_leaf=12,
                        random_state=42,
                    ),
                )
            ]
        )
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000, C=0.35, class_weight="balanced", random_state=42
                ),
            ),
        ]
    )


def equity_metrics(rows: list[dict], skip_ids: set[str], deposit: float = 400.0) -> dict:
    kept = [r for r in rows if str(r.get("basket_id", "")) not in skip_ids]
    m = basket_metrics(kept, deposit=deposit)
    m["skip_n"] = len(rows) - len(kept)
    m["skip_rate"] = round((len(rows) - len(kept)) / len(rows), 4) if rows else 0.0
    return m


def skip_quality(rows: list[dict], skip_ids: set[str]) -> dict:
    skipped = [r for r in rows if str(r.get("basket_id", "")) in skip_ids]
    if not skipped:
        return {
            "n": 0,
            "precision_not_tp": 0.0,
            "precision_loser": 0.0,
            "precision_y_fail": 0.0,
            "net_avoided": 0.0,
        }
    not_tp = sum(1 for r in skipped if int(float(r.get("hit_tp", 0) or 0)) == 0)
    losers = sum(1 for r in skipped if f(r, "profit") < 0)
    yf = sum(1 for r in skipped if int(float(r.get("y_fail", 0) or 0)) == 1)
    profits = [f(r, "profit") for r in skipped]
    return {
        "n": len(skipped),
        "precision_not_tp": round(not_tp / len(skipped), 4),
        "precision_loser": round(losers / len(skipped), 4),
        "precision_y_fail": round(yf / len(skipped), 4),
        "net_avoided": round(sum(profits), 2),
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


def load_ai2_skip_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        return set()
    return {line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")}


def load_ai2_shadow(path: Path) -> dict[str, float]:
    """basket_id -> p_fail from AI2 shadow if present."""
    if not path.exists():
        return {}
    out = {}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            out[str(row.get("basket_id", ""))] = float(row.get("p_fail", 0) or 0)
    return out


def bottom_quantile_ids(rows: list[dict], scores: np.ndarray, q: float) -> set[str]:
    """IDs in the bottom q fraction by score (low P(TP))."""
    if len(rows) == 0 or q <= 0:
        return set()
    thr = float(np.quantile(scores, q))
    ids = [str(r.get("basket_id", "")) for r in rows]
    return {ids[i] for i, s in enumerate(scores) if s <= thr}


def feature_importance(model: Pipeline, names: list[str], kind: str) -> list[dict]:
    try:
        if kind == "gbdt":
            coef = model.named_steps["clf"].feature_importances_
        else:
            coef = model.named_steps["clf"].coef_.ravel()
        order = np.argsort(np.abs(coef))[::-1]
        return [{"feature": names[i], "weight": round(float(coef[i]), 4)} for i in order[:12]]
    except Exception:
        return []


def write_md(path: Path, report: dict) -> None:
    lines = [
        "# AI4 — Edge probability / confidence report",
        "",
        f"**Status:** `{report['status']}`",
        f"**Model:** `{report['model']}` · label=`hit_tp`",
        f"**AUC train / validate:** {report['auc_train']:.3f} / {report['auc_validate']:.3f}",
        "",
        "## Policy",
        "",
        "Low P(TP) alone does **not** skip (no elite-only mode).",
        "Use as logging / tie-break with AI2.",
        "",
        "## Ablations on 2026 validate",
        "",
        "| Policy | Skip% | PF | DD% | Net | AI-G1 | Skip loser% |",
        "| ------ | ----- | -- | --- | --- | ----- | ----------- |",
    ]
    for name, abl in report["ablations"].items():
        g1 = "PASS" if abl["ai_g1"]["ai_g1_pass"] else "FAIL"
        lines.append(
            f"| {name} | {abl['skip_rate']:.1%} | {abl['kept']['pf']:.2f} | "
            f"{abl['kept']['max_dd_pct']:.1f} | {abl['kept']['net']:+.1f} | {g1} | "
            f"{abl['skip']['precision_loser']:.0%} |"
        )
    lines += [
        "",
        "## Top features",
        "",
    ]
    for row in report.get("feature_importance", [])[:8]:
        lines.append(f"- `{row['feature']}`: {row['weight']}")
    lines += [
        "",
        "Shadow / logging only unless status is `soft_assist`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="AI4 edge probability")
    ap.add_argument("--train", type=Path, default=Path("AI/data/dataset_train_2024_2025.csv"))
    ap.add_argument("--validate", type=Path, default=Path("AI/data/dataset_validate_2026.csv"))
    ap.add_argument("--model", choices=("logistic", "gbdt"), default="gbdt")
    ap.add_argument("--use-regime", action="store_true")
    ap.add_argument("--ai2-skip", type=Path, default=Path("AI/data/ai2_skip_ids.txt"))
    ap.add_argument("--ai2-shadow", type=Path, default=Path("AI/data/ai2_shadow.csv"))
    ap.add_argument("--low-ptp-q", type=float, default=0.10, help="Bottom quantile = low confidence")
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
        print("ERROR: basket_id not unique — run AI/repair_basket_ids.py", file=sys.stderr)
        return 1

    atr_p25, atr_p75 = atr_percentiles(train_rows)
    X_tr, y_tr, names = featurize(train_rows, atr_p25, atr_p75, args.use_regime)
    X_va, y_va, _ = featurize(val_rows, atr_p25, atr_p75, args.use_regime)

    model = build_model(args.model)
    model.fit(X_tr, y_tr)
    p_tr = model.predict_proba(X_tr)[:, 1]
    p_va = model.predict_proba(X_va)[:, 1]

    auc_tr = float(roc_auc_score(y_tr, p_tr)) if len(set(y_tr)) > 1 else 0.0
    auc_va = float(roc_auc_score(y_va, p_va)) if len(set(y_va)) > 1 else 0.0

    val_base = basket_metrics(val_rows, deposit=args.deposit)
    ai2_ids = load_ai2_skip_ids(args.ai2_skip)
    # If AI2 skip file empty, rebuild mild AI2-like fail quantile from shadow p_fail
    p_fail_map = load_ai2_shadow(args.ai2_shadow)
    if not ai2_ids and p_fail_map:
        fails = np.asarray([p_fail_map.get(str(r.get("basket_id", "")), 0.0) for r in val_rows])
        ai2_ids = {
            str(r.get("basket_id", ""))
            for r, p in zip(val_rows, fails)
            if p >= float(np.quantile(fails, 0.95))
        }

    low_ptp = bottom_quantile_ids(val_rows, p_va, args.low_ptp_q)
    # Elite-only (FORBIDDEN as promote): skip bottom p_tp alone
    ai4_only = low_ptp
    # Soft assist: intersection AI2 flag AND low P(TP)
    ai2_and_low = ai2_ids & low_ptp
    # Mild: AI2 skips, but drop skip if P(TP) is high (top 50%) — keep AI2 only when not confident winner
    p_tp_map = {str(r.get("basket_id", "")): float(p) for r, p in zip(val_rows, p_va)}
    med_ptp = float(np.median(p_va))
    ai2_confirmed = {i for i in ai2_ids if p_tp_map.get(i, 1.0) <= med_ptp}

    def pack(skip_ids: set[str], label: str) -> dict:
        kept = equity_metrics(val_rows, skip_ids, args.deposit)
        skip = skip_quality(val_rows, skip_ids)
        return {
            "label": label,
            "skip_n": len(skip_ids),
            "skip_rate": round(len(skip_ids) / len(val_rows), 4),
            "kept": kept,
            "skip": skip,
            "ai_g1": ai_g1(val_base, kept),
            "skip_ids": sorted(skip_ids, key=lambda x: int(x) if x.isdigit() else x),
        }

    ablations = {
        "baseline_no_skip": pack(set(), "approve all"),
        "ai4_low_ptp_only": pack(ai4_only, "FORBIDDEN elite-style (logging compare)"),
        "ai2_only": pack(ai2_ids, "AI2 skip list"),
        "ai2_and_low_ptp": pack(ai2_and_low, "AI2 ∩ low P(TP)"),
        "ai2_unless_high_ptp": pack(ai2_confirmed, "AI2 but waive if P(TP)>median"),
    }

    # Status: soft_assist if intersection or confirmed beats AI2-only on G1+precision without starving
    base_ai2 = ablations["ai2_only"]
    assist = ablations["ai2_and_low_ptp"]
    confirmed = ablations["ai2_unless_high_ptp"]
    ai4_only_abl = ablations["ai4_low_ptp_only"]

    def better_than_ai2(cand: dict) -> bool:
        if not cand["ai_g1"]["ai_g1_pass"]:
            return False
        if cand["skip_n"] < 3:
            return False
        # Prefer higher skip precision or better DD/PF than AI2-only
        prec_lift = cand["skip"]["precision_loser"] >= max(
            0.45, base_ai2["skip"]["precision_loser"] - 1e-9
        )
        metric_lift = (
            cand["kept"]["pf"] >= base_ai2["kept"]["pf"] - 1e-9
            and cand["kept"]["max_dd_pct"] <= base_ai2["kept"]["max_dd_pct"] + 1e-9
        )
        return prec_lift and metric_lift and cand["skip"]["net_avoided"] <= 0

    if auc_va < 0.52:
        status = "logging_only_weak_rank"
    elif better_than_ai2(assist) or better_than_ai2(confirmed):
        status = "soft_assist"
    elif ai4_only_abl["ai_g1"]["ai_g1_pass"] and ai4_only_abl["skip"]["precision_loser"] >= 0.5:
        # still not promote — policy forbids AI4-only skip
        status = "logging_only_g1_ok_but_no_solo_skip"
    else:
        status = "logging_only"

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    shadow_path = out_dir / "ai4_shadow.csv"
    with shadow_path.open("w", newline="", encoding="utf-8") as fh:
        fields = [
            "basket_id",
            "open_time",
            "p_tp",
            "low_ptp",
            "ai2_flag",
            "hit_tp",
            "y_fail",
            "profit",
            "regime",
        ]
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row, p in zip(val_rows, p_va):
            bid = str(row.get("basket_id", ""))
            w.writerow(
                {
                    "basket_id": bid,
                    "open_time": row.get("open_time", ""),
                    "p_tp": f"{p:.6f}",
                    "low_ptp": 1 if bid in low_ptp else 0,
                    "ai2_flag": 1 if bid in ai2_ids else 0,
                    "hit_tp": row.get("hit_tp", ""),
                    "y_fail": row.get("y_fail", ""),
                    "profit": row.get("profit", ""),
                    "regime": assign_regime(row, atr_p25, atr_p75),
                }
            )

    # Persist assist skip ids for AI5 (intersection — most conservative)
    assist_path = out_dir / "ai4_assist_skip_ids.txt"
    assist_ids = assist["skip_ids"] if status == "soft_assist" else confirmed["skip_ids"]
    if status != "soft_assist":
        assist_ids = []  # do not emit operational skips unless soft_assist
    assist_path.write_text(
        "\n".join(assist_ids) + ("\n" if assist_ids else ""), encoding="utf-8"
    )

    report = {
        "phase": "AI4-PROB",
        "status": status,
        "model": args.model,
        "use_regime": bool(args.use_regime),
        "label": "hit_tp",
        "low_ptp_quantile": args.low_ptp_q,
        "train_n": len(train_rows),
        "validate_n": len(val_rows),
        "train_tp_rate": round(float(y_tr.mean()), 4),
        "validate_tp_rate": round(float(y_va.mean()), 4),
        "auc_train": round(auc_tr, 4),
        "auc_validate": round(auc_va, 4),
        "validate_baseline": val_base,
        "ai2_skip_n": len(ai2_ids),
        "ablations": {
            k: {kk: vv for kk, vv in v.items() if kk != "skip_ids"}
            for k, v in ablations.items()
        },
        "feature_importance": feature_importance(model, names, args.model),
        "artifacts": {
            "shadow": str(shadow_path).replace("\\", "/"),
            "assist_skip_ids": str(assist_path).replace("\\", "/"),
        },
        "note": (
            "AI4 is permissive: never promote AI4-only skips. "
            "soft_assist only if AI2∩low-P(TP) (or AI2 waived-when-high-P(TP)) improves skip quality under AI-G1."
        ),
    }

    json_path = out_dir / "ai4_report.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path = out_dir / "ai4_report.md"
    write_md(md_path, report)

    print(
        f"AI4 {args.model} | status={status} | "
        f"auc={auc_tr:.3f}/{auc_va:.3f} | "
        f"ai2_n={len(ai2_ids)} | low_ptp_n={len(low_ptp)} | "
        f"intersect_n={len(ai2_and_low)} | "
        f"ai4_only G1={'PASS' if ai4_only_abl['ai_g1']['ai_g1_pass'] else 'FAIL'} | "
        f"assist G1={'PASS' if assist['ai_g1']['ai_g1_pass'] else 'FAIL'}"
    )
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    print(f"wrote {shadow_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
