"""EL2 — evaluate candidates against gate_rules.json (G1 primary)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_AI_DIR = Path(__file__).resolve().parent.parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from paths import GATE_RULES_JSON, KB_DIR  # noqa: E402

SEED = KB_DIR / "discovery_rows_seed.json"


def load_gates(path: Path | None = None) -> dict[str, Any]:
    return json.loads((path or GATE_RULES_JSON).read_text(encoding="utf-8"))


def _dd(row: dict[str, Any]) -> float | None:
    v = row.get("dd")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def eval_g1(row: dict[str, Any], gates: dict[str, Any] | None = None) -> dict[str, Any]:
    """G1: PF >= PRODUCTION and DD <= PRODUCTION on same canonical window."""
    g = gates or load_gates()
    bench = g["production_benchmark"]
    pf = float(row["pf"]) if row.get("pf") is not None else None
    dd = _dd(row)
    bpf = float(bench["profit_factor"])
    bdd = float(bench["max_dd_balance_pct"])

    # Stale-slice demotion: non-canonical window cannot promote
    start = str(row.get("window_start") or "")
    end = str(row.get("window_end") or "")
    canon_s = bench["window"]["start"]
    canon_e = bench["window"]["end"]
    same_window = start == canon_s and end == canon_e
    symbol_ok = str(row.get("symbol") or "EURUSD") == str(bench["symbol"])

    checks = {
        "same_window": same_window,
        "same_symbol": symbol_ok,
        "pf_ge_production": pf is not None and pf + 1e-12 >= bpf,
        "dd_le_production": dd is not None and dd <= bdd + 1e-9,
    }
    stale = not same_window
    g1_pass = (
        checks["same_window"]
        and checks["same_symbol"]
        and checks["pf_ge_production"]
        and checks["dd_le_production"]
    )

    reason = ""
    if not symbol_ok:
        reason = "other"  # cross-symbol → G3 lane
    elif stale:
        reason = "other"  # stale_slice
    elif pf is not None and pf + 1e-12 < bpf and dd is not None and dd > bdd:
        reason = "pf_breach"  # both fail; prefer pf tag if PF is the headline miss
        if dd - bdd >= (bpf - pf):
            reason = "dd_breach"
    elif pf is not None and pf + 1e-12 < bpf:
        reason = "pf_breach"
    elif dd is not None and dd > bdd:
        reason = "dd_breach"

    return {
        "gate": "G1",
        "pass": g1_pass,
        "stale_slice": stale,
        "checks": checks,
        "candidate": {"pf": pf, "dd": dd, "symbol": row.get("symbol") or "EURUSD"},
        "benchmark": {"pf": bpf, "dd": bdd},
        "failure_reason": "" if g1_pass else reason,
        "notes": (
            "stale_slice_demote"
            if stale
            else ("g1_pass" if g1_pass else f"g1_fail:{reason}")
        ),
    }


def classify_row(row: dict[str, Any], gates: dict[str, Any] | None = None) -> dict[str, Any]:
    """Map Discovery seed row → KB status + failure_reason."""
    g = gates or load_gates()
    status_raw = str(row.get("status") or "").lower()
    row_n = int(row["row"])

    if row_n == 22:
        return {
            "status": "lock",
            "failure_reason": "",
            "g1": eval_g1(row, g),
            "decision": "promote_locked",
        }

    # G3 cross-symbol
    if str(row.get("symbol") or "EURUSD") != "EURUSD" or "g3" in status_raw:
        return {
            "status": "reject",
            "failure_reason": "other",
            "g1": eval_g1(row, g),
            "decision": "g3_fail",
        }

    g1 = eval_g1(row, g)
    if g1["stale_slice"]:
        return {
            "status": "reject",
            "failure_reason": "other",
            "g1": g1,
            "decision": "demote_stale_slice",
        }

    if "inert" in status_raw or "control" in status_raw:
        return {
            "status": "reject" if "inert" in status_raw else "control",
            "failure_reason": "" if "control" in status_raw else "other",
            "g1": g1,
            "decision": "inert_or_control",
        }

    if g1["pass"]:
        # Would be promote candidate — none besides lock on this table
        return {
            "status": "candidate",
            "failure_reason": "",
            "g1": g1,
            "decision": "g1_pass_not_promoted",
        }

    # Tag regime/session from notes when G1 fails
    notes = str(row.get("notes") or "").lower() + " " + str(row.get("preset") or "").lower()
    fr = g1["failure_reason"] or "other"
    if any(k in notes for k in ("atr", "adx", "htf", "ema sep", "regime", "slope", "breakout")):
        if "ses_" in notes or "session" in notes or "fri" in notes or "sun" in notes:
            pass
        else:
            fr = "regime"
    if any(k in notes for k in ("ses_", "session", "fri", "sun", "ldn", "whitelist")):
        fr = "session" if "dd" not in (g1["failure_reason"] or "") else g1["failure_reason"]

    # Alternates that beat PF but fail DD stay candidate with dd_breach
    if "alternate" in status_raw or "prev" in status_raw or "near" in status_raw:
        return {
            "status": "candidate",
            "failure_reason": g1["failure_reason"] or "dd_breach",
            "g1": g1,
            "decision": "alternate_g1_fail",
        }

    return {
        "status": "reject",
        "failure_reason": fr,
        "g1": g1,
        "decision": "reject",
    }


def polish_kb(
    seed_path: Path | None = None,
    out_csv: Path | None = None,
    out_json: Path | None = None,
) -> dict[str, Any]:
    """Rewrite candidates.csv + el2_gate_scorecard.json from Discovery seed."""
    import csv

    seed_path = seed_path or SEED
    out_csv = out_csv or (KB_DIR / "candidates.csv")
    out_json = out_json or (KB_DIR / "el2_gate_scorecard.json")
    gates = load_gates()
    rows = json.loads(seed_path.read_text(encoding="utf-8"))
    map_path = KB_DIR / "discovery_run_ids.json"
    run_map = {}
    if map_path.is_file():
        run_map = {
            int(r["row"]): r["run_id"]
            for r in json.loads(map_path.read_text(encoding="utf-8")).get("rows") or []
        }

    scorecard = []
    csv_rows = []
    for row in rows:
        cls = classify_row(row, gates)
        rid = run_map.get(int(row["row"]), "")
        scorecard.append(
            {
                "row": int(row["row"]),
                "preset": row["preset"],
                "run_id": rid,
                "status": cls["status"],
                "failure_reason": cls["failure_reason"],
                "decision": cls["decision"],
                "g1": cls["g1"],
            }
        )
        csv_rows.append(
            {
                "id": str(row["preset"]).replace("/", "_"),
                "parent": "PRODUCTION" if int(row["row"]) != 22 else "",
                "subsystem": "",
                "diffs": str(row.get("notes") or "")[:80],
                "window": f"{row.get('window_start')}-{row.get('window_end')}",
                "symbol": row.get("symbol") or "EURUSD",
                "pf": row.get("pf"),
                "wr": (float(row["wr"]) / 100.0) if row.get("wr") is not None else "",
                "dd": row.get("dd"),
                "status": cls["status"],
                "failure_reason": cls["failure_reason"],
                "run_id": rid,
                "notes": f"EL2 row {row['row']}; {cls['decision']}",
            }
        )

    # Keep factory smoke row
    csv_rows.append(
        {
            "id": "Candidate_X1",
            "parent": "PRODUCTION",
            "subsystem": "session",
            "diffs": "InpUseSessionBlockNo23:false->true",
            "window": "",
            "symbol": "EURUSD",
            "pf": "",
            "wr": "",
            "dd": "",
            "status": "queued",
            "failure_reason": "",
            "run_id": "",
            "notes": "INF-PRESET factory smoke",
        }
    )

    fields = [
        "id",
        "parent",
        "subsystem",
        "diffs",
        "window",
        "symbol",
        "pf",
        "wr",
        "dd",
        "status",
        "failure_reason",
        "run_id",
        "notes",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in csv_rows:
            w.writerow({k: r.get(k, "") for k in fields})

    summary = {
        "lock": sum(1 for s in scorecard if s["status"] == "lock"),
        "candidate": sum(1 for s in scorecard if s["status"] == "candidate"),
        "reject": sum(1 for s in scorecard if s["status"] == "reject"),
        "control": sum(1 for s in scorecard if s["status"] == "control"),
        "g1_pass": sum(1 for s in scorecard if s["g1"]["pass"]),
        "stale_demoted": sum(1 for s in scorecard if s["decision"] == "demote_stale_slice"),
    }
    out = {
        "phase": "EL2-GATE",
        "benchmark": gates["production_benchmark"],
        "summary": summary,
        "rows": scorecard,
    }
    out_json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out
