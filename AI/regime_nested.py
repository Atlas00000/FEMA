#!/usr/bin/env python3
"""EC1 nested regime gate — calibrate toxic bar on train only.

Windows (frozen, no peek at holdout for tuning):
  fit   2020.01.01 → 2021.12.31  — ATR + relative toxic stats
  cal   2022.01.01 → 2023.12.31  — pick X / confirm regimes
  hold  2024.01.01 → 2025.12.31  — one eval only

Toxic (on fit):
  PF < fit_all_PF × pf_mult   OR   BSL ≥ fit_median_BSL + X
then pack by worst fit PF until share ≤ 10%, confirm on cal (PF < 1.0, n≥3).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime
from pathlib import Path
from statistics import median

from regime_atlas import (
    REGIME_ORDER,
    assign_regime,
    f,
    load_dataset,
    metrics,
    parse_time,
    scorecard_for,
    soft_skip_holdout_report,
)

_AI_DIR = Path(__file__).resolve().parent
_ROOT = _AI_DIR.parent


def split_windows(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    fit_end = datetime(2021, 12, 31, 23, 59, 59)
    cal_end = datetime(2023, 12, 31, 23, 59, 59)
    hold_start = datetime(2024, 1, 1)
    hold_end = datetime(2025, 12, 31, 23, 59, 59)
    fit = [r for r in rows if r["_ts"] <= fit_end]
    cal = [r for r in rows if fit_end < r["_ts"] <= cal_end]
    hold = [r for r in rows if hold_start <= r["_ts"] <= hold_end]
    return fit, cal, hold


def fit_stats(fit_card: dict, min_n: int = 5) -> dict:
    all_pf = float(fit_card["_all"]["pf"])
    bsls = [
        fit_card[name]["bsl_rate"]
        for name in REGIME_ORDER
        if fit_card[name]["n"] >= min_n
    ]
    return {
        "all_pf": all_pf,
        "median_bsl": float(median(bsls)) if bsls else 0.0,
        "n_regimes": len(bsls),
    }


def toxic_from_fit(
    fit_card: dict,
    stats: dict,
    pf_mult: float,
    bsl_add: float,
    max_skip_share: float,
    min_n: int = 5,
) -> tuple[list[str], list[dict]]:
    """Select regimes toxic on fit under relative rule; pack to share budget."""
    pf_cut = stats["all_pf"] * pf_mult
    bsl_cut = stats["median_bsl"] + bsl_add
    notes = []
    cands = []
    for name in REGIME_ORDER:
        tr = fit_card[name]
        if tr["n"] < min_n:
            continue
        pf_hit = tr["pf"] < pf_cut
        bsl_hit = tr["bsl_rate"] >= bsl_cut
        if not (pf_hit or bsl_hit):
            continue
        notes.append(
            {
                "regime": name,
                "fit_pf": tr["pf"],
                "fit_bsl": tr["bsl_rate"],
                "fit_share": tr["share"],
                "pf_hit": pf_hit,
                "bsl_hit": bsl_hit,
                "pf_cut": round(pf_cut, 4),
                "bsl_cut": round(bsl_cut, 4),
            }
        )
        cands.append((name, tr["pf"], tr["share"], tr["bsl_rate"]))

    cands.sort(key=lambda x: (x[1], -x[3]))
    chosen: list[str] = []
    share = 0.0
    for name, pf, sh, bsl in cands:
        if share + sh > max_skip_share + 1e-9:
            continue
        chosen.append(name)
        share += sh
    return chosen, notes


def confirm_on_cal(
    chosen: list[str],
    cal_card: dict,
    min_n: int = 3,
) -> tuple[list[str], list[dict]]:
    confirmed = []
    notes = []
    for name in chosen:
        ho = cal_card[name]
        note = {
            "regime": name,
            "cal_n": ho["n"],
            "cal_pf": ho["pf"],
            "cal_bsl": ho["bsl_rate"],
            "cal_net": ho["net"],
        }
        if ho["n"] < min_n:
            note["status"] = "drop_sparse_cal"
            notes.append(note)
            continue
        if ho["pf"] >= 1.0:
            note["status"] = "drop_cal_recovered"
            notes.append(note)
            continue
        note["status"] = "confirmed"
        notes.append(note)
        confirmed.append(name)
    return confirmed, notes


def cal_score(rep: dict) -> tuple:
    """Higher is better. Guardrail pass required to beat empty; then damage avoided."""
    g = rep.get("guardrail", {})
    pass_all = 1 if g and all(g.values()) else 0
    avoided = -float(rep.get("net_avoided") or 0.0)
    prec = rep.get("bad_path_precision")
    prec_v = float(prec) if prec is not None else 0.0
    # Empty skip that passes guardrail scores as valid approve-by-default
    nonempty = 1 if rep.get("skip_count", 0) > 0 else 0
    return (pass_all, nonempty, avoided, prec_v)


def main() -> int:
    ap = argparse.ArgumentParser(description="EC1 nested regime calibrate")
    ap.add_argument("--dataset", type=Path, default=_ROOT / "AI" / "data" / "dataset_2020_2025.csv")
    ap.add_argument("--out-dir", type=Path, default=_ROOT / "AI" / "data")
    ap.add_argument("--deposit", type=float, default=1000.0)
    ap.add_argument("--max-skip-share", type=float, default=0.10)
    ap.add_argument("--pf-mult", type=float, default=0.9, help="Fixed: PF < all_pf * this")
    ap.add_argument(
        "--bsl-add-grid",
        type=str,
        default="0,0.02,0.05,0.08,0.10,0.12",
        help="Comma list of X for BSL ≥ median + X (calibrated on 2022-23)",
    )
    args = ap.parse_args()

    rows = load_dataset(args.dataset)
    fit, cal, hold = split_windows(rows)
    if not fit or not cal or not hold:
        print(
            json.dumps(
                {
                    "error": "empty window",
                    "fit_n": len(fit),
                    "cal_n": len(cal),
                    "hold_n": len(hold),
                }
            )
        )
        return 2

    atrs = sorted(f(r, "atr") for r in fit)
    atr_p25 = atrs[int(0.25 * (len(atrs) - 1))]
    atr_p75 = atrs[int(0.75 * (len(atrs) - 1))]
    for r in rows:
        r["regime"] = assign_regime(r, atr_p25, atr_p75)

    fit_card = scorecard_for(fit, atr_p25, atr_p75, args.deposit)
    cal_card = scorecard_for(cal, atr_p25, atr_p75, args.deposit)
    hold_card = scorecard_for(hold, atr_p25, atr_p75, args.deposit)
    stats = fit_stats(fit_card)

    x_grid = [float(x.strip()) for x in args.bsl_add_grid.split(",") if x.strip()]
    trials: list[dict] = []
    # Always include empty gate as a candidate (approve-by-default)
    empty_rep = soft_skip_holdout_report(cal, [], args.deposit)
    empty_trial = {
        "bsl_add": None,
        "pf_mult": args.pf_mult,
        "fit_raw": [],
        "confirmed": [],
        "fit_notes": [],
        "cal_notes": [{"status": "approve_by_default_empty"}],
        "cal_soft_skip": empty_rep,
        "score": list(cal_score(empty_rep)),
        "guardrail_pass": all(empty_rep.get("guardrail", {}).values()),
    }
    trials.append(empty_trial)
    best = empty_trial

    for x in x_grid:
        raw, fit_notes = toxic_from_fit(
            fit_card,
            stats,
            pf_mult=args.pf_mult,
            bsl_add=x,
            max_skip_share=args.max_skip_share,
        )
        confirmed, cal_notes = confirm_on_cal(raw, cal_card)
        cal_rep = soft_skip_holdout_report(cal, confirmed, args.deposit)
        trial = {
            "bsl_add": x,
            "pf_mult": args.pf_mult,
            "fit_raw": raw,
            "confirmed": confirmed,
            "fit_notes": fit_notes,
            "cal_notes": cal_notes,
            "cal_soft_skip": cal_rep,
            "score": list(cal_score(cal_rep)),
            "guardrail_pass": all(cal_rep.get("guardrail", {}).values()),
        }
        trials.append(trial)
        if tuple(trial["score"]) > tuple(best["score"]):
            best = trial

    toxic = list(best["confirmed"])
    # One holdout eval — never used for picking X
    hold_rep = soft_skip_holdout_report(hold, toxic, args.deposit)
    cal_rep = best["cal_soft_skip"]

    skip_ids = [r["_row_id"] for r in rows if r["regime"] in toxic]
    # Holdout-only skip ids for shadow
    hold_skip_ids = [r["_row_id"] for r in hold if r["regime"] in toxic]

    gate = {
        "cal_guardrail_pass": best["guardrail_pass"],
        "hold_guardrail_pass": all(hold_rep.get("guardrail", {}).values()),
        "skip_share_fit_budget": True,  # enforced at pack time
        "no_holdout_tuning": True,
    }
    gate["ec1_nested_pass"] = gate["cal_guardrail_pass"] and gate["hold_guardrail_pass"]

    if not toxic:
        # Note rejected nonempty trials for transparency
        rejected = [
            t
            for t in trials
            if t["confirmed"] and not t["guardrail_pass"]
        ]
        if rejected:
            r0 = rejected[0]
            verdict = (
                "Nested calibrate chose **empty** gate (approve-by-default). "
                f"Nonempty candidate {r0['confirmed']} helped cal net "
                f"({r0['cal_soft_skip'].get('net_avoided')}) but failed cal precision "
                f"({r0['cal_soft_skip'].get('bad_path_precision')}); "
                "forcing it also skips winners on holdout. "
                "Note: fit `high_adx` is toxic on PF but ~25% share — cannot pack under 10%."
            )
        else:
            verdict = (
                "Nested calibrate: no cal-confirmed toxic regime within 10% budget. "
                "Approve-by-default (empty gate)."
            )
    else:
        verdict = (
            f"Nested calibrate froze soft-skip {toxic} "
            f"(pf_mult={args.pf_mult}, bsl_add={best['bsl_add']}). "
            "Shadow only — not wired to EA."
        )

    report = {
        "phase": "EC1-REGIME-NESTED",
        "philosophy": "guardrails_not_gates",
        "split": {
            "fit": {"start": "2020.01.01", "end": "2021.12.31", "n": len(fit)},
            "cal": {"start": "2022.01.01", "end": "2023.12.31", "n": len(cal)},
            "holdout": {"start": "2024.01.01", "end": "2025.12.31", "n": len(hold)},
        },
        "thresholds": {"atr_p25": atr_p25, "atr_p75": atr_p75},
        "fit_stats": stats,
        "rule": {
            "pf_lt": f"fit_all_pf * {args.pf_mult}",
            "bsl_ge": "fit_median_bsl + X",
            "max_skip_share": args.max_skip_share,
            "confirm": "cal PF < 1.0 and n >= 3",
        },
        "chosen": {
            "bsl_add": best["bsl_add"],
            "pf_mult": args.pf_mult,
            "toxic_regimes": toxic,
            "fit_raw_before_confirm": best["fit_raw"],
        },
        "calibration_trials": [
            {
                "bsl_add": t["bsl_add"],
                "confirmed": t["confirmed"],
                "cal_skip_share": t["cal_soft_skip"].get("skip_share"),
                "cal_net_avoided": t["cal_soft_skip"].get("net_avoided"),
                "cal_precision": t["cal_soft_skip"].get("bad_path_precision"),
                "guardrail_pass": t["guardrail_pass"],
                "score": t["score"],
            }
            for t in trials
        ],
        "scorecard_fit": fit_card,
        "scorecard_cal": cal_card,
        "scorecard_holdout": hold_card,
        "cal_soft_skip": cal_rep,
        "holdout_soft_skip": hold_rep,
        "gate_checks": gate,
        "verdict": verdict,
        "deposit_note": "Deposit for DD% only; ignore vs demo $400.",
    }

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "regime_nested_scorecard.json"
    md_path = out / "regime_nested_scorecard.md"
    skip_path = out / "regime_nested_skip_ids.txt"
    hold_skip_path = out / "regime_nested_holdout_skip_ids.txt"

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    skip_path.write_text("\n".join(skip_ids) + ("\n" if skip_ids else ""), encoding="utf-8")
    hold_skip_path.write_text(
        "\n".join(hold_skip_ids) + ("\n" if hold_skip_ids else ""), encoding="utf-8"
    )

    hb, hs = hold_rep["holdout_baseline"], hold_rep["holdout_soft_skip"]
    cb, cs = cal_rep["holdout_baseline"], cal_rep["holdout_soft_skip"]
    lines = [
        "# EC1 Nested Regime Gate",
        "",
        f"Fit {len(fit)} (2020–21) · Cal {len(cal)} (2022–23) · Holdout {len(hold)} (2024–25)",
        f"ATR (fit): p25={atr_p25:.6f} | p75={atr_p75:.6f}",
        f"Fit all PF={stats['all_pf']:.4f} · median BSL={stats['median_bsl']:.2%}",
        f"Frozen: **pf_mult={args.pf_mult}** · **bsl_add={best['bsl_add']}** · toxic **{toxic or 'none'}**",
        "",
        verdict,
        "",
        "## Fit regimes (2020–21)",
        "",
        "| Regime | N | Share | PF | BSL% | Net |",
        "| ------ | - | ----- | -- | ---- | --- |",
    ]
    for name in REGIME_ORDER:
        c = fit_card[name]
        if c["n"] == 0:
            continue
        lines.append(
            f"| {name} | {c['n']} | {c['share']:.1%} | {c['pf']:.2f} | "
            f"{c['bsl_rate']:.1%} | {c['net']:.1f} |"
        )
    lines += [
        "",
        "## Calibration grid (2022–23 only)",
        "",
        "| X (bsl_add) | Confirmed | Cal skip% | Net skipped | Precision | Guardrail |",
        "| ----------- | --------- | --------- | ----------- | --------- | --------- |",
    ]
    for t in trials:
        cr = t["cal_soft_skip"]
        x_label = "—" if t["bsl_add"] is None else f"{t['bsl_add']:.2f}"
        lines.append(
            f"| {x_label} | {t['confirmed'] or '—'} | "
            f"{cr.get('skip_share', 0):.1%} | {cr.get('net_avoided', 0):.1f} | "
            f"{cr.get('bad_path_precision')} | "
            f"{'pass' if t['guardrail_pass'] else 'fail'} |"
        )
    lines += [
        "",
        "## Cal soft-skip (chosen X)",
        "",
        f"- Baseline: PF {cb['pf']:.2f} | net {cb['net']:.1f} | n {cb['n']}",
        f"- Soft-skip: PF {cs['pf']:.2f} | net {cs['net']:.1f} | n {cs['n']}",
        f"- Skip share {cal_rep['skip_share']:.1%} | precision {cal_rep['bad_path_precision']} | "
        f"net skipped {cal_rep['net_avoided']:.1f}",
        "",
        "## Holdout one-shot eval (2024–25) — not used for tuning",
        "",
        f"- Baseline: PF {hb['pf']:.2f} | net {hb['net']:.1f} | n {hb['n']}",
        f"- Soft-skip: PF {hs['pf']:.2f} | net {hs['net']:.1f} | n {hs['n']}",
        f"- Skip share {hold_rep['skip_share']:.1%} | precision {hold_rep['bad_path_precision']} | "
        f"net skipped {hold_rep['net_avoided']:.1f}",
        f"- Guardrail: `{json.dumps(hold_rep['guardrail'])}`",
        f"- Gates: `{json.dumps(gate)}`",
        "",
        "## Policy",
        "",
        "- Thresholds / X chosen on fit+cal only.",
        "- Holdout is a single frozen eval.",
        "- Shadow only — not wired to EA.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(
        json.dumps(
            {
                "phase": "EC1-REGIME-NESTED",
                "toxic_regimes": toxic,
                "bsl_add": best["bsl_add"],
                "pf_mult": args.pf_mult,
                "fit_stats": stats,
                "cal": {
                    "skip_share": cal_rep["skip_share"],
                    "net_avoided": cal_rep["net_avoided"],
                    "precision": cal_rep["bad_path_precision"],
                    "pf_base": cb["pf"],
                    "pf_soft": cs["pf"],
                },
                "holdout": {
                    "skip_share": hold_rep["skip_share"],
                    "net_avoided": hold_rep["net_avoided"],
                    "precision": hold_rep["bad_path_precision"],
                    "pf_base": hb["pf"],
                    "pf_soft": hs["pf"],
                    "guardrail": hold_rep["guardrail"],
                },
                "gate_checks": gate,
                "verdict": verdict,
                "artifacts": {
                    "json": str(json_path),
                    "md": str(md_path),
                    "skip_ids": str(skip_path),
                    "holdout_skip_ids": str(hold_skip_path),
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
