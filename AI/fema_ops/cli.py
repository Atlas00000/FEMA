"""ASCII-safe CLI: python -m fema_ops health|ingest|weekly"""

from __future__ import annotations

import argparse
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
