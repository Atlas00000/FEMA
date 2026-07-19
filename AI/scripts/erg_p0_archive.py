"""ERG-P0: archive P1 2021-2025 agent CSVs + build loser atlas."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

AGENT = Path(
    r"C:\Users\emili\AppData\Roaming\MetaQuotes\Tester"
    r"\158041E5204719DC59E8E86EAAE9D56B\Agent-127.0.0.1-3000\MQL5\Files\FEMA_AI"
)
AI = Path(__file__).resolve().parent.parent
OUT = AI / "data" / "erg" / "p0_p1_baseline_2021_2025"


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def fnum(x, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def load_baskets(path: Path) -> tuple[list[str], list[dict]]:
    raw = path.read_text(encoding="utf-8", errors="replace").splitlines()
    lines = [ln for ln in raw if ln.strip() and not ln.startswith("#")]
    reader = csv.DictReader(lines)
    return list(reader.fieldnames or []), list(reader)


def sum_by(meta: list[dict], key: str) -> list[tuple]:
    d: dict = defaultdict(float)
    c: Counter = Counter()
    for m in meta:
        k = m[key]
        d[k] += m["profit"]
        c[k] += 1
    return sorted(((k, round(d[k], 2), c[k]) for k in d), key=lambda x: x[1])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    src_b = AGENT / "EURUSD_20260707_baskets.csv"
    src_e = AGENT / "EURUSD_20260707_events.csv"
    src_m = AGENT / "EURUSD_20260707_run.meta.txt"
    src_c = AGENT / "EURUSD_20260707_run_config.json"

    (OUT / "P1-BASELINE_2021_2025_baskets.csv").write_bytes(src_b.read_bytes())
    (OUT / "P1-BASELINE_2021_2025_events.csv").write_bytes(src_e.read_bytes())
    (OUT / "run.meta.txt").write_bytes(src_m.read_bytes())
    (OUT / "run_config.json").write_bytes(src_c.read_bytes())

    _, rows = load_baskets(src_b)
    profits = [fnum(r.get("profit")) for r in rows]
    wins = [p for p in profits if p > 0]
    losses_p = [p for p in profits if p < 0]
    loss_rows = sorted(
        [r for r in rows if fnum(r.get("profit")) < 0],
        key=lambda r: fnum(r.get("profit")),
    )

    atlas = []
    for r in loss_rows[:15]:
        od = parse_dt(r.get("open_time"))
        cd = parse_dt(r.get("close_time"))
        atlas.append(
            {
                "basket_id": r.get("basket_id"),
                "profit": round(fnum(r.get("profit")), 2),
                "mae": round(fnum(r.get("mae")), 2),
                "mfe": round(fnum(r.get("mfe")), 2),
                "max_depth": int(fnum(r.get("max_depth"))),
                "bars_alive": int(fnum(r.get("bars_alive"))),
                "exit_reason": r.get("exit_reason"),
                "direction": r.get("direction"),
                "open_time": r.get("open_time"),
                "close_time": r.get("close_time"),
                "open_hour": od.hour if od else None,
                "close_hour": cd.hour if cd else None,
                "open_dow": od.strftime("%a") if od else None,
                "close_dow": cd.strftime("%a") if cd else None,
                "open_month": od.strftime("%Y-%m") if od else None,
                "close_month": cd.strftime("%Y-%m") if cd else None,
                "adx": round(fnum(r.get("adx")), 2),
                "atr": round(fnum(r.get("atr")), 5),
            }
        )

    loss_meta = []
    for r in loss_rows:
        cd = parse_dt(r.get("close_time"))
        loss_meta.append(
            {
                "profit": fnum(r.get("profit")),
                "close_hour": cd.hour if cd else None,
                "close_dow": cd.strftime("%a") if cd else None,
                "close_month": cd.month if cd else None,
                "max_depth": int(fnum(r.get("max_depth"))),
                "bars_alive": int(fnum(r.get("bars_alive"))),
            }
        )

    bars = [m["bars_alive"] for m in loss_meta] or [0]
    summary = {
        "erg_task": "ERG-P0-02/03",
        "source_agent": str(src_b),
        "archived_to": str(OUT).replace("\\", "/"),
        "n_baskets": len(rows),
        "n_losses": len(loss_rows),
        "net": round(sum(profits), 2),
        "pf_baskets": round(sum(wins) / abs(sum(losses_p)), 4) if losses_p else None,
        "wr": round(len(wins) / len(profits), 4) if profits else None,
        "avg_win": round(sum(wins) / len(wins), 2) if wins else None,
        "avg_loss": round(sum(losses_p) / len(losses_p), 2) if losses_p else None,
        "window_from_data": {
            "first_open": rows[0].get("open_time") if rows else None,
            "last_close": rows[-1].get("close_time") if rows else None,
        },
        "config_note": (
            "Agent meta preset_id=PRODUCTION but InpUseBasketSl=false "
            "InpUseAdxGate=false (= P1-BASELINE stack). Treat as P1 telemetry."
        ),
        "mt5_report_deals": 687,
        "mismatch_note": (
            "MT5 Backtest Report counts deals (687); FEMA baskets CSV counts "
            "baskets — inequality expected."
        ),
        "coverage_note": (
            "Compare basket net/PF to MT5 deal report; if sparse, re-run P1 with "
            "InpUseAiEventLog=true for full 2021-2025 and re-sync."
        ),
        "worst15": atlas,
        "loss_by_close_hour": [
            {"hour": h, "pnl": p, "n": n} for h, p, n in sum_by(loss_meta, "close_hour")
        ],
        "loss_by_close_dow": [
            {"dow": d, "pnl": p, "n": n} for d, p, n in sum_by(loss_meta, "close_dow")
        ],
        "loss_by_close_month": [
            {"month": m, "pnl": p, "n": n}
            for m, p, n in sum_by(loss_meta, "close_month")
        ],
        "loss_depth_counts": dict(Counter(m["max_depth"] for m in loss_meta)),
        "loss_bars_alive": {
            "min": min(bars),
            "median": sorted(bars)[len(bars) // 2],
            "max": max(bars),
        },
    }
    (OUT / "loser_atlas.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: summary[k] for k in (
        "n_baskets", "n_losses", "net", "pf_baskets", "wr", "avg_win", "avg_loss",
        "window_from_data", "loss_bars_alive"
    )}, indent=2))
    print("worst15 profits:", [a["profit"] for a in atlas])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
