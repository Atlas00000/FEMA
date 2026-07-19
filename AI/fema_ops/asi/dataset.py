"""ASI-P1 — build labeled dataset, splits, baseline, shadow v0."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fema_ops.asi.features import OPEN_COLS, TEP_DERIVED, build_open_features, parse_open_time
from fema_ops.asi.labels import classify_basket, label_summary

OUTCOME_COLS = [
    "close_time",
    "profit",
    "exit_reason",
    "hit_tp",
    "hit_bsl",
    "mae",
    "mfe",
    "bars_alive",
    "max_depth",
    "label_class",
    "y_steamroller",
    "y_fail",
]

DATASET_FIELDS = OPEN_COLS + TEP_DERIVED + OUTCOME_COLS

DEFAULT_SPLITS = {
    "schema": "fema_asi_splits_v1",
    "train": {
        "start": "2020.01.01",
        "end": "2023.12.31",
        "purpose": "model fit",
    },
    "calibrate": {
        "start": "2024.01.01",
        "end": "2025.12.31",
        "purpose": "threshold tune — not promote window",
    },
    "promote_frozen": {
        "start": "2026.01.01",
        "end": "2026.07.31",
        "purpose": "G1 one-shot — never tune threshold here",
    },
    "rule": "Disjoint spans; no random shuffle; promote_frozen held out until P2/P4 freeze.",
}

# Longer train: fit on 2018–2024, tune threshold on 2025 only (guardrail holdout).
LONG_TRAIN_SPLITS = {
    "schema": "fema_asi_splits_v1",
    "profile": "long_train",
    "philosophy": "guardrails_not_gates",
    "train": {
        "start": "2018.01.01",
        "end": "2024.12.31",
        "purpose": "model fit (extended 2018+)",
    },
    "calibrate": {
        "start": "2025.01.01",
        "end": "2025.12.31",
        "purpose": "threshold tune + guardrail holdout",
    },
    "promote_frozen": {
        "start": "2026.01.01",
        "end": "2026.07.31",
        "purpose": "optional live slice — not a production parity target",
    },
    "rule": "Disjoint spans; no random shuffle; calibrate is guardrail holdout.",
}

SPLIT_PROFILES: dict[str, dict[str, Any]] = {
    "default": DEFAULT_SPLITS,
    "long": LONG_TRAIN_SPLITS,
}


def resolve_splits(profile: str | None = None, splits: dict[str, Any] | None = None) -> dict[str, Any]:
    if splits is not None:
        return splits
    key = (profile or "default").strip().lower()
    if key not in SPLIT_PROFILES:
        raise ValueError(f"Unknown split profile {profile!r}; use {list(SPLIT_PROFILES)}")
    return dict(SPLIT_PROFILES[key])


def _in_window(open_time: str, start: str, end: str) -> bool:
    t = parse_open_time(open_time)
    lo = parse_open_time(f"{start} 00:00:00")
    hi = parse_open_time(f"{end} 23:59:59")
    return lo <= t <= hi


def split_rows(rows: list[dict], splits: dict[str, Any]) -> dict[str, list[dict]]:
    buckets: dict[str, list[dict]] = {
        "train": [],
        "calibrate": [],
        "promote_frozen": [],
        "other": [],
    }
    for row in rows:
        ot = str(row.get("open_time", ""))
        if _in_window(ot, splits["train"]["start"], splits["train"]["end"]):
            buckets["train"].append(row)
        elif _in_window(ot, splits["calibrate"]["start"], splits["calibrate"]["end"]):
            buckets["calibrate"].append(row)
        elif _in_window(
            ot, splits["promote_frozen"]["start"], splits["promote_frozen"]["end"]
        ):
            buckets["promote_frozen"].append(row)
        else:
            buckets["other"].append(row)
    return buckets


def _pf(rows: list[dict]) -> float:
    wins = sum(_f(r, "profit") for r in rows if _f(r, "profit") > 0)
    losses = sum(-_f(r, "profit") for r in rows if _f(r, "profit") < 0)
    if losses <= 0:
        return 99.0 if wins > 0 else 0.0
    return round(wins / losses, 4)


def _f(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def basket_run_metrics(rows: list[dict]) -> dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {"n": 0, "profit_factor": 0.0, "win_rate": 0.0, "net": 0.0}
    profits = [_f(r, "profit") for r in rows]
    wins = [p for p in profits if p > 0]
    return {
        "n": n,
        "profit_factor": _pf(rows),
        "win_rate": round(len(wins) / n, 4),
        "net": round(sum(profits), 2),
        "steamroller_rate": round(
            sum(int(r.get("y_steamroller", 0)) for r in rows) / n, 4
        ),
    }


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


def shadow_skip_v0(
    rows: list[dict],
    *,
    train_rows: list[dict],
    skip_quantile: float = 0.90,
) -> dict[str, Any]:
    """P1-05 provisional skip: top (1-q) impulse_score on train → apply everywhere."""
    train_scores = [_f(r, "impulse_score") for r in train_rows]
    threshold = _percentile(train_scores, skip_quantile)
    skipped: list[dict] = []
    kept: list[dict] = []
    for row in rows:
        if _f(row, "impulse_score") >= threshold:
            skipped.append(row)
        else:
            kept.append(row)

    def bucket(part: list[dict]) -> dict[str, Any]:
        if not part:
            return {"n": 0, "net": 0.0, "steamroller_n": 0, "winner_n": 0}
        return {
            "n": len(part),
            "net": round(sum(_f(r, "profit") for r in part), 2),
            "steamroller_n": sum(int(r.get("y_steamroller", 0)) for r in part),
            "winner_n": sum(1 for r in part if int(r.get("y_steamroller", 0)) == 0 and _f(r, "profit") > 0),
        }

    sk, ke = bucket(skipped), bucket(kept)
    false_skip_winners = sum(
        1 for r in skipped if int(r.get("y_steamroller", 0)) == 0 and _f(r, "profit") > 0
    )
    true_skip_steam = sum(int(r.get("y_steamroller", 0)) for r in skipped)

    return {
        "schema": "fema_asi_shadow_v0",
        "method": "impulse_score >= train p90 (provisional — replaced in P2)",
        "skip_quantile": skip_quantile,
        "threshold": round(threshold, 4),
        "skip_rate": round(len(skipped) / len(rows), 4) if rows else 0.0,
        "skipped": sk,
        "kept": ke,
        "skipped_steamrollers": true_skip_steam,
        "skipped_winners_false": false_skip_winners,
        "net_if_skipped": sk["net"],
        "net_kept": ke["net"],
        "net_all": round(sum(_f(r, "profit") for r in rows), 2),
    }


def merge_labeled_rows(raw_rows: list[dict]) -> list[dict[str, Any]]:
    open_rows = build_open_features(raw_rows)
    by_id = {str(r.get("basket_id", "")): r for r in raw_rows}
    out: list[dict[str, Any]] = []
    for feat in open_rows:
        bid = str(feat.get("basket_id", ""))
        raw = by_id.get(bid, {})
        lab = classify_basket(raw)
        row: dict[str, Any] = dict(feat)
        for c in OUTCOME_COLS:
            if c in ("label_class", "y_steamroller", "y_fail"):
                continue
            row[c] = raw.get(c, "")
        row.update(lab)
        out.append(row)
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=DATASET_FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in DATASET_FIELDS})


def build_asi_dataset(
    *,
    baskets_path: Path,
    out_dir: Path,
    promote_baskets_path: Path | None = None,
    splits: dict[str, Any] | None = None,
    split_profile: str | None = None,
    skip_quantile: float = 0.90,
) -> dict[str, Any]:
    from csv_util import parse_meta_lines, read_csv_rows
    from paths import REPO_ROOT

    def _rel(p: Path) -> str:
        try:
            return p.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
        except ValueError:
            return str(p).replace("\\", "/")

    splits = resolve_splits(split_profile, splits)
    meta = parse_meta_lines(baskets_path)
    raw = read_csv_rows(baskets_path)
    labeled = merge_labeled_rows(raw)

    promote_labeled: list[dict] = []
    promote_meta: dict[str, str] = {}
    if promote_baskets_path and promote_baskets_path.is_file():
        promote_meta = parse_meta_lines(promote_baskets_path)
        promote_labeled = merge_labeled_rows(read_csv_rows(promote_baskets_path))

    buckets = split_rows(labeled, splits)
    if promote_labeled:
        buckets["promote_frozen"] = promote_labeled
    else:
        buckets["promote_frozen"] = []

    out_dir.mkdir(parents=True, exist_ok=True)
    promote_csv = out_dir / "dataset_promote_frozen.csv"
    if promote_labeled:
        write_csv(promote_csv, promote_labeled)
    elif promote_csv.is_file():
        promote_csv.unlink()

    write_csv(out_dir / "dataset_full.csv", labeled)
    for name in ("train", "calibrate", "other"):
        part = buckets.get(name) or []
        if part:
            write_csv(out_dir / f"dataset_{name}.csv", part)

    splits_doc = {**splits, "counts": {k: len(v) for k, v in buckets.items()}}
    (out_dir / "splits.json").write_text(
        json.dumps(splits_doc, indent=2), encoding="utf-8"
    )

    baseline = {
        "schema": "fema_asi_baseline_v1",
        "computed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_baskets": _rel(baskets_path),
        "source_meta": meta,
        "promote_baskets": _rel(promote_baskets_path) if promote_baskets_path else None,
        "promote_meta": promote_meta or None,
        "labels": label_summary(labeled),
        "promote_labels": label_summary(promote_labeled) if promote_labeled else None,
        "metrics": {
            "all": basket_run_metrics(labeled),
            "train": basket_run_metrics(buckets["train"]),
            "calibrate": basket_run_metrics(buckets["calibrate"]),
            "promote_frozen": basket_run_metrics(buckets["promote_frozen"]),
        },
    }
    (out_dir / "asi_baseline_metrics.json").write_text(
        json.dumps(baseline, indent=2), encoding="utf-8"
    )

    train_rows = buckets["train"]
    shadow = {
        "schema": "fema_asi_shadow_report_v1",
        "computed_at": baseline["computed_at"],
        "splits": splits_doc["counts"],
        "all": shadow_skip_v0(labeled, train_rows=train_rows, skip_quantile=skip_quantile),
        "calibrate": shadow_skip_v0(
            buckets["calibrate"], train_rows=train_rows, skip_quantile=skip_quantile
        )
        if buckets["calibrate"]
        else None,
        "promote_frozen": shadow_skip_v0(
            buckets["promote_frozen"], train_rows=train_rows, skip_quantile=skip_quantile
        )
        if buckets["promote_frozen"]
        else None,
    }
    (out_dir / "asi_shadow_v0.json").write_text(
        json.dumps(shadow, indent=2), encoding="utf-8"
    )

    return {
        "ok": True,
        "out_dir": str(out_dir),
        "n": len(labeled),
        "labels": baseline["labels"],
        "metrics": baseline["metrics"],
        "shadow_all": shadow["all"],
        "paths": {
            "dataset_full": str(out_dir / "dataset_full.csv"),
            "splits": str(out_dir / "splits.json"),
            "baseline": str(out_dir / "asi_baseline_metrics.json"),
            "shadow": str(out_dir / "asi_shadow_v0.json"),
        },
    }


def write_asi_build_report(report: dict[str, Any]) -> str:
    lines = [
        "# ASI-P1 build report",
        "",
        f"- rows: **{report.get('n', 0)}**",
        f"- steamroller rate: **{(report.get('labels') or {}).get('y_steamroller_rate', 0)}**",
        f"- out: `{report.get('out_dir', '')}`",
        "",
        "## Shadow v0 (train p90 impulse)",
        "",
    ]
    sh = report.get("shadow_all") or {}
    lines.extend(
        [
            f"- skip rate: **{sh.get('skip_rate', 0)}**",
            f"- skipped steamrollers: **{sh.get('skipped_steamrollers', 0)}**",
            f"- false-skip winners: **{sh.get('skipped_winners_false', 0)}**",
            f"- net all / kept / skipped: **{sh.get('net_all')} / {sh.get('net_kept')} / {sh.get('net_if_skipped')}**",
        ]
    )
    return "\n".join(lines) + "\n"
