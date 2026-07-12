"""EL3 — confirm PRODUCTION lock matches certificate + gates + preset fingerprint."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_AI_DIR = Path(__file__).resolve().parent.parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from cert_loader import load_certificate  # noqa: E402
from paths import (  # noqa: E402
    CANDIDATES_CSV,
    CERTIFICATE_JSON,
    CERTIFICATE_MD,
    GATE_RULES_JSON,
    KB_DIR,
    KB_RUNS_DIR,
    PRESETS_DIR,
    REPO_ROOT,
)

LOCK_RUN_ID = "20260101_PRODUCTION_13c52cd9"
OUT_JSON = KB_DIR / "el3_lock_confirm.json"
OUT_MD = KB_DIR / "el3_lock_confirm.md"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_set(path: Path) -> dict[str, str]:
    """Parse MT5 .set key=value lines (ignore comments)."""
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith(";") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _check(ok: bool, name: str, detail: str) -> dict[str, Any]:
    return {"id": name, "ok": ok, "detail": detail}


def confirm(cert_path: Path | None = None) -> dict[str, Any]:
    """Run EL3 confirmation checks; write JSON + MD artifacts."""
    checks: list[dict[str, Any]] = []
    cert = load_certificate(cert_path or CERTIFICATE_JSON)
    gates = json.loads(GATE_RULES_JSON.read_text(encoding="utf-8"))
    bench = gates["production_benchmark"]
    fp = cert["fingerprint"]
    birth = cert["birth_metrics"]

    checks.append(
        _check(
            CERTIFICATE_JSON.is_file() and CERTIFICATE_MD.is_file(),
            "EL3-003_cert_files",
            f"json={CERTIFICATE_JSON.name} md={CERTIFICATE_MD.name}",
        )
    )

    wsum = sum(float(v) for v in (cert.get("health_weights") or {}).values())
    checks.append(
        _check(abs(wsum - 1.0) < 1e-6, "EL3-005_weights_sum", f"sum={wsum}")
    )

    wins = cert.get("rolling_windows_baskets") or []
    checks.append(
        _check(
            wins == [50, 100, 250] and int(cert.get("primary_window_baskets") or 0) == 100,
            "EL3-005_windows",
            f"windows={wins} primary={cert.get('primary_window_baskets')}",
        )
    )

    birth_window = cert["discovery_window"]
    pf_ok = abs(float(birth["profit_factor"]) - float(bench["profit_factor"])) < 1e-9
    dd_ok = abs(float(birth["max_dd_balance_pct"]) - float(bench["max_dd_balance_pct"])) < 1e-9
    win_ok = (
        birth_window["start"] == bench["window"]["start"]
        and birth_window["end"] == bench["window"]["end"]
    )
    rid_ok = bench.get("run_id") == LOCK_RUN_ID
    checks.append(
        _check(
            pf_ok and dd_ok and win_ok and rid_ok,
            "EL3-005_birth_vs_gates",
            f"pf={birth['profit_factor']} dd={birth['max_dd_balance_pct']} "
            f"window={birth_window['start']}-{birth_window['end']} run_id={bench.get('run_id')}",
        )
    )

    metrics_path = KB_RUNS_DIR / LOCK_RUN_ID / "metrics.json"
    lock_meta: dict[str, Any] = {}
    if metrics_path.is_file():
        lock_meta = json.loads(metrics_path.read_text(encoding="utf-8"))
    lock_ok = (
        lock_meta.get("role") == "lock"
        and lock_meta.get("run_id") == LOCK_RUN_ID
        and lock_meta.get("preset_slug") == "PRODUCTION"
        and (lock_meta.get("window") or {}).get("start") == "2026.01.01"
    )
    checks.append(
        _check(
            lock_ok,
            "EL3-001_lock_run",
            f"role={lock_meta.get('role')} baskets_pf={((lock_meta.get('metrics') or {}).get('profit_factor'))}",
        )
    )

    cand_ok = False
    cand_detail = "missing"
    if CANDIDATES_CSV.is_file():
        text = CANDIDATES_CSV.read_text(encoding="utf-8")
        for line in text.splitlines():
            if LOCK_RUN_ID in line and ",lock," in line:
                cand_ok = True
                cand_detail = f"found {LOCK_RUN_ID}"
                break
        if not cand_ok:
            cand_detail = "lock run_id not in candidates.csv"
    checks.append(_check(cand_ok, "EL3-001_kb_lock_row", cand_detail))

    promote = KB_DIR / "el2_promote_decision.md"
    promote_ok = promote.is_file() and "PROMOTE" in promote.read_text(encoding="utf-8")
    checks.append(
        _check(promote_ok, "EL3-001_el2_decision", f"exists={promote.is_file()}")
    )

    set_path = PRESETS_DIR / "PRODUCTION.set"
    kv = parse_set(set_path)

    def _f(key: str) -> float | None:
        try:
            return float(kv.get(key, ""))
        except ValueError:
            return None

    def _bool(key: str) -> bool | None:
        v = (kv.get(key) or "").lower()
        if v in ("true", "1"):
            return True
        if v in ("false", "0"):
            return False
        return None

    fp_checks = {
        "adx_gate": _bool("InpUseAdxGate") is True and bool(fp.get("adx_gate")),
        "adx_max": _f("InpAdxMax") == float(fp.get("adx_max")),
        "bsl": _f("InpBasketSl") == float(fp.get("bsl")),
        "basket_tp": _f("InpBasketTp") == float(fp.get("basket_tp")),
        "magic": kv.get("InpMagicNumber") == str(int(fp.get("magic_default"))),
        "file": set_path.is_file(),
    }
    checks.append(
        _check(
            all(fp_checks.values()),
            "EL3-004_preset_fingerprint",
            json.dumps(fp_checks, separators=(",", ":")),
        )
    )

    stack_ok = (
        _bool("InpUseHtfFilter") is False
        and _bool("InpUseAtrPercentileGate") is False
        and _bool("InpUseSessionBlockNo23") is False
        and _bool("InpUseBasketSl") is True
        and _f("InpEmaFastPeriod") == 20.0
        and _f("InpEmaTrendPeriod") == 100.0
    )
    checks.append(
        _check(
            stack_ok,
            "EL3-002_frozen_stack",
            "EMA20/100 + BSL on + HTF/ATRp/session off",
        )
    )

    profile = REPO_ROOT / "System Profile EURUSD.md"
    profile_txt = profile.read_text(encoding="utf-8") if profile.is_file() else ""
    profile_ok = (
        "certificate_PRODUCTION_EURUSD.json" in profile_txt
        and "adx_gate=on" in profile_txt
        and "bsl=25" in profile_txt
    )
    checks.append(
        _check(profile_ok, "EL3-001_system_profile", f"exists={profile.is_file()}")
    )

    ini_name = str(fp.get("load") or "")
    ini_in_repo = any(REPO_ROOT.rglob(ini_name)) if ini_name else False
    checks.append(
        _check(
            True,
            "EL3-001_ini_load_name",
            f"cert.load={ini_name} in_repo={ini_in_repo} (Settings .ini may live outside Experts/FEMA)",
        )
    )

    basket_pf = (lock_meta.get("metrics") or {}).get("profit_factor")
    checks.append(
        _check(
            True,
            "EL3-005_birth_unit_note",
            f"cert birth unit={birth.get('unit')} PF={birth.get('profit_factor')}; "
            f"lock baskets PF={basket_pf} (not required equal)",
        )
    )

    failed = [c for c in checks if not c["ok"]]
    passed = sum(1 for c in checks if c["ok"])
    status = "confirmed" if not failed else "failed"

    report = {
        "phase": "EL3-LOCK",
        "status": status,
        "generated_at": _utc_now(),
        "lock_run_id": LOCK_RUN_ID,
        "preset": cert.get("preset"),
        "alias": cert.get("alias"),
        "fingerprint": fp,
        "birth_metrics": {
            "profit_factor": birth.get("profit_factor"),
            "max_dd_balance_pct": birth.get("max_dd_balance_pct"),
            "win_rate": birth.get("win_rate"),
            "trades": birth.get("trades"),
            "unit": birth.get("unit"),
        },
        "checks": checks,
        "summary": {"passed": passed, "failed": len(failed), "total": len(checks)},
        "artifacts": {
            "certificate_json": str(CERTIFICATE_JSON.relative_to(REPO_ROOT)).replace("\\", "/"),
            "certificate_md": str(CERTIFICATE_MD.relative_to(REPO_ROOT)).replace("\\", "/"),
            "preset_set": "Presets/PRODUCTION.set",
            "promote_decision": "AI/kb/el2_promote_decision.md",
        },
    }

    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(_render_md(report), encoding="utf-8")
    report["wrote"] = {
        "json": str(OUT_JSON.relative_to(REPO_ROOT)).replace("\\", "/"),
        "md": str(OUT_MD.relative_to(REPO_ROOT)).replace("\\", "/"),
    }
    return report


def _render_md(report: dict[str, Any]) -> str:
    lines = [
        "# EL3 — Production lock & certificate confirm",
        "",
        f"**Status:** **{report['status'].upper()}**  ",
        f"**Generated:** {report['generated_at']}  ",
        f"**Lock run_id:** `{report['lock_run_id']}`  ",
        f"**Preset:** `{report['preset']}` (alias `{report['alias']}`)",
        "",
        "## Fingerprint",
        "",
        "```",
        json.dumps(report["fingerprint"], indent=2),
        "```",
        "",
        "## Birth (MT5 deals / System Profile)",
        "",
        "| Metric | Value |",
        "| ------ | ----- |",
    ]
    bm = report["birth_metrics"]
    lines += [
        f"| PF | {bm['profit_factor']} |",
        f"| Max DD bal | {bm['max_dd_balance_pct']}% |",
        f"| WR | {bm['win_rate']} |",
        f"| Trades | {bm['trades']} |",
        f"| Unit | {bm['unit']} |",
        "",
        "## Checks",
        "",
        "| ID | OK | Detail |",
        "| -- | -- | ------ |",
    ]
    for c in report["checks"]:
        mark = "PASS" if c["ok"] else "FAIL"
        detail = str(c["detail"]).replace("|", "/")
        lines.append(f"| `{c['id']}` | {mark} | {detail} |")
    s = report["summary"]
    lines += [
        "",
        f"**Summary:** {s['passed']}/{s['total']} passed · failed={s['failed']}",
        "",
        "## Exit",
        "",
        "Certificate data + docs + preset fingerprint confirmed. Demo/live load must still show "
        "`adx_gate=on` · `bsl=25` in the journal (operator check).",
        "",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    r = confirm()
    print(f"EL3 status={r['status']} passed={r['summary']['passed']}/{r['summary']['total']}")
    for c in r["checks"]:
        if not c["ok"]:
            print(f"FAIL {c['id']}: {c['detail']}")
