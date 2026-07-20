"""ASI-P6 — basket recovery probability (offline).

P(recover | open features, warn_depth) at depth milestones.
Complementary to ASI-P5 mid-steamroller warn: recovery scores whether a stressed
basket is still likely to finish TP/profit.
"""

from __future__ import annotations

import csv
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from csv_util import read_csv_rows
from fema_ops.asi.dataset import resolve_splits
from fema_ops.asi.features import OPEN_COLS, parse_open_time
from fema_ops.asi.labels import classify_basket
from fema_ops.asi.midbasket import MID_STATIC, mid_checkpoints
from fema_ops.asi.tep import safe_auc

# Same anti-leakage feature set as mid-warn (no mae/mfe/profit)
REC_STATIC = list(MID_STATIC)

DATASET_FIELDS = (
    ["basket_id", "open_time", "symbol", "direction", "warn_depth", "max_depth"]
    + [c for c in REC_STATIC if c not in ("warn_depth", "is_sell")]
    + [
        "is_sell",
        "profit",
        "hit_bsl",
        "hit_tp",
        "mae",
        "mfe",
        "bars_alive",
        "label_class",
        "y_steamroller",
        "y_recover",
    ]
)


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


def _i(row: dict, key: str, default: int = 0) -> int:
    try:
        return int(float(row.get(key, default) or default))
    except (TypeError, ValueError):
        return default


def recover_label(row: dict) -> int:
    """1 = basket eventually recovers (TP or profit>0); 0 = fails to recover."""
    if _i(row, "hit_tp") == 1 or _f(row, "profit") > 0:
        return 1
    return 0


def expand_rec_rows(
    labeled_open: list[dict],
    *,
    min_depth: int = 2,
    max_warn: int = 5,
) -> list[dict[str, Any]]:
    """One row per (basket, warn_depth); label eventual recovery."""
    out: list[dict[str, Any]] = []
    for row in labeled_open:
        max_depth = int(float(row.get("max_depth", 0) or 0))
        lab = classify_basket(row)
        y_rec = recover_label(row)
        for d in mid_checkpoints(max_depth, min_depth=min_depth, max_warn=max_warn):
            mid = {c: row.get(c, "") for c in OPEN_COLS}
            mid.update(
                {
                    k: row.get(k, "")
                    for k in ("profit", "hit_bsl", "hit_tp", "mae", "mfe", "bars_alive", "max_depth")
                }
            )
            mid["warn_depth"] = d
            mid["is_sell"] = 1.0 if str(row.get("direction", "")).upper() == "SELL" else 0.0
            mid["label_class"] = lab["label_class"]
            mid["y_steamroller"] = int(lab["y_steamroller"])
            mid["y_recover"] = y_rec
            for k in (
                "ema_slope_accel",
                "adx_accel",
                "atr_expansion_rate",
                "consecutive_same_dir",
                "dist_ema_abs",
                "impulse_score",
            ):
                mid[k] = row.get(k, 0)
            out.append(mid)
    return out


def featurize_rec(rows: list[dict], feature_names: list[str] | None = None) -> tuple[np.ndarray, np.ndarray]:
    names = list(feature_names or REC_STATIC)
    X, y = [], []
    for row in rows:
        vec = []
        for c in names:
            if c == "is_sell":
                vec.append(
                    1.0
                    if (row.get("is_sell") in (1, 1.0, "1") or str(row.get("direction", "")).upper() == "SELL")
                    else 0.0
                )
            else:
                vec.append(_f(row, c))
        X.append(vec)
        y.append(int(float(row.get("y_recover", 0) or 0)))
    return np.asarray(X, dtype=float), np.asarray(y, dtype=int)


def write_rec_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=DATASET_FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in DATASET_FIELDS})


def build_rec_dataset(
    *,
    baskets_path: Path,
    out_dir: Path,
    split_profile: str = "long",
    min_depth: int = 2,
    max_warn: int = 5,
) -> dict[str, Any]:
    from fema_ops.asi.dataset import merge_labeled_rows

    raw = read_csv_rows(baskets_path)
    labeled = merge_labeled_rows(raw)
    rec_rows = expand_rec_rows(labeled, min_depth=min_depth, max_warn=max_warn)

    splits = resolve_splits(split_profile)
    buckets = {"train": [], "calibrate": [], "promote_frozen": [], "other": []}
    for row in rec_rows:
        ot = str(row.get("open_time", ""))
        placed = False
        for name in ("train", "calibrate", "promote_frozen"):
            sp = splits[name]
            lo = parse_open_time(f"{sp['start']} 00:00:00")
            hi = parse_open_time(f"{sp['end']} 23:59:59")
            t = parse_open_time(ot)
            if lo <= t <= hi:
                buckets[name].append(row)
                placed = True
                break
        if not placed:
            buckets["other"].append(row)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_rec_csv(out_dir / "rec_dataset_full.csv", rec_rows)
    for name, part in buckets.items():
        if part:
            write_rec_csv(out_dir / f"rec_dataset_{name}.csv", part)

    n_rec = sum(int(r.get("y_recover", 0)) for r in rec_rows)
    report = {
        "schema": "fema_asi_rec_build_v1",
        "computed_at": _utc_now(),
        "phase": "ASI-P6",
        "source_baskets": str(baskets_path).replace("\\", "/"),
        "split_profile": splits.get("profile", split_profile),
        "min_depth": min_depth,
        "max_warn": max_warn,
        "n_baskets": len(labeled),
        "n_rec_rows": len(rec_rows),
        "y_recover_rate": round(n_rec / len(rec_rows), 4) if rec_rows else 0.0,
        "counts": {k: len(v) for k, v in buckets.items()},
        "feature_names": REC_STATIC,
        "leakage_rule": "warn_depth known when level fills; no mae/mfe/profit as features",
        "label": "y_recover = hit_tp or profit>0",
    }
    (out_dir / "rec_splits.json").write_text(json.dumps({**splits, **report}, indent=2), encoding="utf-8")
    (out_dir / "rec_build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def train_rec(
    *,
    asi_dir: Path,
    max_exit_rate: float = 0.15,
) -> dict[str, Any]:
    """Train P(recover | open, warn_depth); calibrate low-P exit recommend band."""
    asi_dir = Path(asi_dir)
    train_rows = read_csv_rows(asi_dir / "rec_dataset_train.csv")
    cal_rows = read_csv_rows(asi_dir / "rec_dataset_calibrate.csv")
    if not train_rows or not cal_rows:
        raise FileNotFoundError("Run asi-rec-build first")

    names = list(REC_STATIC)
    X_tr, y_tr = featurize_rec(train_rows, names)
    X_cal, y_cal = featurize_rec(cal_rows, names)
    model = Pipeline(
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
    model.fit(X_tr, y_tr)
    p_cal = model.predict_proba(X_cal)[:, 1]

    # Low recovery → recommend early exit (complement of keep)
    candidates = []
    for t in (0.05, 0.08, 0.10, 0.12, 0.15):
        if t > max_exit_rate + 1e-9:
            continue
        thr = float(np.quantile(p_cal, t))  # bottom mass = low recover
        mask = p_cal <= thr
        exit_n = int(mask.sum())
        if exit_n == 0:
            continue
        # among exit recommends: how many truly failed to recover?
        true_fail = int(((y_cal == 0) & mask).sum())
        false_cut = 0  # would have recovered (false early exit)
        for row, s in zip(cal_rows, mask):
            if s and int(row.get("y_recover", 0)) == 1:
                false_cut += 1
        prec_fail = true_fail / exit_n
        net = sum(_f(r, "profit") for r, s in zip(cal_rows, mask) if s)
        # Prefer cutting true non-recoveries; reward negative net of cut set
        score = 80.0 * prec_fail - 5.0 * false_cut + (20.0 if net <= 0 else -20.0)
        candidates.append(
            {
                "exit_threshold": round(thr, 6),
                "exit_rate": round(exit_n / len(cal_rows), 4),
                "exit_n": exit_n,
                "fail_precision": round(prec_fail, 4),
                "false_cut_recoveries": false_cut,
                "true_non_recoveries": true_fail,
                "net_of_exit_set": round(net, 2),
                "score": round(score, 4),
            }
        )
    candidates.sort(key=lambda d: d["score"], reverse=True)
    best = candidates[0] if candidates else {"exit_threshold": 0.0, "exit_n": 0, "fail_precision": 0.0}

    thr = float(best.get("exit_threshold", 0.0))
    keep_thr = 0.55  # advisory keep band (document only)
    card = {
        "schema": "fema_asi_rec_model_card_v1",
        "computed_at": _utc_now(),
        "phase": "ASI-P6",
        "label": "y_recover",
        "model_kind": "logistic_regression",
        "feature_names": names,
        "exit_threshold": thr,
        "keep_threshold_advisory": keep_thr,
        "max_exit_rate": max_exit_rate,
        "auc_train": safe_auc(y_tr, model.predict_proba(X_tr)[:, 1]),
        "auc_calibrate": safe_auc(y_cal, p_cal),
        "calibrate_eval": best,
        "calibrate_candidates": candidates,
        "policy": "shadow_recommend_only",
        "action_map": {
            "keep": f"P(recover) >= {keep_thr} → KEEP (advisory)",
            "caution": f"{thr} < P(recover) < {keep_thr} → CAUTION / stop-adds (not wired)",
            "early_bsl": f"P(recover) <= {thr} → recommend early BSL (shadow; human Mode B)",
        },
        "non_goals": [
            "no silent lot change",
            "no auto early-BSL until human stacks with Mode B",
            "no threshold tune on 2026 canon",
            "do not replace mid-warn; complementary score",
        ],
        "next": "ASI-P6 shadow / optional combine with ASI_P5_TEP_MID_BSL_01",
    }

    with (asi_dir / "rec_model.pkl").open("wb") as fh:
        pickle.dump({"model": model, "feature_names": names, "exit_threshold": thr}, fh)
    (asi_dir / "rec_model_card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")

    shadow = {
        "schema": "fema_asi_rec_shadow_v1",
        "computed_at": card["computed_at"],
        "exit_threshold": thr,
        "calibrate": best,
        "method": f"P(recover) <= {thr} → RECOMMEND early exit",
    }
    (asi_dir / "asi_shadow_rec.json").write_text(json.dumps(shadow, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "exit_threshold": thr,
        "auc_calibrate": card["auc_calibrate"],
        "calibrate": best,
        "paths": {
            "model": str(asi_dir / "rec_model.pkl"),
            "card": str(asi_dir / "rec_model_card.json"),
            "shadow": str(asi_dir / "asi_shadow_rec.json"),
        },
    }


def write_rec_review(asi_dir: Path) -> dict[str, Any]:
    asi_dir = Path(asi_dir)
    card = json.loads((asi_dir / "rec_model_card.json").read_text(encoding="utf-8"))
    cal = card.get("calibrate_eval") or {}
    pack = {
        "schema": "fema_asi_p6_review_pack_v1",
        "computed_at": _utc_now(),
        "philosophy": "recommend_before_act",
        "exit_threshold": card.get("exit_threshold"),
        "holdout": cal,
        "auc_calibrate": card.get("auc_calibrate"),
        "policy": card.get("policy"),
        "action_map": card.get("action_map"),
        "verdict_hint": (
            "REC OK - proceed to policy ADR / shadow"
            if float(cal.get("fail_precision") or 0) >= 0.35 and int(cal.get("exit_n") or 0) > 0
            else "REC WEAK - retune or stay shadow-only"
        ),
    }
    out_json = asi_dir / "asi_p6_review_pack.json"
    out_md = asi_dir / "asi_p6_review_pack.md"
    out_json.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
    md = "\n".join(
        [
            "# ASI-P6 review — basket recovery probability",
            "",
            f"Generated: `{pack['computed_at']}`",
            f"Exit threshold (low P recover): **{pack['exit_threshold']}**",
            f"AUC calibrate: **{pack['auc_calibrate']}**",
            "",
            "## Holdout (calibrate mid-rows)",
            "",
            f"- exit recommend n / rate: **{cal.get('exit_n')}** / **{cal.get('exit_rate')}**",
            f"- fail precision (true non-recoveries): **{cal.get('fail_precision')}**",
            f"- false-cut recoveries: **{cal.get('false_cut_recoveries')}**",
            f"- net of exit-recommend set: **{cal.get('net_of_exit_set')}**",
            "",
            f"**Verdict:** {pack['verdict_hint']}",
            "",
            "Default: **shadow recommend only**. Early BSL remains human Mode B (`ASI_P5_TEP_MID_BSL_01`).",
            "",
        ]
    )
    out_md.write_text(md, encoding="utf-8")
    pack["paths"] = {"json": str(out_json), "md": str(out_md)}
    return pack


def score_rec_baskets(
    baskets_path: Path,
    *,
    asi_dir: Path | None = None,
    model_path: Path | None = None,
    min_depth: int = 2,
    max_warn: int = 5,
) -> dict[str, Any]:
    from fema_ops.asi.dataset import merge_labeled_rows
    from paths import KB_DIR

    asi_dir = Path(asi_dir) if asi_dir else KB_DIR / "asi"
    path = Path(model_path) if model_path else asi_dir / "rec_model.pkl"
    if not path.is_file():
        raise FileNotFoundError(f"rec model missing: {path}")
    with path.open("rb") as fh:
        bundle = pickle.load(fh)
    model = bundle["model"]
    names = list(bundle.get("feature_names") or REC_STATIC)
    thr = float(bundle.get("exit_threshold", 0.0))
    card_path = asi_dir / "rec_model_card.json"
    if card_path.is_file():
        thr = float(json.loads(card_path.read_text(encoding="utf-8")).get("exit_threshold", thr))

    labeled = merge_labeled_rows(read_csv_rows(baskets_path))
    rows = expand_rec_rows(labeled, min_depth=min_depth, max_warn=max_warn)
    if not rows:
        return {
            "schema": "fema_asi_rec_shadow_run_v1",
            "computed_at": _utc_now(),
            "exit_threshold": thr,
            "n_rec_rows": 0,
            "shadow": {"exit_n": 0},
        }

    X, y = featurize_rec(rows, names)
    p = model.predict_proba(X)[:, 1]
    mask = p <= thr + 1e-12
    exit_n = int(mask.sum())
    true_fail = int(((y == 0) & mask).sum())
    false_cut = int(((y == 1) & mask).sum())
    warned_baskets: set[str] = set()
    net = 0.0
    for row, s in zip(rows, mask):
        if not s:
            continue
        bid = str(row.get("basket_id", ""))
        if bid not in warned_baskets:
            warned_baskets.add(bid)
            net += _f(row, "profit")

    shadow = {
        "exit_n": exit_n,
        "exit_rate": round(exit_n / len(rows), 4),
        "exit_baskets_n": len(warned_baskets),
        "fail_precision_rows": round(true_fail / exit_n, 4) if exit_n else 0.0,
        "false_cut_recoveries": false_cut,
        "net_of_exit_baskets": round(net, 2),
        "method": f"P(recover) <= {thr} → RECOMMEND early exit",
    }
    return {
        "schema": "fema_asi_rec_shadow_run_v1",
        "computed_at": _utc_now(),
        "exit_threshold": thr,
        "n_baskets": len(labeled),
        "n_rec_rows": len(rows),
        "baskets_path": str(baskets_path).replace("\\", "/"),
        "shadow": shadow,
        "policy": "shadow_recommend_only",
    }
