# Edge Re-Discovery System

**Role:** Snapshot + high-level changelog for the Discover plane (not the phase runbook).  
**Charter:** MT5 executes · Python scores · Human promotes  
**Updated:** 2026-07-14  
**Phase detail (Lane A):** [`../automated_edge_rediscovery_pipeline.md`](../automated_edge_rediscovery_pipeline.md) (`AER-P0`…`P6`)  
**Dual-lane MVP:** [`dual_lane_rediscovery_pipeline.md`](dual_lane_rediscovery_pipeline.md) (`DLR-P0`…`P3` **complete**)  
**Subsystem audit:** [`../system_audit.md`](../system_audit.md) · MAIN 2  
**EL7 runbook:** [`../AI/kb/el7_rediscovery_runbook.md`](../AI/kb/el7_rediscovery_runbook.md)  
**Policy:** [`../AI/kb/dlr_policy.json`](../AI/kb/dlr_policy.json) · roster [`../AI/kb/challenger_roster.md`](../AI/kb/challenger_roster.md)

> New operator/design markdown goes under [`doc/`](README.md). Root keeps spine + README; do not grow the root with more guides.

---

## What it's for

Re-Discovery finds a **better lock offline** without touching live PRODUCTION.

| May | Must not |
| --- | -------- |
| Lane A one-axis clones · Lane B from roster · Tester on Terminal B · G1 score · human promote/reject | Auto-promote · live EMA/TP/SL/lot retune · Discovery on the PRODUCTION chart · treat tester CSV as demo health · overnight-default Lane B |

**Hardware:** remote (or Terminal A) runs PRODUCTION; **Terminal B** (`MT5_FEMA_Discovery`) is Strategy Tester / candidates only. Demo health never reads tester CSVs.

---

## Dual-lane model (hybrid MVP)

**Shipped:** both lanes — default wave is still **Lane A**; Lane B is human-enqueued when policy advises (or on a hunt).

| Lane | Job | Parent | Cap |
| ---- | --- | ------ | --- |
| **A — Localized** | Cheap fade repair | current `PRODUCTION` lock | ≤3 / wave (`el7_enqueue`) |
| **B — Multi-base challenger** | Hunt outside the lock's neighbourhood; keep profiles | roster: `P1-BASELINE`, alternates, near-misses | ≤1–2 / cycle · not every night |

**One-liner:** Lane A retunes PRODUCTION; Lane B keeps multiple challenger bases on the same G1/human-promote rail — no genetic farm, auto-promote, or thawing frozen architecture.

**Policy:** default overnight = A only; escalate **1× B** after **≥2** Lane A reject/alternate (`el7_policy.ps1` advises — never auto-enqueues B).

Jobs carry `lane` · `parent` · `role` · `profile_id` · `subsystem`. Reject/alternate **upsert** profile cards (no amnesia).

```text
Lane A: PRODUCTION ± one axis           ─┐
Lane B: P1-BASELINE / alternates / …   ─┼→ Terminal B → G1 → scorecard → human
         (roster profiles, no amnesia)  ─┘
```

---

## How the loop works

```text
trigger / human opens Discovery
        ↓
el7_policy.ps1  →  recommend A  or  A+B
        ↓
Lane A: factory clones ≤3 one-axis presets from PRODUCTION
Lane B: (if advised) 1× Challenger_* from roster parent
        ↓
enqueue → Terminal B Tester (canonical window)
        ↓
sync tester → register → G1 gate (PF + DD vs PRODUCTION)
        ↓
scorecard (lane · parent · profile) → human decision
        ↓
only then: lock bump · EL8 archive · redeploy PRODUCTION
```

**G1 (current):** PF ≥ **1.36** and max DD bal ≤ **18%** vs lock `20260101_PRODUCTION_13c52cd9`.

```powershell
# From repo root
powershell -File ops\tester_queue\el7_policy.ps1
powershell -File ops\tester_queue\el7_enqueue.ps1 -Force -Max 3    # Lane A
# When recommend_b=true:
powershell -File ops\tester_queue\enqueue_lane_b.ps1 -Preset Challenger_P1BASE_adx_01 -Parent P1-BASELINE -Subsystem adx
powershell -File ops\tester_queue\drain.ps1 -Max 3
powershell -File ops\tester_queue\scorecard.ps1
powershell -File ops\tester_queue\decision.ps1 -Preset <id> -PF <pf> -DD <dd> -Decision Reject -Signer "operator"
```

---

## Subsystems (what each is meant to achieve)

| Subsystem | Job |
| --------- | --- |
| **Search map / playbook** | Defines which one axis may change (`adx`, `grid`, `session`, …) so Lane A stays localized. |
| **Candidate factory** | Turns a mismatch or forced recipe into a `Candidate_*.set` clone of PRODUCTION (≤3 / wave). |
| **Challenger roster** | Living bases + profile cards for Lane B (`P1-BASELINE`, alternates) — lose without forgetting. |
| **Dual-lane policy** | A-default EL7; advise B after ≥2 A fails; never auto-enqueue B or auto-promote. |
| **Terminal B host** | Isolated Tester box — Discovery never competes with the live/mirror chart. |
| **Tester queue** | Job list + FIFO drain; tags lane/parent/role; caps A≤3 · B≤2 queued. |
| **Scripted Tester launch** | Builds `.ini`, launches B with `/config`, waits for shutdown, parses DD from the report. |
| **Tester sync / postrun** | Pulls Agent CSVs → ingest → register so Python has a scored `run_id`. |
| **Validation G1** | Hard promote bar vs the locked birth certificate — both PF **and** DD. |
| **Morning scorecard** | Operator pack: candidates vs PRODUCTION with lane/parent/profile columns. |
| **Promotion gate** | Checklist + decision log; **refuses** Promote if G1 fails; upserts roster; never swaps charts. |
| **Run KB / lineage** | Immutable metrics + parent lock so every reject/alternate is reproducible. |
| **EL7 Lane A enqueue** | When health ladder says Discovery (or human `-Force`), fill queue from factory — A only. |

**Beside Discover (Ops):** health/decay watches whether the current lock is still true; when sick long enough, EL7 **opens** Re-Discovery — it does not invent inputs live.

---

## Snapshot status (2026-07-14)

| Item | State |
| ---- | ----- |
| AER tooling | `P0`–`P6` complete on this machine |
| Dual-lane (`DLR-*`) | **`P0`–`P3` complete** · hybrid MVP |
| Roster seeds | `P1-BASELINE` · `Candidate_X2` · `P2D-001_SES_NO23` |
| Policy | A default · escalate B after ≥2 A fails · promote = human AER-P6 |
| Queue | Empty after X1/X2 drain (live); smoke used isolated queue |
| G1 this cycle | No promote — PRODUCTION unchanged |
| EL7 ladder | Often `open_discovery=false` (compat green); overnight needs human open or `-Force` |
| Next wave hint | Lane A non-session (`adx`, `grid`, …) + optional **1× B** (policy already recommends B) |

### Evidence this cycle (AER)

| Candidate | Axis | PF | DD | Decision |
| --------- | ---- | --: | --: | -------- |
| `Candidate_X1` | session NO23 | 1.477 | 19.17% | **Reject** |
| `Candidate_X2` | session FriClose | 1.432 | 18.13% | **Alternate** (on roster) |

---

## High-level changelog

Append a dated bullet when the Discover plane's shape or status changes (not every script tweak — that stays in git / AER / DLR phase docs).

### 2026-07-13 — Initial AER MVP live

- Two-terminal topology documented and smoked (A = PRODUCTION/mirror, B = Discovery).
- Queue + postrun + scripted Tester launch (`build_ini` / `launch`) verified on Terminal B.
- Scheduler glue (L1), multi-job `drain`, `el7_enqueue`, `scorecard`, `decision.ps1` shipped.
- Phases `AER-P0`…`AER-P6` tooling marked complete; no PRODUCTION promote.
- X1 Reject / X2 Alternate on G1 `dd_breach` (session axis).

### 2026-07-14 — Snapshot doc under `doc/`

- This file added as the Discover-plane overview + changelog home.
- Convention: new high-level MDs land in `doc/` so repo root stays neat.

### 2026-07-14 — Dual-lane design → hybrid MVP

- Adopted hybrid: **Lane A** retunes PRODUCTION; **Lane B** multi-base roster on shared G1/human rail.
- `DLR-P0` charter · `P1` schema/A tags · `P2` roster/B enqueue · `P3` policy + A+B smoke — **complete**.
- Policy [`dlr_policy.json`](../AI/kb/dlr_policy.json); advisor `el7_policy.ps1`; smoke `smoke_dlr_p3.ps1`.
- Promote remains human AER-P6 only (`auto_promote=false`).

---

## Related paths

| Path | Role |
| ---- | ---- |
| `doc/dual_lane_rediscovery_pipeline.md` | Hybrid dual-lane · `DLR-P0`…`P3` MVP |
| `AI/kb/challenger_roster.md` | Lane B bases + naming |
| `AI/kb/dlr_policy.json` | EL7 dual-lane rules |
| `AI/kb/el7_rediscovery_runbook.md` | Operator EL7 steps |
| `ops/tester_queue/` | Enqueue · Lane B · policy · launch · drain · scorecard · decision · smoke |
| `ops/scheduler/` | Demo / tester Task Scheduler (L1) |
| `AI/kb/decisions/` | Filled promotion checklists |
| `AI/kb/el2_promote_decision.md` | Signed decision log |
| `AI/data/live/discovery_scorecard_latest.*` | Morning pack (gitignored data; regenerate locally) |
| `AI/data/live/dlr_el7_policy_latest.json` | Last policy advice |
| `AI/data/live/dlr_p3_smoke_latest.json` | Last A+B scorecard smoke |
