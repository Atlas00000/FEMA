"""ASCII-safe CLI: python -m fema_ops health|ingest|weekly"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parent.parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))


def cmd_health(args: argparse.Namespace) -> int:
    from fema_ops.health import ascii_summary, run_health

    report = run_health(
        baskets_path=Path(args.baskets) if args.baskets else None,
        events_path=Path(args.events) if args.events else None,
        cert_path=Path(args.cert) if args.cert else None,
        update_state=not args.no_state,
    )
    print(ascii_summary(report))
    arts = report.get("artifacts") or {}
    if arts.get("json"):
        print(f"wrote {arts['json']}")
    if arts.get("md"):
        print(f"wrote {arts['md']}")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    from fema_ops.ingest import run_ingest

    return run_ingest(
        source=args.source,
        magic=args.magic or "",
        from_dir=args.from_dir,
        allow_empty=args.allow_empty,
    )


def cmd_pipeline(args: argparse.Namespace) -> int:
    from fema_ops.pipeline import run_pipeline

    report = run_pipeline(
        source=args.source,
        allow_empty=True,
        with_db=bool(args.with_db),
        with_ci=bool(args.with_ci),
        with_archive=not args.no_archive,
    )
    print(
        f"pipeline ok={report.get('ok')} rows={report.get('basket_rows')} "
        f"health_ran={report.get('health_ran')} failed={report.get('failed')}"
    )
    for s in report.get("steps") or []:
        flag = "SKIP" if s.get("skipped") else ("OK" if s.get("ok") else "FAIL")
        extra = s.get("reason") or s.get("error") or ""
        print(f"  [{flag}] {s.get('name')} {extra}".rstrip())
    for n in report.get("notes") or []:
        print(f"note: {n}")
    print(f"wrote {report.get('artifact')}")
    return 0 if report.get("ok") else 1


def cmd_weekly(_args: argparse.Namespace) -> int:
    from fema_ops.health import ascii_summary, run_health

    report = run_health(update_state=True)
    print(ascii_summary(report))
    print("--- weekly checklist ---")
    print("1. Confirm ladder vs demo feel")
    print("2. Note certificate breaches (components <55)")
    print("3. Default action: do nothing unless persistence warning_active=1")
    print("4. Template: AI/templates/weekly_edge_review.md (ESR-W06)")
    return 0


def cmd_register(args: argparse.Namespace) -> int:
    from fema_ops.runs import ascii_run_line, register_run

    rec = register_run(
        Path(args.baskets),
        preset=args.preset,
        role=args.role,
        window_start=args.window_from,
        window_end=args.window_to,
        symbol=args.symbol,
        timeframe=args.timeframe,
        notes=args.notes or "",
        meta_path=Path(args.meta) if args.meta else None,
    )
    print(ascii_run_line(rec))
    print(f"wrote AI/kb/runs/{rec['run_id']}/")
    return 0


def cmd_list_runs(_args: argparse.Namespace) -> int:
    from fema_ops.runs import ascii_run_line, list_runs

    rows = list_runs()
    if not rows:
        print("no runs registered")
        return 0
    for r in rows:
        print(ascii_run_line(r))
    print(f"n={len(rows)}")
    return 0


def cmd_clone(args: argparse.Namespace) -> int:
    from fema_ops.presets import clone_preset, list_subsystems, parse_set_args

    if args.list_subsystems:
        print(" ".join(list_subsystems()))
        return 0
    overrides = parse_set_args(args.set or [])
    try:
        rec = clone_preset(
            candidate_id=args.id,
            subsystem=args.subsystem,
            overrides=overrides,
            parent_id=args.parent,
            notes=args.notes or "",
            status=args.status,
            allow_multi=args.allow_multi,
        )
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        print(f"clone_fail: {exc}")
        return 1
    print(
        f"cloned id={rec['id']} subsystem={rec['subsystem']} "
        f"diff={rec['diff_summary']}"
    )
    print(f"wrote {rec['file']}")
    print("kb=AI/kb/candidates.csv manifest=Presets/manifest.json")
    return 0


def cmd_list_presets(_args: argparse.Namespace) -> int:
    from fema_ops.presets import load_manifest

    man = load_manifest()
    for p in man.get("presets") or []:
        print(
            f"{p.get('id')} status={p.get('status')} "
            f"parent={p.get('parent') or '-'} "
            f"sub={p.get('subsystem') or '-'} "
            f"| {p.get('diff_summary') or ''}"
        )
    print(f"n={len(man.get('presets') or [])}")
    return 0


def cmd_pause_check(args: argparse.Namespace) -> int:
    from fema_ops.pause_check import backfill_pause_check

    out = backfill_pause_check(
        Path(args.baskets) if args.baskets else None,
        step=int(args.step),
    )
    print(
        f"pause_check status={out['status']} rate={out.get('pause_rate')} "
        f"ok_not_always_on={out.get('ok_not_always_on')} "
        f"n={out.get('n_snapshots')}"
    )
    if out.get("artifact"):
        print(f"wrote {out['artifact']}")
    return 0 if out.get("ok_not_always_on") in (True, None) else 2


def cmd_pause_flag(args: argparse.Namespace) -> int:
    from paths import PAUSE_FLAG_LIVE
    from fema_ops.health import run_health
    from fema_ops.pause import write_flag_file

    report = run_health(update_state=not args.no_state)
    pause = bool(report.get("would_pause_new"))
    reason = (report.get("pause") or {}).get("reason", "")
    if args.force_off:
        pause = False
        reason = "human_force_off"
    if args.force_on:
        pause = True
        reason = reason or "human_force_on"
    write_flag_file(
        PAUSE_FLAG_LIVE,
        pause,
        reason=reason,
        source="health_shadow" if not (args.force_on or args.force_off) else "human",
    )
    print(f"pause_new={int(pause)} reason={reason} wrote {PAUSE_FLAG_LIVE}")
    print("Copy to MT5 Files\\\\FEMA_AI\\\\pause_new.flag only if InpReadPauseNewFlag=true")
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    from fema_ops.status import write_status

    data = write_status()
    h = data["health"]
    print(
        f"STATUS phase={data['phase']} health={h.get('score')} "
        f"ladder={h.get('ladder')} run={data['runs'].get('lock_run_id')} "
        f"esr={data['open_esr']}"
    )
    arts = data.get("artifacts") or {}
    if arts.get("md"):
        print(f"wrote {arts['md']}")
    return 0


def cmd_backfill_discovery(_args: argparse.Namespace) -> int:
    from fema_ops.discovery_backfill import backfill

    out = backfill()
    print(
        f"backfill rows={out['created_or_linked']} new_index={out['new_index_rows']}"
    )
    print(f"wrote AI/kb/discovery_run_ids.json")
    return 0


def cmd_gate_polish(_args: argparse.Namespace) -> int:
    from fema_ops.gates import polish_kb

    out = polish_kb()
    s = out["summary"]
    print(
        f"EL2 scorecard lock={s['lock']} candidate={s['candidate']} "
        f"reject={s['reject']} control={s['control']} "
        f"g1_pass={s['g1_pass']} stale_demoted={s['stale_demoted']}"
    )
    print("wrote AI/kb/el2_gate_scorecard.json")
    print("wrote AI/kb/candidates.csv")
    return 0


def cmd_gate_check(args: argparse.Namespace) -> int:
    from fema_ops.gates import eval_g1, load_gates

    row = {
        "pf": args.pf,
        "dd": args.dd,
        "window_start": args.window_from,
        "window_end": args.window_to,
        "symbol": args.symbol,
    }
    r = eval_g1(row, load_gates())
    print(
        f"G1 pass={int(r['pass'])} stale={int(r['stale_slice'])} "
        f"reason={r['notes']} pf={r['candidate']['pf']} dd={r['candidate']['dd']}"
    )
    return 0 if r["pass"] else 1


def cmd_cert_confirm(_args: argparse.Namespace) -> int:
    from fema_ops.lock_confirm import confirm

    r = confirm()
    print(
        f"EL3 status={r['status']} passed={r['summary']['passed']}/{r['summary']['total']} "
        f"lock={r['lock_run_id']}"
    )
    for c in r["checks"]:
        if not c["ok"]:
            print(f"FAIL {c['id']}: {c['detail']}")
    print(f"wrote {r['wrote']['md']}")
    return 0 if r["status"] == "confirmed" else 1


def cmd_observatory(_args: argparse.Namespace) -> int:
    from fema_ops.observatory import write_observatory

    r = write_observatory()
    c = r.get("compatibility") or {}
    print(
        f"observatory action={r['action']} source={r['source']} "
        f"health={r['health'].get('score')} ladder={r['health'].get('ladder')} "
        f"compat={c.get('signal')}"
    )
    print(f"wrote {r['wrote']['md']}")
    return 0


def cmd_fingerprint(args: argparse.Namespace) -> int:
    from fema_ops.fingerprint import write_fingerprint

    out = write_fingerprint(
        baskets=Path(args.baskets) if args.baskets else None,
        window=args.window,
        run_id=args.run_id,
        attach_run=not args.no_attach,
    )
    fp = out["fingerprint"]
    c = out["compatibility"]
    print(
        f"fingerprint n={fp['window'].get('n_baskets')} "
        f"adx_lt30={((fp.get('regime') or {}).get('adx_lt_30_share'))} "
        f"depth={((fp.get('pullback') or {}).get('avg_depth'))} "
        f"compat={c.get('signal')} score={c.get('score')}"
    )
    arts = out.get("artifacts") or {}
    for k, v in arts.items():
        if v:
            print(f"wrote {k}={v}")
    return 0


def cmd_recommend(_args: argparse.Namespace) -> int:
    from fema_ops.factory import write_recommend

    r = write_recommend()
    n = len(r.get("cloneable") or [])
    print(
        f"recommend compat={r.get('compat_signal')} cloneable={n} "
        f"subs={[s.get('subsystem') for s in (r.get('cloneable') or [])]}"
    )
    for s in r.get("suggestions") or []:
        flag = "clone" if s.get("cloneable") else "note"
        print(f"  [{flag}] {s.get('subsystem')}: {s.get('hypothesis') or s.get('reason')}")
    print(f"wrote {r.get('artifact')}")
    return 0


def cmd_factory(args: argparse.Namespace) -> int:
    from fema_ops.factory import propose_clone

    try:
        out = propose_clone(
            subsystem=args.subsystem,
            hypothesis=args.hypothesis or "",
            index=args.index,
            dry_run=not args.apply,
            candidate_id=args.id,
            parent=args.parent,
        )
    except Exception as e:  # noqa: BLE001
        print(f"factory_fail: {e}")
        return 1
    if not out.get("ok"):
        print(f"factory skip: {out.get('reason')}")
        return 0
    mode = "APPLY" if args.apply else "dry_run"
    print(
        f"factory {mode} subsystem={out.get('subsystem')} "
        f"set={out.get('set_args')} hyp={out.get('hypothesis')}"
    )
    if out.get("cloned"):
        c = out["cloned"]
        print(f"cloned id={c['id']} file={c['file']}")
    return 0


def cmd_asi_build(args: argparse.Namespace) -> int:
    from paths import KB_DIR, LATEST_BASKETS

    from fema_ops.asi.dataset import build_asi_dataset, write_asi_build_report

    default_baskets = _AI_DIR / "data" / "EURUSD_baskets_2020_2025_uid.csv"
    if not default_baskets.is_file():
        alt = _AI_DIR / "data" / "EURUSD_baskets_2020_2025.csv"
        default_baskets = alt if alt.is_file() else default_baskets

    baskets = Path(args.baskets) if args.baskets else default_baskets
    if not baskets.is_file():
        print(f"asi_build_fail: baskets not found: {baskets}", file=sys.stderr)
        return 1

    promote = Path(args.promote_baskets) if args.promote_baskets else LATEST_BASKETS
    if args.no_promote:
        promote = None

    out_dir = Path(args.out_dir) if args.out_dir else KB_DIR / "asi"
    try:
        report = build_asi_dataset(
            baskets_path=baskets,
            out_dir=out_dir,
            promote_baskets_path=promote,
            split_profile=args.split_profile,
            skip_quantile=float(args.skip_quantile),
        )
    except Exception as e:  # noqa: BLE001
        print(f"asi_build_fail: {e}", file=sys.stderr)
        return 1

    md = write_asi_build_report(report)
    (out_dir / "asi_build_report.md").write_text(md, encoding="utf-8")
    print(md)
    for k, v in (report.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    return 0


def cmd_asi_train(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.tep import train_tep, write_tep_train_report

    asi_dir = Path(args.asi_dir) if args.asi_dir else KB_DIR / "asi"
    try:
        report = train_tep(
            asi_dir=asi_dir,
            max_skip=float(args.max_skip),
            strict=bool(args.strict),
            guardrail=bool(args.guardrail),
        )
    except Exception as e:  # noqa: BLE001
        print(f"asi_train_fail: {e}", file=sys.stderr)
        return 1

    md = write_tep_train_report(report)
    (asi_dir / "tep_train_report.md").write_text(md, encoding="utf-8")
    print(md)
    for k, v in (report.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    return 0


def cmd_asi_export_gate(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.gate import export_tep_gate

    asi_dir = Path(args.asi_dir) if args.asi_dir else KB_DIR / "asi"
    try:
        report = export_tep_gate(
            asi_dir=asi_dir,
            out_name=args.out_name,
            require_guardrail_ok=not bool(args.force),
        )
    except Exception as e:  # noqa: BLE001
        print(f"asi_export_gate_fail: {e}", file=sys.stderr)
        return 1

    print(
        f"asi_export_gate ok threshold={report.get('threshold')} "
        f"n_features={report.get('n_features')} guardrail={report.get('guardrail_kill')}"
    )
    for k, v in (report.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    print(
        "copy gate to MT5 Common\\Files\\FEMA_AI\\tep_gate_v1.txt "
        "(or path in InpAiTepGateFile) before enabling InpUseAiTepGate"
    )
    return 0


def cmd_asi_mid_build(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.midbasket import build_mid_dataset

    default_baskets = _AI_DIR / "data" / "EURUSD_baskets_2018_2025.csv"
    if not default_baskets.is_file():
        default_baskets = _AI_DIR / "data" / "EURUSD_baskets_2020_2025_uid.csv"
    baskets = Path(args.baskets) if args.baskets else default_baskets
    if not baskets.is_file():
        print(f"asi_mid_build_fail: baskets not found: {baskets}", file=sys.stderr)
        return 1
    out_dir = Path(args.out_dir) if args.out_dir else KB_DIR / "asi"
    try:
        report = build_mid_dataset(
            baskets_path=baskets,
            out_dir=out_dir,
            split_profile=args.split_profile,
            min_depth=int(args.min_depth),
            max_warn=int(args.max_warn),
        )
    except Exception as e:  # noqa: BLE001
        print(f"asi_mid_build_fail: {e}", file=sys.stderr)
        return 1
    print(
        f"asi_mid_build ok mid_rows={report.get('n_mid_rows')} "
        f"steam_rate={report.get('y_mid_steamroller_rate')} "
        f"counts={report.get('counts')}"
    )
    return 0


def cmd_asi_mid_train(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.midbasket import train_mid

    asi_dir = Path(args.asi_dir) if args.asi_dir else KB_DIR / "asi"
    try:
        report = train_mid(asi_dir=asi_dir, max_skip=float(args.max_skip))
    except Exception as e:  # noqa: BLE001
        print(f"asi_mid_train_fail: {e}", file=sys.stderr)
        return 1
    cal = report.get("calibrate") or {}
    print(
        f"asi_mid_train ok thr={report.get('threshold')} "
        f"auc={report.get('auc_calibrate')} "
        f"warn_n={cal.get('skip_n')} prec={cal.get('precision')}"
    )
    for k, v in (report.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    return 0


def cmd_asi_mid_review(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.midbasket import write_mid_review

    asi_dir = Path(args.asi_dir) if args.asi_dir else KB_DIR / "asi"
    try:
        pack = write_mid_review(asi_dir)
    except Exception as e:  # noqa: BLE001
        print(f"asi_mid_review_fail: {e}", file=sys.stderr)
        return 1
    print(f"asi_mid_review: {pack.get('verdict_hint')}")
    for k, v in (pack.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    return 0


def cmd_asi_export_mid_gate(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.midbasket import export_mid_gate

    asi_dir = Path(args.asi_dir) if args.asi_dir else KB_DIR / "asi"
    try:
        report = export_mid_gate(asi_dir=asi_dir, out_name=args.out_name)
    except Exception as e:  # noqa: BLE001
        print(f"asi_export_mid_gate_fail: {e}", file=sys.stderr)
        return 1
    print(
        f"asi_export_mid_gate ok threshold={report.get('threshold')} "
        f"n_features={report.get('n_features')}"
    )
    for k, v in (report.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    print(
        "copy mid gate to MT5 Common\\Files\\FEMA_AI\\mid_gate_v1.txt "
        "(or path in InpAiMidGateFile) before enabling InpUseAiMidWarn"
    )
    return 0


def cmd_asi_mid_shadow(args: argparse.Namespace) -> int:
    from fema_ops.asi.midbasket import score_mid_baskets, score_mid_run

    try:
        if args.run_id:
            report = score_mid_run(args.run_id)
        elif args.baskets:
            report = score_mid_baskets(Path(args.baskets))
            out = Path(args.out) if args.out else Path("asi_mid_shadow_ad_hoc.json")
            out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            report.setdefault("paths", {})["ad_hoc"] = str(out)
        else:
            print("asi_mid_shadow_fail: need --run-id or --baskets", file=sys.stderr)
            return 1
    except Exception as e:  # noqa: BLE001
        print(f"asi_mid_shadow_fail: {e}", file=sys.stderr)
        return 1

    sh = report.get("shadow") or {}
    print(
        f"asi_mid_shadow ok warn_n={sh.get('warn_n')} rate={sh.get('warn_rate')} "
        f"prec={sh.get('precision_rows')} net={sh.get('net_warned_baskets')}"
    )
    for k, v in (report.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    return 0


def cmd_asi_rec_build(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.recovery import build_rec_dataset

    default_baskets = _AI_DIR / "data" / "EURUSD_baskets_2018_2025.csv"
    if not default_baskets.is_file():
        default_baskets = _AI_DIR / "data" / "EURUSD_baskets_2020_2025_uid.csv"
    baskets = Path(args.baskets) if args.baskets else default_baskets
    if not baskets.is_file():
        print(f"asi_rec_build_fail: baskets not found: {baskets}", file=sys.stderr)
        return 1
    out_dir = Path(args.out_dir) if args.out_dir else KB_DIR / "asi"
    try:
        report = build_rec_dataset(
            baskets_path=baskets,
            out_dir=out_dir,
            split_profile=args.split_profile,
            min_depth=int(args.min_depth),
            max_warn=int(args.max_warn),
        )
    except Exception as e:  # noqa: BLE001
        print(f"asi_rec_build_fail: {e}", file=sys.stderr)
        return 1
    print(
        f"asi_rec_build ok rec_rows={report.get('n_rec_rows')} "
        f"recover_rate={report.get('y_recover_rate')} "
        f"counts={report.get('counts')}"
    )
    return 0


def cmd_asi_rec_train(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.recovery import train_rec

    asi_dir = Path(args.asi_dir) if args.asi_dir else KB_DIR / "asi"
    try:
        report = train_rec(asi_dir=asi_dir, max_exit_rate=float(args.max_exit_rate))
    except Exception as e:  # noqa: BLE001
        print(f"asi_rec_train_fail: {e}", file=sys.stderr)
        return 1
    cal = report.get("calibrate") or {}
    print(
        f"asi_rec_train ok exit_thr={report.get('exit_threshold')} "
        f"auc={report.get('auc_calibrate')} "
        f"exit_n={cal.get('exit_n')} fail_prec={cal.get('fail_precision')}"
    )
    for k, v in (report.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    return 0


def cmd_asi_rec_review(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.recovery import write_rec_review

    asi_dir = Path(args.asi_dir) if args.asi_dir else KB_DIR / "asi"
    try:
        pack = write_rec_review(asi_dir)
    except Exception as e:  # noqa: BLE001
        print(f"asi_rec_review_fail: {e}", file=sys.stderr)
        return 1
    print(f"asi_rec_review: {pack.get('verdict_hint')}")
    for k, v in (pack.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    return 0


def cmd_asi_rec_shadow(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.recovery import score_rec_baskets

    if not args.baskets:
        print("asi_rec_shadow_fail: need --baskets", file=sys.stderr)
        return 1
    asi_dir = Path(args.asi_dir) if args.asi_dir else KB_DIR / "asi"
    try:
        report = score_rec_baskets(Path(args.baskets), asi_dir=asi_dir)
        out = Path(args.out) if args.out else asi_dir / "asi_rec_shadow_ad_hoc.json"
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        report.setdefault("paths", {})["ad_hoc"] = str(out)
    except Exception as e:  # noqa: BLE001
        print(f"asi_rec_shadow_fail: {e}", file=sys.stderr)
        return 1

    sh = report.get("shadow") or {}
    print(
        f"asi_rec_shadow ok exit_n={sh.get('exit_n')} rate={sh.get('exit_rate')} "
        f"fail_prec={sh.get('fail_precision_rows')} net={sh.get('net_of_exit_baskets')}"
    )
    for k, v in (report.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    return 0


def cmd_asi_regime_build(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.regime import build_regime_pack

    default_baskets = _AI_DIR / "data" / "EURUSD_baskets_2018_2025.csv"
    if not default_baskets.is_file():
        default_baskets = _AI_DIR / "data" / "EURUSD_baskets_2020_2025_uid.csv"
    baskets = Path(args.baskets) if args.baskets else default_baskets
    if not baskets.is_file():
        print(f"asi_regime_build_fail: baskets not found: {baskets}", file=sys.stderr)
        return 1
    lock = Path(args.lock_baskets) if args.lock_baskets else _AI_DIR / "data" / "live" / "latest_baskets.csv"
    if not lock.is_file():
        lock = None
    out_dir = Path(args.out_dir) if args.out_dir else KB_DIR / "asi"
    try:
        report = build_regime_pack(
            baskets_path=baskets,
            out_dir=out_dir,
            lock_baskets_path=lock,
            split_profile=args.split_profile,
            deposit=float(args.deposit),
        )
    except Exception as e:  # noqa: BLE001
        print(f"asi_regime_build_fail: {e}", file=sys.stderr)
        return 1
    ps = report.get("policy_summary") or {}
    print(
        f"asi_regime_build ok n={report.get('n_baskets')} "
        f"allow={ps.get('allow')} caution={ps.get('caution')} skip={ps.get('skip')}"
    )
    for k, v in (report.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    return 0


def cmd_asi_regime_shadow(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.regime import score_regime_shadow

    if not args.baskets:
        print("asi_regime_shadow_fail: need --baskets", file=sys.stderr)
        return 1
    asi_dir = Path(args.asi_dir) if args.asi_dir else KB_DIR / "asi"
    try:
        report = score_regime_shadow(
            Path(args.baskets),
            asi_dir=asi_dir,
            deposit=float(args.deposit),
        )
        out = Path(args.out) if args.out else asi_dir / "asi_shadow_regime.json"
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        report.setdefault("paths", {})["shadow"] = str(out)
    except Exception as e:  # noqa: BLE001
        print(f"asi_regime_shadow_fail: {e}", file=sys.stderr)
        return 1

    sh = report.get("shadow") or {}
    print(
        f"asi_regime_shadow ok skip_n={sh.get('skip_n')} rate={sh.get('skip_rate')} "
        f"steam_prec={sh.get('steamroller_precision')} net={sh.get('net_skipped')}"
    )
    for k, v in (report.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    return 0


def cmd_asi_regime_review(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.regime import write_regime_review

    asi_dir = Path(args.asi_dir) if args.asi_dir else KB_DIR / "asi"
    try:
        pack = write_regime_review(asi_dir)
    except Exception as e:  # noqa: BLE001
        print(f"asi_regime_review_fail: {e}", file=sys.stderr)
        return 1
    print(f"asi_regime_review: {pack.get('verdict_hint')}")
    for k, v in (pack.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    return 0


def cmd_asi_export_regime_gate(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.regime import export_regime_gate

    asi_dir = Path(args.asi_dir) if args.asi_dir else KB_DIR / "asi"
    try:
        report = export_regime_gate(
            asi_dir=asi_dir,
            out_name=args.out_name,
            include_caution=not args.skip_only,
        )
    except Exception as e:  # noqa: BLE001
        print(f"asi_export_regime_gate_fail: {e}", file=sys.stderr)
        return 1
    print(
        f"asi_export_regime_gate ok filters={report.get('filters')} "
        f"n={report.get('n_filters')}"
    )
    for k, v in (report.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    print(
        "copy regime gate to MT5 Common\\Files\\FEMA_AI\\regime_gate_v1.txt "
        "(or path in InpAiRegimeGateFile) before enabling InpUseAiRegimeGate"
    )
    return 0


def cmd_asi_shadow(args: argparse.Namespace) -> int:
    from fema_ops.asi.shadow import score_baskets, score_run

    try:
        if args.run_id:
            report = score_run(args.run_id, deposit=float(args.deposit))
        elif args.baskets:
            report = score_baskets(Path(args.baskets), deposit=float(args.deposit))
            out = Path(args.out) if args.out else Path("asi_shadow_ad_hoc.json")
            out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            report.setdefault("paths", {})["ad_hoc"] = str(out)
        else:
            print("asi_shadow_fail: need --run-id or --baskets", file=sys.stderr)
            return 1
    except Exception as e:  # noqa: BLE001
        print(f"asi_shadow_fail: {e}", file=sys.stderr)
        return 1

    sh = report.get("shadow") or {}
    kill = report.get("kill") or {}
    print(
        f"asi_shadow run={report.get('run_id') or 'ad_hoc'} "
        f"skip_n={sh.get('skip_n')} skip_rate={sh.get('skip_rate')} "
        f"skipped_pnl={sh.get('skipped_pnl')} "
        f"dd_all={sh.get('dd_all_pct')} dd_if_skipped={sh.get('dd_if_skipped_pct')} "
        f"kill={kill.get('status')}"
    )
    for k, v in (report.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    return 0


def cmd_asi_review(args: argparse.Namespace) -> int:
    from paths import KB_DIR

    from fema_ops.asi.shadow import (
        patch_model_card_kill,
        write_guardrail_review_pack,
        write_review_pack,
    )

    asi_dir = Path(args.asi_dir) if args.asi_dir else KB_DIR / "asi"
    try:
        if args.guardrail:
            pack = write_guardrail_review_pack(asi_dir=asi_dir)
        else:
            pack = write_review_pack(
                production_run_id=args.production_run_id,
                asi_dir=asi_dir,
            )
        patch_model_card_kill(asi_dir)
    except Exception as e:  # noqa: BLE001
        print(f"asi_review_fail: {e}", file=sys.stderr)
        return 1

    kill = pack.get("kill") or {}
    print(f"asi_review mode={'guardrail' if args.guardrail else 'production'} "
          f"kill={kill.get('status')} action={kill.get('action')}")
    if args.guardrail:
        h = pack.get("holdout") or {}
        print(
            f"holdout n={h.get('n')} skip_n={h.get('skip_n')} "
            f"precision={h.get('steamroller_precision')} "
            f"net_skipped={h.get('net_skipped')} "
            f"dd_delta={h.get('dd_delta_pct')}%"
        )
    else:
        c = pack.get("compare") or {}
        print(
            f"baseline PF={c.get('baseline_pf')} n={c.get('baseline_n')} | "
            f"kept PF={c.get('kept_pf')} n={c.get('kept_n')} | "
            f"skip_n={c.get('skip_n')} skipped_pnl={c.get('skipped_pnl')} "
            f"dd {c.get('dd_all_pct')}->{c.get('dd_if_skipped_pct')}"
        )
    print(f"verdict: {pack.get('verdict_hint')}")
    for k, v in (pack.get("paths") or {}).items():
        print(f"wrote {k}: {v}")
    return 0


def cmd_el7_dry_run(args: argparse.Namespace) -> int:
    from fema_ops.el7 import el7_dry_run

    plan = el7_dry_run(apply_lineage=bool(args.apply))
    t = plan.get("trigger") or {}
    print(
        f"el7 open_discovery={t.get('open_discovery')} reason={t.get('reason')} "
        f"ladder={t.get('ladder')} applied={plan.get('applied')}"
    )
    print(f"wrote {plan.get('artifact')}")
    return 0


def cmd_experiments(_args: argparse.Namespace) -> int:
    from fema_ops.el7 import build_experiments_index

    out = build_experiments_index()
    print(
        f"experiments n={out.get('n')} fingerprint={out.get('with_fingerprint')} "
        f"failure_reason={out.get('with_failure_reason')}"
    )
    print(f"wrote {out.get('artifact')}")
    return 0


def cmd_ci_gates(_args: argparse.Namespace) -> int:
    from fema_ops.ci_gates import run_ci_gates

    out = run_ci_gates(refresh_openapi=True)
    for name, chk in (out.get("checks") or {}).items():
        flag = "OK" if chk.get("ok") else "FAIL"
        print(f"ci_gate {flag} {name} {chk}")
    print(f"ci_gates ok={out.get('ok')}")
    return 0 if out.get("ok") else 1


def cmd_drift(_args: argparse.Namespace) -> int:
    from fema_ops.drift import detect_drift

    r = detect_drift()
    print(
        f"drift severity={r.get('severity')} n_alerts={r.get('n_alerts')} "
        f"compat={r.get('compat_signal')}"
    )
    for a in (r.get("alerts") or [])[:8]:
        print(f"  [{a.get('severity')}] {a.get('kind')}: {a.get('detail')}")
    print(f"wrote {r.get('artifact')}")
    return 0


def cmd_artifacts_list(args: argparse.Namespace) -> int:
    from fema_ops.artifacts import list_artifact_runs

    rows = list_artifact_runs(limit=args.limit)
    print(f"artifacts runs={len(rows)}")
    for r in rows:
        print(
            f"  {r['run_id']} baskets={r['has_baskets']} "
            f"bytes={r['bytes']} manifest={r['manifest']}"
        )
    return 0


def cmd_artifacts_archive(args: argparse.Namespace) -> int:
    from fema_ops.artifacts import archive_from_live

    try:
        out = archive_from_live(
            run_id=args.run_id,
            source=args.source,
            role=args.role,
            baskets=Path(args.baskets) if args.baskets else None,
        )
    except Exception as e:  # noqa: BLE001
        print(f"archive_fail: {e}")
        return 1
    print(f"archive run_id={out['run_id']} note={out['note']} dir={out['dir']}")
    return 0


def cmd_db_rehydrate(args: argparse.Namespace) -> int:
    from fema_ops.artifacts import rehydrate_run

    try:
        out = rehydrate_run(
            args.run_id,
            role=args.role,
            source=args.source,
        )
    except Exception as e:  # noqa: BLE001
        print(f"rehydrate_fail: {e}")
        return 1
    print(
        f"rehydrate run_id={out['run_id']} n={out['n_baskets']} "
        f"pf={(out.get('metrics') or {}).get('profit_factor')}"
    )
    return 0


def cmd_db_migrate(_args: argparse.Namespace) -> int:
    from fema_ops.db_store import migrate

    try:
        out = migrate()
    except Exception as e:  # noqa: BLE001
        print(f"db_migrate_fail: {e}")
        return 1
    print(f"db_migrate ok schema={out['schema']}")
    return 0


def cmd_db_ingest(args: argparse.Namespace) -> int:
    from fema_ops.db_ingest import ingest_from_incoming, ingest_from_live

    try:
        if args.from_live:
            out = ingest_from_live(source=args.source, role=args.role)
        else:
            out = ingest_from_incoming(source=args.source, role=args.role)
    except Exception as e:  # noqa: BLE001
        print(f"db_ingest_fail: {e}")
        return 1
    print(
        f"db_ingest run_id={out['run_id']} source={out['source']} "
        f"role={out['role']} n={out['n_baskets']} pf={out['metrics'].get('profit_factor')}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="fema_ops", description="FEMA offline ops (INF-OPS)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("health", help="Certificate health_v0 on latest baskets")
    h.add_argument("--baskets", default=None, help="Basket CSV (default: live/latest_baskets.csv)")
    h.add_argument("--events", default=None, help="Events CSV optional")
    h.add_argument("--cert", default=None, help="Certificate JSON")
    h.add_argument("--no-state", action="store_true", help="Do not update health_state.json")
    h.set_defaults(func=cmd_health)

    i = sub.add_parser("ingest", help="Sync Agent/Common CSVs to AI/data/live")
    i.add_argument(
        "--source",
        choices=["auto", "demo", "tester"],
        default="demo",
        help="demo=Common/Terminal (EL4 default); tester=Agent; auto=newest",
    )
    i.add_argument("--magic", default="", help="Filter magic e.g. 20260707")
    i.add_argument("--from-dir", default=None, help="Explicit FEMA_AI folder")
    i.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow header-only / empty baskets",
    )
    i.set_defaults(func=cmd_ingest)

    w = sub.add_parser("weekly", help="Health + weekly operator checklist")
    w.set_defaults(func=cmd_weekly)

    pl = sub.add_parser(
        "pipeline",
        help="Ops pipeline: ingest→health(if rows)→FP→drift→obs→status (safe if header-only)",
    )
    pl.add_argument("--source", choices=["demo", "tester", "auto"], default="demo")
    pl.add_argument("--with-db", action="store_true", help="Also db-ingest if FEMA_DATABASE_URL set")
    pl.add_argument("--with-ci", action="store_true", help="Also run ci-gates")
    pl.add_argument("--no-archive", action="store_true")
    pl.set_defaults(func=cmd_pipeline)

    r = sub.add_parser("register", help="Register a tester/demo slice (INF-RUN)")
    r.add_argument("--baskets", required=True, help="Basket outcome CSV")
    r.add_argument("--preset", required=True, help="Preset id or PRODUCTION")
    r.add_argument(
        "--role",
        default="other",
        choices=["lock", "demo", "collect", "candidate", "reject", "other"],
    )
    r.add_argument("--from", dest="window_from", default=None, help="Window start YYYY.MM.DD")
    r.add_argument("--to", dest="window_to", default=None, help="Window end YYYY.MM.DD")
    r.add_argument("--symbol", default="EURUSD")
    r.add_argument("--timeframe", default="M5")
    r.add_argument("--notes", default="")
    r.add_argument("--meta", default=None, help="Optional *_run.meta.txt for ea_run_id")
    r.set_defaults(func=cmd_register)

    lr = sub.add_parser("list-runs", help="List registered run_ids")
    lr.set_defaults(func=cmd_list_runs)

    c = sub.add_parser("clone", help="Clone PRODUCTION -> candidate (INF-PRESET)")
    c.add_argument("--id", default=None, help="Candidate id (default Candidate_X1..)")
    c.add_argument("--subsystem", default=None, help="One search_map subsystem id")
    c.add_argument(
        "--set",
        action="append",
        default=[],
        help="Override Key=Value (repeatable)",
    )
    c.add_argument("--parent", default="PRODUCTION")
    c.add_argument("--notes", default="")
    c.add_argument("--status", default="queued")
    c.add_argument(
        "--allow-multi",
        action="store_true",
        help="Allow overrides outside one subsystem (not recommended)",
    )
    c.add_argument(
        "--list-subsystems",
        action="store_true",
        help="Print may-adapt subsystem ids and exit",
    )
    c.set_defaults(func=cmd_clone)

    lp = sub.add_parser("list-presets", help="List Presets/manifest.json")
    lp.set_defaults(func=cmd_list_presets)

    pc = sub.add_parser("pause-check", help="EL6 backfill false-positive check")
    pc.add_argument("--baskets", default=None)
    pc.add_argument("--step", type=int, default=25)
    pc.set_defaults(func=cmd_pause_check)

    pf = sub.add_parser("pause-flag", help="Write live/pause_new.flag from health shadow")
    pf.add_argument("--force-on", action="store_true")
    pf.add_argument("--force-off", action="store_true")
    pf.add_argument("--no-state", action="store_true")
    pf.set_defaults(func=cmd_pause_flag)

    st = sub.add_parser("status", help="Refresh AI/STATUS.md (INF-STATUS)")
    st.set_defaults(func=cmd_status)

    bf = sub.add_parser(
        "backfill-discovery",
        help="EL1: register Discovery table rows as documented run_ids",
    )
    bf.set_defaults(func=cmd_backfill_discovery)

    gp = sub.add_parser("gate-polish", help="EL2: rebuild candidates.csv + G1 scorecard")
    gp.set_defaults(func=cmd_gate_polish)

    gc = sub.add_parser("gate-check", help="EL2: evaluate one PF/DD vs G1")
    gc.add_argument("--pf", type=float, required=True)
    gc.add_argument("--dd", type=float, required=True)
    gc.add_argument("--from", dest="window_from", default="2026.01.01")
    gc.add_argument("--to", dest="window_to", default="2026.07.31")
    gc.add_argument("--symbol", default="EURUSD")
    gc.set_defaults(func=cmd_gate_check)

    cc = sub.add_parser(
        "cert-confirm",
        help="EL3: confirm PRODUCTION lock vs certificate + preset fingerprint",
    )
    cc.set_defaults(func=cmd_cert_confirm)

    ob = sub.add_parser(
        "observatory",
        help="Wave 3: daily Observatory from health + fingerprint + lineage",
    )
    ob.set_defaults(func=cmd_observatory)

    fp = sub.add_parser(
        "fingerprint",
        help="Wave 3: compute Market Fingerprint + genome compatibility (shadow)",
    )
    fp.add_argument("--baskets", default=None)
    fp.add_argument("--window", type=int, default=100)
    fp.add_argument("--run-id", default=None, help="Attach under AI/kb/runs/<run_id>/")
    fp.add_argument("--no-attach", action="store_true")
    fp.set_defaults(func=cmd_fingerprint)

    rec = sub.add_parser(
        "recommend",
        help="Wave 4: suggest <=3 subsystems from genome mismatches",
    )
    rec.set_defaults(func=cmd_recommend)

    fac = sub.add_parser(
        "factory",
        help="Wave 4: goal-driven candidate propose/clone (one subsystem)",
    )
    fac.add_argument("--index", type=int, default=0, help="Pick from recommend list")
    fac.add_argument("--subsystem", default=None)
    fac.add_argument("--hypothesis", default="")
    fac.add_argument("--id", default=None, help="Candidate id")
    fac.add_argument("--parent", default="PRODUCTION")
    fac.add_argument(
        "--apply",
        action="store_true",
        help="Write Presets/*.set (default is dry-run)",
    )
    fac.set_defaults(func=cmd_factory)

    ab = sub.add_parser(
        "asi-build",
        help="ASI-P1: labeled dataset + splits + baseline + shadow v0",
    )
    ab.add_argument(
        "--baskets",
        default=None,
        help="Research baskets CSV (default AI/data/EURUSD_baskets_2020_2025_uid.csv)",
    )
    ab.add_argument(
        "--promote-baskets",
        default=None,
        help="Canonical G1 baskets (default AI/data/live/latest_baskets.csv)",
    )
    ab.add_argument("--no-promote", action="store_true", help="Omit promote_frozen split")
    ab.add_argument(
        "--out-dir",
        default=None,
        help="Output dir (default AI/kb/asi)",
    )
    ab.add_argument(
        "--skip-quantile",
        type=float,
        default=0.90,
        help="Train percentile for shadow v0 skip threshold",
    )
    ab.add_argument(
        "--split-profile",
        choices=("default", "long"),
        default="default",
        help="long = train 2018-2024, calibrate 2025 (guardrail holdout)",
    )
    ab.set_defaults(func=cmd_asi_build)

    at = sub.add_parser(
        "asi-train",
        help="ASI-P2: train offline TEP + calibrate threshold + ablation",
    )
    at.add_argument("--asi-dir", default=None, help="ASI kb dir (default AI/kb/asi)")
    at.add_argument(
        "--max-skip",
        type=float,
        default=0.10,
        help="Max skip rate on calibrate (default 0.10; use 0.05 with --strict)",
    )
    at.add_argument(
        "--strict",
        action="store_true",
        help="Strict retune: precision-first threshold scan",
    )
    at.add_argument(
        "--guardrail",
        action="store_true",
        help="Guardrail candidate: skip promote-frozen downgrade",
    )
    at.set_defaults(func=cmd_asi_train)

    aeg = sub.add_parser(
        "asi-export-gate",
        help="ASI-P4: export tep_gate_v1.txt for MT5 InpUseAiTepGate",
    )
    aeg.add_argument("--asi-dir", default=None)
    aeg.add_argument("--out-name", default="tep_gate_v1.txt")
    aeg.add_argument(
        "--force",
        action="store_true",
        help="Export even if guardrail review is not ok",
    )
    aeg.set_defaults(func=cmd_asi_export_gate)

    amb = sub.add_parser(
        "asi-mid-build",
        help="ASI-P5: expand baskets into mid-depth steamroller warn rows",
    )
    amb.add_argument("--baskets", default=None)
    amb.add_argument("--out-dir", default=None)
    amb.add_argument(
        "--split-profile",
        choices=("default", "long"),
        default="long",
        help="long = train 2018-2024, calibrate 2025 (default for P5)",
    )
    amb.add_argument("--min-depth", type=int, default=2)
    amb.add_argument("--max-warn", type=int, default=5)
    amb.set_defaults(func=cmd_asi_mid_build)

    amt = sub.add_parser(
        "asi-mid-train",
        help="ASI-P5: train mid-basket P(eventual steamroller) warn model",
    )
    amt.add_argument("--asi-dir", default=None)
    amt.add_argument(
        "--max-skip",
        type=float,
        default=0.15,
        help="Max warn rate on calibrate mid-rows (default 0.15)",
    )
    amt.set_defaults(func=cmd_asi_mid_train)

    amr = sub.add_parser(
        "asi-mid-review",
        help="ASI-P5: mid-basket warn review pack",
    )
    amr.add_argument("--asi-dir", default=None)
    amr.set_defaults(func=cmd_asi_mid_review)

    aem = sub.add_parser(
        "asi-export-mid-gate",
        help="ASI-P5: export mid_gate_v1.txt for MT5 InpUseAiMidWarn (warn-only)",
    )
    aem.add_argument("--asi-dir", default=None)
    aem.add_argument("--out-name", default="mid_gate_v1.txt")
    aem.set_defaults(func=cmd_asi_export_mid_gate)

    ams = sub.add_parser(
        "asi-mid-shadow",
        help="ASI-P5: score run/baskets with mid-warn shadow (no live action)",
    )
    ams.add_argument("--run-id", default=None)
    ams.add_argument("--baskets", default=None)
    ams.add_argument("--out", default=None)
    ams.set_defaults(func=cmd_asi_mid_shadow)

    arb = sub.add_parser(
        "asi-rec-build",
        help="ASI-P6: expand baskets into recovery-probability mid-depth rows",
    )
    arb.add_argument("--baskets", default=None)
    arb.add_argument("--out-dir", default=None)
    arb.add_argument(
        "--split-profile",
        choices=("default", "long"),
        default="long",
        help="long = train 2018-2024, calibrate 2025 (default for P6)",
    )
    arb.add_argument("--min-depth", type=int, default=2)
    arb.add_argument("--max-warn", type=int, default=5)
    arb.set_defaults(func=cmd_asi_rec_build)

    art = sub.add_parser(
        "asi-rec-train",
        help="ASI-P6: train P(recover | open, warn_depth); calibrate low-P exit band",
    )
    art.add_argument("--asi-dir", default=None)
    art.add_argument(
        "--max-exit-rate",
        type=float,
        default=0.15,
        help="Max early-exit recommend rate on calibrate mid-rows (default 0.15)",
    )
    art.set_defaults(func=cmd_asi_rec_train)

    arr = sub.add_parser(
        "asi-rec-review",
        help="ASI-P6: recovery probability review pack",
    )
    arr.add_argument("--asi-dir", default=None)
    arr.set_defaults(func=cmd_asi_rec_review)

    ars = sub.add_parser(
        "asi-rec-shadow",
        help="ASI-P6: score baskets with recovery low-P exit recommend (shadow only)",
    )
    ars.add_argument("--baskets", required=True)
    ars.add_argument("--asi-dir", default=None)
    ars.add_argument("--out", default=None)
    ars.set_defaults(func=cmd_asi_rec_shadow)

    argb = sub.add_parser(
        "asi-regime-build",
        help="ASI-P8: classify regimes, scorecard PF/DD, write allow/caution/skip policy",
    )
    argb.add_argument("--baskets", default=None)
    argb.add_argument(
        "--lock-baskets",
        default=None,
        help="PRODUCTION/lock baskets CSV (default: data/live/latest_baskets.csv)",
    )
    argb.add_argument("--out-dir", default=None)
    argb.add_argument("--split-profile", choices=("default", "long"), default="long")
    argb.add_argument("--deposit", type=float, default=400.0)
    argb.set_defaults(func=cmd_asi_regime_build)

    args_ = sub.add_parser(
        "asi-regime-shadow",
        help="ASI-P8: shadow-skip baskets in policy skip regimes",
    )
    args_.add_argument("--baskets", required=True)
    args_.add_argument("--asi-dir", default=None)
    args_.add_argument("--out", default=None)
    args_.add_argument("--deposit", type=float, default=400.0)
    args_.set_defaults(func=cmd_asi_regime_shadow)

    argr = sub.add_parser(
        "asi-regime-review",
        help="ASI-P8: regime intelligence review pack",
    )
    argr.add_argument("--asi-dir", default=None)
    argr.set_defaults(func=cmd_asi_regime_review)

    aerg = sub.add_parser(
        "asi-export-regime-gate",
        help="ASI-P8: export regime_gate_v1.txt (caution+skip filters) for MT5",
    )
    aerg.add_argument("--asi-dir", default=None)
    aerg.add_argument("--out-name", default="regime_gate_v1.txt")
    aerg.add_argument(
        "--skip-only",
        action="store_true",
        help="Export skip regimes only (default includes caution)",
    )
    aerg.set_defaults(func=cmd_asi_export_regime_gate)

    ash = sub.add_parser(
        "asi-shadow",
        help="ASI-P3: score run/baskets with TEP shadow (no live skip)",
    )
    ash.add_argument("--run-id", default=None, help="Registered run id under AI/kb/runs/")
    ash.add_argument("--baskets", default=None, help="Basket CSV path (ad-hoc)")
    ash.add_argument("--out", default=None, help="Ad-hoc output JSON path")
    ash.add_argument("--deposit", type=float, default=400.0)
    ash.set_defaults(func=cmd_asi_shadow)

    arv = sub.add_parser(
        "asi-review",
        help="ASI-P3: review pack TEP shadow vs PRODUCTION canon",
    )
    arv.add_argument("--asi-dir", default=None)
    arv.add_argument(
        "--production-run-id",
        default="20260101_PRODUCTION_bcc8b9b0_02",
    )
    arv.add_argument(
        "--guardrail",
        action="store_true",
        help="Guardrail review on calibrate holdout (not production parity)",
    )
    arv.set_defaults(func=cmd_asi_review)

    e7 = sub.add_parser(
        "el7-dry-run",
        help="Wave 4: EL7 Re-Discovery plan (dry-run; --apply stamps lineage retire)",
    )
    e7.add_argument(
        "--apply",
        action="store_true",
        help="Set lineage retired_run_id (human Re-Discovery only)",
    )
    e7.set_defaults(func=cmd_el7_dry_run)

    ex = sub.add_parser(
        "experiments",
        help="Wave 4: join scorecard + fingerprint + failure_reason index",
    )
    ex.set_defaults(func=cmd_experiments)

    cg = sub.add_parser("ci-gates", help="Wave 5: CI schema gates (cert/gates/FP/OpenAPI)")
    cg.set_defaults(func=cmd_ci_gates)

    dr = sub.add_parser("drift", help="Wave 5: drift alerts vs birth/compat (shadow)")
    dr.set_defaults(func=cmd_drift)

    al = sub.add_parser("artifacts-list", help="Wave 5: list immutable artifact runs")
    al.add_argument("--limit", type=int, default=50)
    al.set_defaults(func=cmd_artifacts_list)

    aa = sub.add_parser("artifacts-archive", help="Wave 5: copy live baskets to artifacts/")
    aa.add_argument("--run-id", default=None)
    aa.add_argument("--source", default="demo")
    aa.add_argument("--role", default="demo")
    aa.add_argument("--baskets", default=None)
    aa.set_defaults(func=cmd_artifacts_archive)

    rh = sub.add_parser(
        "db-rehydrate",
        help="Wave 5: restore Postgres run from artifacts/runs/{run_id}",
    )
    rh.add_argument("--run-id", required=True)
    rh.add_argument("--source", default=None)
    rh.add_argument("--role", default=None)
    rh.set_defaults(func=cmd_db_rehydrate)

    dm = sub.add_parser("db-migrate", help="Wave 1: apply Postgres schema")
    dm.set_defaults(func=cmd_db_migrate)

    di = sub.add_parser("db-ingest", help="Wave 1: upsert baskets into Postgres + artifacts")
    di.add_argument("--source", choices=["demo", "tester", "auto"], default="demo")
    di.add_argument("--role", default=None, help="run role (default demo|collect)")
    di.add_argument(
        "--from-live",
        action="store_true",
        help="Use AI/data/live/latest_baskets.csv",
    )
    di.set_defaults(func=cmd_db_ingest)

    args = ap.parse_args(argv)
    if args.cmd == "clone" and not args.list_subsystems:
        if not args.subsystem:
            print("clone_fail: --subsystem required (or --list-subsystems)")
            return 1
        if not args.set:
            print("clone_fail: need at least one --set Key=Value")
            return 1
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
