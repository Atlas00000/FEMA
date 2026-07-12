# EL7 trigger table (IS-EL7-01)

Human opens Re-Discovery. Scripts only **recommend**.

| Ladder | Persistence | Pause shadow | Open Discovery? | Priority | Next |
| ------ | ----------- | ------------ | --------------- | -------- | ---- |
| `retire` | any | likely | **Yes** | high | EL7-002 snapshot → EL1 ≤3 |
| `re_discovery` | `warning_active` | yes | **Yes** | high | Same |
| `re_discovery` | not yet | maybe | Wait | medium | Do not panic-retune |
| `watch` | warning + det≥3 | maybe | **Yes** (optional) | medium | Factory recommend ≤3 |
| `watch` / `investigate` | weak | no | No | low | Offline notes only |
| `normal` | — | no | No | none | Observatory only |

**Ignore single bad day** (certificate `ignore_single_bad_day`).

CLI: `python -m fema_ops el7-dry-run` → [`el7_dry_run_latest.json`](el7_dry_run_latest.json)

Full steps: [`el7_rediscovery_runbook.md`](el7_rediscovery_runbook.md) · SOP [`research_loop_sop.md`](research_loop_sop.md)
