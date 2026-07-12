# Wave 6 — Park freeze (offline only)

**Status:** Parked by charter. This file is the offline **confirmation**, not a build plan.  
**Rule:** Do not implement rows below until charter explicitly changes.

| ID | Parked item | Why parked | Offline substitute (already shipped) |
| -- | ----------- | ---------- | ------------------------------------ |
| `PARK-01` | Auto-promote PRODUCTION | Human-only promote | `raci.md` · EL2 checklist · `cert-confirm` |
| `PARK-02` | Live EMA/TP/SL/lot from AI | Charter break | Factory `recommend` / `factory` → human `clone` + Tester |
| `PARK-03` | MT5 in Docker / K8s tester farm | Windows worker instead | `ops/tester_queue/` · `sync.ps1` · Agent FEMA_AI |
| `PARK-04` | AI model retrain drives **live** risk | Premature / risk | Shadow scoring only: `health` · `fingerprint` · `drift` · `pipeline` |
| `PARK-05` | EC2 open-time fail predictor as main path | Superseded | Rolling `health_v0` + Observatory (fade path) |
| `PARK-06` | Full platform UI / multi-EA control plane | API first | Read-only `ops/api` · `STATUS` · Observatory MD |

## Allowed offline work under Wave 6 (done here)

1. Keep parks visible in STATUS / lifecycle / infrascaleup.
2. Refuse auto-wire of pause, promote, or live retune.
3. Prefer `python -m fema_ops pipeline` for offline ops.

## Explicit non-goals (do not code)

- Endpoints or cron that promote presets
- EA inputs changed by Python at runtime
- MT5 containerization
- Retrain → lot/TP/SL
- Reopening `ai_enhance` / EC2 predictor as spine
- Multi-EA dashboard UI

**Unblock condition:** Written charter change + human sign-off (RACI Accountable), not a green health score alone.
