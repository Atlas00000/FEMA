"""ASI-P5 — mid-basket steamroller early warning (offline)."""

from __future__ import annotations

import csv
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
from fema_ops.asi.dataset import resolve_splits
from fema_ops.asi.features import OPEN_COLS, parse_open_time
from fema_ops.asi.labels import classify_basket
from fema_ops.asi.tep import safe_auc

# Mid-basket features: open snapshot + depth milestone (no outcome leakage)
MID_STATIC = [
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
    "ema_slope_accel",
    "adx_accel",
    "atr_expansion_rate",
    "consecutive_same_dir",
    "dist_ema_abs",
    "impulse_score",
    "warn_depth",
    "is_sell",
]

DATASET_FIELDS = (
    ["basket_id", "open_time", "symbol", "direction", "warn_depth", "max_depth"]
    + [c for c in MID_STATIC if c not in ("warn_depth", "is_sell")]
    + [
        "is_sell",
        "profit",
        "hit_bsl",
        "mae",
        "mfe",
        "bars_alive",
        "label_class",
        "y_steamroller",
        "y_mid_steamroller",
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


def mid_checkpoints(max_depth: int, *, min_depth: int = 2, max_warn: int = 5) -> list[int]:
    """Depth milestones knowable live when that level first fills (no future leakage)."""
    if max_depth < min_depth:
        return []
    return list(range(min_depth, min(max_depth, max_warn) + 1))


def expand_mid_rows(
    labeled_open: list[dict],
    *,
    min_depth: int = 2,
    max_warn: int = 5,
) -> list[dict[str, Any]]:
    """One row per (basket, warn_depth) for baskets that reached that depth."""
    out: list[dict[str, Any]] = []
    for row in labeled_open:
        max_depth = int(float(row.get("max_depth", 0) or 0))
        lab = classify_basket(row)
        y = int(lab["y_steamroller"])
        for d in mid_checkpoints(max_depth, min_depth=min_depth, max_warn=max_warn):
            mid = {c: row.get(c, "") for c in OPEN_COLS}
            mid.update({k: row.get(k, "") for k in ("profit", "hit_bsl", "mae", "mfe", "bars_alive", "max_depth")})
            mid["warn_depth"] = d
            mid["is_sell"] = 1.0 if str(row.get("direction", "")).upper() == "SELL" else 0.0
            mid["label_class"] = lab["label_class"]
            mid["y_steamroller"] = y
            mid["y_mid_steamroller"] = y  # eventual steamroller from this depth onward
            # carry derived open features if present
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


def featurize_mid(rows: list[dict], feature_names: list[str] | None = None) -> tuple[np.ndarray, np.ndarray]:
    names = list(feature_names or MID_STATIC)
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
        y.append(int(float(row.get("y_mid_steamroller", row.get("y_steamroller", 0)) or 0)))
    return np.asarray(X, dtype=float), np.asarray(y, dtype=int)


def write_mid_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=DATASET_FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in DATASET_FIELDS})


def build_mid_dataset(
    *,
    baskets_path: Path,
    out_dir: Path,
    split_profile: str = "long",
    min_depth: int = 2,
    max_warn: int = 5,
) -> dict[str, Any]:
    from fema_ops.asi.dataset import merge_labeled_rows

    raw = read_csv_rows(baskets_path)
    # merge_labeled_rows already attaches open derived + labels
    labeled = merge_labeled_rows(raw)
    mid_rows = expand_mid_rows(labeled, min_depth=min_depth, max_warn=max_warn)

    splits = resolve_splits(split_profile)
    # split by parent basket open_time
    buckets = {"train": [], "calibrate": [], "promote_frozen": [], "other": []}
    for row in mid_rows:
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
    write_mid_csv(out_dir / "mid_dataset_full.csv", mid_rows)
    for name, part in buckets.items():
        if part:
            write_mid_csv(out_dir / f"mid_dataset_{name}.csv", part)

    steam = sum(int(r.get("y_mid_steamroller", 0)) for r in mid_rows)
    report = {
        "schema": "fema_asi_mid_build_v1",
        "computed_at": _utc_now(),
        "phase": "ASI-P5",
        "source_baskets": str(baskets_path).replace("\\", "/"),
        "split_profile": splits.get("profile", split_profile),
        "min_depth": min_depth,
        "max_warn": max_warn,
        "n_baskets": len(labeled),
        "n_mid_rows": len(mid_rows),
        "y_mid_steamroller_rate": round(steam / len(mid_rows), 4) if mid_rows else 0.0,
        "counts": {k: len(v) for k, v in buckets.items()},
        "feature_names": MID_STATIC,
        "leakage_rule": "warn_depth known when level fills; no mae/mfe/profit as features",
    }
    (out_dir / "mid_splits.json").write_text(json.dumps({**splits, **report}, indent=2), encoding="utf-8")
    (out_dir / "mid_build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def train_mid(
    *,
    asi_dir: Path,
    max_skip: float = 0.15,
) -> dict[str, Any]:
    """Train P(eventual steamroller | open features, warn_depth)."""
    asi_dir = Path(asi_dir)
    train_rows = read_csv_rows(asi_dir / "mid_dataset_train.csv")
    cal_rows = read_csv_rows(asi_dir / "mid_dataset_calibrate.csv")
    if not train_rows or not cal_rows:
        raise FileNotFoundError("Run asi-mid-build first")

    names = list(MID_STATIC)
    X_tr, y_tr = featurize_mid(train_rows, names)
    X_cal, y_cal = featurize_mid(cal_rows, names)
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

    # Permissive threshold: top max_skip mass with precision preference
    candidates = []
    for t in (0.05, 0.08, 0.10, 0.12, 0.15):
        if t > max_skip + 1e-9:
            continue
        thr = float(np.quantile(p_cal, 1.0 - t))
        mask = p_cal >= thr
        skip_n = int(mask.sum())
        if skip_n == 0:
            continue
        true_pos = int(((y_cal == 1) & mask).sum())
        false_win = 0
        for row, s in zip(cal_rows, mask):
            if s and int(row.get("y_mid_steamroller", 0)) == 0 and _f(row, "profit") > 0:
                false_win += 1
        prec = true_pos / skip_n
        net = sum(_f(r, "profit") for r, s in zip(cal_rows, mask) if s)
        # For mid-basket, "skip" means warn — score by precision + net avoided
        score = 80.0 * prec - 5.0 * false_win + (20.0 if net <= 0 else -20.0)
        candidates.append(
            {
                "threshold": round(thr, 6),
                "skip_rate": round(skip_n / len(cal_rows), 4),
                "skip_n": skip_n,
                "precision": round(prec, 4),
                "false_warn_winners": false_win,
                "skipped_steamrollers": true_pos,
                "net_warned": round(net, 2),
                "score": round(score, 4),
            }
        )
    candidates.sort(key=lambda d: d["score"], reverse=True)
    best = candidates[0] if candidates else {"threshold": 1.0, "skip_n": 0, "precision": 0.0}

    thr = float(best["threshold"])
    card = {
        "schema": "fema_asi_mid_model_card_v1",
        "computed_at": _utc_now(),
        "phase": "ASI-P5",
        "label": "y_mid_steamroller",
        "model_kind": "logistic_regression",
        "feature_names": names,
        "threshold": thr,
        "max_skip": max_skip,
        "auc_train": safe_auc(y_tr, model.predict_proba(X_tr)[:, 1]),
        "auc_calibrate": safe_auc(y_cal, p_cal),
        "calibrate_eval": best,
        "calibrate_candidates": candidates,
        "policy": "warn_only_default",
        "non_goals": [
            "no silent lot change",
            "no auto early-BSL until human opt-in",
            "no threshold tune on 2026 canon",
        ],
        "next": "ASI-P5 shadow / optional early-BSL ADR",
    }

    with (asi_dir / "mid_model.pkl").open("wb") as fh:
        pickle.dump({"model": model, "feature_names": names, "threshold": thr}, fh)
    (asi_dir / "mid_model_card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")

    shadow = {
        "schema": "fema_asi_mid_shadow_v1",
        "computed_at": card["computed_at"],
        "threshold": thr,
        "calibrate": best,
        "method": f"P(mid_steamroller) >= {thr} → WARN",
    }
    (asi_dir / "asi_shadow_mid.json").write_text(json.dumps(shadow, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "threshold": thr,
        "auc_calibrate": card["auc_calibrate"],
        "calibrate": best,
        "paths": {
            "model": str(asi_dir / "mid_model.pkl"),
            "card": str(asi_dir / "mid_model_card.json"),
            "shadow": str(asi_dir / "asi_shadow_mid.json"),
        },
    }


def write_mid_review(asi_dir: Path) -> dict[str, Any]:
    asi_dir = Path(asi_dir)
    card = json.loads((asi_dir / "mid_model_card.json").read_text(encoding="utf-8"))
    cal = card.get("calibrate_eval") or {}
    pack = {
        "schema": "fema_asi_p5_review_pack_v1",
        "computed_at": _utc_now(),
        "philosophy": "warn_before_act",
        "threshold": card.get("threshold"),
        "holdout": cal,
        "auc_calibrate": card.get("auc_calibrate"),
        "policy": card.get("policy"),
        "verdict_hint": (
            "MID WARN OK — proceed to policy ADR / shadow"
            if float(cal.get("precision") or 0) >= 0.35 and int(cal.get("skip_n") or 0) > 0
            else "MID WARN WEAK — retune or stay shadow-only"
        ),
    }
    out_json = asi_dir / "asi_p5_review_pack.json"
    out_md = asi_dir / "asi_p5_review_pack.md"
    out_json.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
    md = "\n".join(
        [
            "# ASI-P5 review — mid-basket steamroller warn",
            "",
            f"Generated: `{pack['computed_at']}`",
            f"Threshold: **{pack['threshold']}**",
            f"AUC calibrate: **{pack['auc_calibrate']}**",
            "",
            "## Holdout (calibrate mid-rows)",
            "",
            f"- warn_n / rate: **{cal.get('skip_n')}** / **{cal.get('skip_rate')}**",
            f"- precision: **{cal.get('precision')}**",
            f"- false-warn winners: **{cal.get('false_warn_winners')}**",
            f"- steamrollers flagged: **{cal.get('skipped_steamrollers')}**",
            f"- net of warned baskets: **{cal.get('net_warned')}**",
            "",
            f"**Verdict:** {pack['verdict_hint']}",
            "",
            "Default action: **WARN only** (log). Early BSL / stop-adds requires human opt-in.",
            "",
        ]
    )
    out_md.write_text(md, encoding="utf-8")
    pack["paths"] = {"json": str(out_json), "md": str(out_md)}
    return pack


MID_GATE_SCHEMA = "fema_mid_gate_v1"


def export_mid_gate(
    *,
    asi_dir: Path,
    out_name: str = "mid_gate_v1.txt",
) -> dict[str, Any]:
    """Export mid-warn logistic weights for MQL AiMidWarn.mqh (warn-only)."""
    asi_dir = Path(asi_dir)
    model_path = asi_dir / "mid_model.pkl"
    card_path = asi_dir / "mid_model_card.json"
    if not model_path.is_file():
        raise FileNotFoundError(f"Missing {model_path} — run asi-mid-train first")

    with model_path.open("rb") as fh:
        bundle = pickle.load(fh)
    model = bundle["model"]
    scaler = model.named_steps["scaler"]
    clf = model.named_steps["clf"]
    card = json.loads(card_path.read_text(encoding="utf-8")) if card_path.is_file() else {}
    feature_names = list(card.get("feature_names") or bundle.get("feature_names") or MID_STATIC)
    threshold = float(card.get("threshold", bundle.get("threshold", 1.0)))
    coef = clf.coef_.ravel()
    if len(coef) != len(feature_names):
        raise ValueError(f"coef len {len(coef)} != features {len(feature_names)}")

    meta = {
        "schema": MID_GATE_SCHEMA,
        "exported_at": _utc_now(),
        "phase": "ASI-P5",
        "policy": "warn_only_default",
        "threshold": threshold,
        "intercept": float(clf.intercept_[0]),
        "feature_names": feature_names,
    }
    lines = [
        MID_GATE_SCHEMA,
        f"threshold\t{threshold:.8f}",
        f"intercept\t{meta['intercept']:.12f}",
        f"exported_at\t{meta['exported_at']}",
        f"policy\twarn_only",
        "feature\tmean\tscale\tcoef",
    ]
    for i, name in enumerate(feature_names):
        lines.append(
            f"{name}\t{scaler.mean_[i]:.12f}\t{scaler.scale_[i]:.12f}\t{coef[i]:.12f}"
        )
    txt_path = asi_dir / out_name
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path = asi_dir / "mid_gate.json"
    json_path.write_text(json.dumps({**meta, "paths": {"txt": txt_path.name}}, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "threshold": threshold,
        "n_features": len(feature_names),
        "paths": {"txt": str(txt_path), "json": str(json_path)},
    }


def score_mid_baskets(
    baskets_path: Path,
    *,
    asi_dir: Path | None = None,
    model_path: Path | None = None,
    min_depth: int = 2,
    max_warn: int = 5,
) -> dict[str, Any]:
    """Offline mid-warn shadow on closed baskets (depth-milestone expansion)."""
    from fema_ops.asi.dataset import merge_labeled_rows
    from paths import KB_DIR, REPO_ROOT

    asi_dir = Path(asi_dir) if asi_dir else KB_DIR / "asi"
    path = Path(model_path) if model_path else asi_dir / "mid_model.pkl"
    if not path.is_file():
        raise FileNotFoundError(f"mid model missing: {path}")
    with path.open("rb") as fh:
        bundle = pickle.load(fh)
    model = bundle["model"]
    names = list(bundle.get("feature_names") or MID_STATIC)
    thr = float(bundle.get("threshold", 1.0))
    card_path = asi_dir / "mid_model_card.json"
    if card_path.is_file():
        thr = float(json.loads(card_path.read_text(encoding="utf-8")).get("threshold", thr))

    labeled = merge_labeled_rows(read_csv_rows(baskets_path))
    mid_rows = expand_mid_rows(labeled, min_depth=min_depth, max_warn=max_warn)
    if not mid_rows:
        return {
            "schema": "fema_asi_mid_shadow_run_v1",
            "computed_at": _utc_now(),
            "threshold": thr,
            "n_mid_rows": 0,
            "shadow": {"warn_n": 0, "warn_rate": 0.0},
        }

    X, y = featurize_mid(mid_rows, names)
    p = model.predict_proba(X)[:, 1]
    mask = p >= thr - 1e-12
    warn_n = int(mask.sum())
    true_pos = int(((y == 1) & mask).sum())
    false_win = 0
    net = 0.0
    # Deduplicate by basket_id for basket-level net (first warn only counts once for net)
    warned_baskets: set[str] = set()
    for row, s, pi in zip(mid_rows, mask, p):
        if not s:
            continue
        bid = str(row.get("basket_id", ""))
        if bid not in warned_baskets:
            warned_baskets.add(bid)
            net += _f(row, "profit")
            if int(row.get("y_mid_steamroller", 0)) == 0 and _f(row, "profit") > 0:
                false_win += 1

    shadow = {
        "warn_n": warn_n,
        "warn_rate": round(warn_n / len(mid_rows), 4),
        "warn_baskets_n": len(warned_baskets),
        "precision_rows": round(true_pos / warn_n, 4) if warn_n else 0.0,
        "steamrollers_flagged_rows": true_pos,
        "false_warn_winner_baskets": false_win,
        "net_warned_baskets": round(net, 2),
        "method": f"P(mid_steamroller) >= {thr} → WARN",
    }
    return {
        "schema": "fema_asi_mid_shadow_run_v1",
        "computed_at": _utc_now(),
        "threshold": thr,
        "n_baskets": len(labeled),
        "n_mid_rows": len(mid_rows),
        "baskets_path": str(baskets_path).replace("\\", "/"),
        "shadow": shadow,
        "policy": "warn_only",
    }


def score_mid_run(run_id: str, *, deposit: float = 400.0) -> dict[str, Any]:
    from paths import KB_DIR, KB_RUNS_DIR, REPO_ROOT

    folder = KB_RUNS_DIR / run_id
    metrics_path = folder / "metrics.json"
    if not metrics_path.is_file():
        raise FileNotFoundError(f"run not found: {folder}")
    meta = json.loads(metrics_path.read_text(encoding="utf-8"))
    baskets_rel = meta.get("baskets_path") or ""
    baskets = (REPO_ROOT / baskets_rel).resolve() if baskets_rel else None
    if baskets is None or not baskets.is_file():
        from paths import LATEST_BASKETS

        baskets = LATEST_BASKETS
    if not baskets.is_file():
        raise FileNotFoundError(f"baskets missing for {run_id}")

    report = score_mid_baskets(baskets)
    report["run_id"] = run_id
    report["preset"] = meta.get("preset")
    report["window"] = meta.get("window")
    out = folder / f"asi_mid_shadow_{run_id}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    shadows = KB_DIR / "asi" / "shadows"
    shadows.mkdir(parents=True, exist_ok=True)
    out2 = shadows / f"asi_mid_shadow_{run_id}.json"
    out2.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    meta["asi_mid_shadow"] = {
        "schema": "fema_asi_mid_shadow_stamp_v1",
        "computed_at": report["computed_at"],
        "warn_n": report["shadow"]["warn_n"],
        "warn_rate": report["shadow"]["warn_rate"],
        "precision_rows": report["shadow"]["precision_rows"],
        "net_warned_baskets": report["shadow"]["net_warned_baskets"],
        "path": str(out).replace("\\", "/"),
    }
    metrics_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    report["paths"] = {"run": str(out), "shadows": str(out2)}
    return report
