# Edge Re-Discovery System

**Role:** Snapshot + high-level changelog for the Discover plane (not the phase runbook).  
**Charter:** MT5 executes · Python scores · Human promotes  
**Updated:** 2026-07-19  
**Phase detail (Lane A):** [`../automated_edge_rediscovery_pipeline.md`](../automated_edge_rediscovery_pipeline.md) (`AER-P0`…`P6`)  
**Dual-lane MVP:** [`dual_lane_rediscovery_pipeline.md`](dual_lane_rediscovery_pipeline.md) (`DLR-P0`…`P3` **complete**)  
**Adaptive selection:** [`adaptive_selection_phases.md`](adaptive_selection_phases.md) (`ASI-P5` **COMPLETE** · Mode B Alternate · `ASI-P4` Alternate)
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

Append a dated bullet when the Discover plane's shape or status changes (not every script tweak — that stays in git / AER / DLR / ASI phase docs).

### 2026-07-17 — Adaptive selection charter (`ASI-P0`)

- Adopted **ASI**: selection over signal rewrite; structural failures accepted; adaptive tracks (TEP first).
- Success contract: G1 PF/DD hard · n ≥90% / WR ±3pp soft · skip budget ≤10% · anti-overfit split.
- Search-map bookkeeping: shadow = `asi_track=tep`; P4 tags `regime_extra` / `tep` until dedicated keys.
- Code deferred to `ASI-P1` (labels). PRODUCTION unchanged.

### 2026-07-17 — ASI labels + dataset (`ASI-P1`)

- **`python -m fema_ops asi-build`**: steamroller labels · TEP open features · train/calibrate/promote splits.
- Artifacts: `AI/kb/asi/` (1315 research baskets + 111 promote-frozen PRODUCTION canon).
- Shadow v0: provisional impulse p90 skip (replaced in P2). No live gate.

### 2026-07-17 — ASI offline TEP (`ASI-P2`)

- **`python -m fema_ops asi-train`**: logistic TEP · threshold **0.581** locked on calibrate (5% skip).
- Ablation: TEP full beats static + ADX-only on calibrate AUC.
- Promote-frozen one-shot: kept PF **1.48** vs **1.45** baseline (n=103); not tuned on this window.
- Artifacts: `tep_model_card.json` · `asi_shadow_tep.json`. No live gate until P4.

### 2026-07-17 — ASI shadow ops (`ASI-P3`)

- `asi-shadow` / `asi-review` · postrun hook · scorecard ASI columns.
- Review pack vs PRODUCTION canon: **kill** — precision 25%, false-skip winners dominate, DD proxy 18.14→18.37.
- **P4 live gate blocked** until retune or stop. No auto-promote.

### 2026-07-17 — ASI guardrail gate (`ASI-P4`)

- Philosophy: **guardrails not gates** — holdout kill=ok, not beat PRODUCTION on demo.
- `long_train` split: fit 2020–2024 · holdout 2025 · threshold **~0.605** · skip **2.8%** · precision **67%**.
- Wired: `InpUseAiTepGate` · `AiTepGate.mqh` · `asi-export-gate` · preset `ASI_P4_TEP_GUARD_01`.
- Pack: [`ASI_P4_tep_guard_pack.md`](ASI_P4_tep_guard_pack.md). Next: Terminal B test · 2018+ basket collect.

### 2026-07-19 — ASI-P4 Alternate (keep guardrail)

- Tester 2018–2025: PF~1.00 · DD~55% · gate healthy (`p~0.65`, not lock).
- Window addendum: **2026.01–07 PF 1.38** · **2025–2026.07 PF 1.20** — competitive, still not promote.
- Decision: **Alternate** — keep `ASI_P4_TEP_GUARD_01` as opt-in guardrail candidate; do not replace PRODUCTION.
- Profile `prof_ASI_P4_TEP_GUARD_01` · decision `AI/kb/decisions/20260719_ASI_P4_TEP_GUARD_01_Alternate.md`.

### 2026-07-19 — ASI mid-basket warn (`ASI-P5`) started

- Offline MVP: depth-milestone rows · `y_mid_steamroller` · warn-only ADR.
- CLI: `asi-mid-build` / `asi-mid-train` / `asi-mid-review` / `asi-export-mid-gate` / `asi-mid-shadow`.
- Stacked presets: `ASI_P5_TEP_MID_01` (Mode A) · `ASI_P5_TEP_MID_BSL_01` (Mode B early close, EA v1.28).
- Pack: [`ASI_P5_midbasket_pack.md`](ASI_P5_midbasket_pack.md).

### 2026-07-19 — ASI-P5 Mode B Alternate (own preset)

- Promote bar: **survival across regimes** (not beat PRODUCTION).
- Tester deposit 400: **2026** PF1.44 / DD~19%; **2018–25** PF1.35 / DD~23% (vs TEP-only ~PF1 / DD~55%).
- Decision: **Alternate** — keep `ASI_P5_TEP_MID_BSL_01` separate from Mode A / P4 / PRODUCTION.
- Profile `prof_ASI_P5_TEP_MID_BSL_01` · decision `AI/kb/decisions/20260719_ASI_P5_TEP_MID_BSL_01_Alternate.md`.

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
| `doc/adaptive_selection_phases.md` | ASI tracks · P5 Complete · Mode B Alternate |
| `doc/ASI_P4_tep_guard_pack.md` | TEP guardrail gate |
| `doc/ASI_P5_midbasket_pack.md` | Mid-basket Mode A + Mode B (own presets) |
| `doc/backtesting_guide.md` | Systematic backtesting · anti-overfitting · time splits · FEMA gates |
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
