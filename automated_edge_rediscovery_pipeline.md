# Automated Edge Re-Discovery Pipeline

**Status:** Phases `AER-P0`–`AER-P6` tooling complete (2026-07-13); PRODUCTION lock unchanged this cycle  
**Charter fit:** Discover offline → score in `fema_ops` → human promote → PRODUCTION on MT5 stays frozen  
**Hardware rule:** Discovery uses a **second local MT5 terminal** on the same machine (or a second install). **No VPS** in this plan.  
**Non-goals:** TradingView as promote authority · MT5-in-Docker · auto-promote · live EMA/TP/SL/lot retune

**Spine links:** [`edgelifecycle.md`](edgelifecycle.md) (EL7) · [`infrascaleup.md`](infrascaleup.md) § IS-P4 · [`AI/kb/el7_rediscovery_runbook.md`](AI/kb/el7_rediscovery_runbook.md) · [`AI/kb/wave6_park_freeze.md`](AI/kb/wave6_park_freeze.md)

---

## 1. One-sentence job

Overnight (or queued) Strategy Tester jobs on a **second terminal** produce candidate CSVs; `fema_ops` scores and gate-checks them; a human alone may promote. The PRODUCTION chart terminal is never used for Discovery runs.

---

## 2. Topology (two local terminals)

```text
┌─────────────────────────────┐     ┌──────────────────────────────────┐
│  Terminal A — PRODUCTION    │     │  Terminal B — Discovery (Tester) │
│  Chart: PRODUCTION.set      │     │  Strategy Tester only            │
│  Common\Files\FEMA_AI       │     │  Tester\...\Agent-*\...\FEMA_AI  │
│  Demo/live health path      │     │  Never writes Common demo path   │
└──────────────┬──────────────┘     └────────────────┬─────────────────┘
               │ sync -Source demo                    │ sync -Source tester
               ▼                                      ▼
        ops/incoming/demo                      ops/incoming/tester
               │                                      │
               └─────────────► fema_ops ◄─────────────┘
                      health | register | gate-check
                                   │
                            human promote?
                             ├── no  → keep lock
                             └── yes → new certificate
                                       (redeploy Terminal A later)
```

| Role | Terminal | Owns | Sync | Ingest |
| ---- | -------- | ---- | ---- | ------ |
| **PRODUCTION** | **A** (primary) | Locked chart · `Common\Files\FEMA_AI\` | `ops/sync/sync.ps1 -Source demo` | `fema_ops ingest --source demo` |
| **Discovery** | **B** (second local) | Strategy Tester · Agent `FEMA_AI` | `ops/sync/sync.ps1 -Source tester` | `fema_ops ingest --source tester` |

**This machine (2026-07-13)**

| | Path |
| --- | --- |
| Terminal A (PRODUCTION) | `%APPDATA%\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075` |
| Terminal B (Discovery) install | `C:\MT5_FEMA_Discovery` |
| Terminal B data | `%APPDATA%\MetaQuotes\Terminal\0E1EDD540A3CC541130B9A608E1932D2` |
| B Tester Agent CSV | `...\Tester\0E1EDD540A3CC541130B9A608E1932D2\Agent-127.0.0.1-3000\MQL5\Files\FEMA_AI\` |

**Hard rules**

1. Never point demo health at tester CSVs.
2. Never run Optimizer / heavy Discovery on Terminal A while a demo basket is open.
3. Prefer Terminal B for all `.set` candidates; Terminal A stays on PRODUCTION fingerprint (`adx_gate=on`, `bsl=25`).
4. Same PC is fine — second terminal install/profile is enough; **do not require a VPS**.

---

## 3. End-to-end flow

```text
recommend / factory / clone  →  Presets/*.set
        │
        ▼
enqueue (ops/tester_queue)  →  queue.json
        │
        ▼
Terminal B: Strategy Tester (canonical window)
        │
        ▼
sync tester → ingest → register → gate-check
        │
        ▼
promotion checklist (human) → promote | reject | alternate
```

### Candidate job contract

| Field | Value |
| ----- | ----- |
| Symbol / TF | EURUSD M5 |
| Window | `2026.01.01`–`2026.07.31` (canonical lock) |
| Deposit | $400 · every tick · `ProfitInPips=0` |
| Diff | **One subsystem** ([`AI/kb/search_map.md`](AI/kb/search_map.md)) |
| Cap | ≤3 candidates per EL7 wave |
| Output | Agent `FEMA_AI` baskets / events CSV |
| Authority | MT5 Tester only (not TradingView) |

### Commands (reference)

```powershell
# Factory → queue
cd AI
python -m fema_ops recommend
python -m fema_ops factory --apply --index 0
cd ..
powershell -File ops\tester_queue\enqueue.ps1 -Preset Candidate_X1 -Window "2026.01.01-2026.07.31" -Notes "EL7"
powershell -File ops\tester_queue\status.ps1

# After Terminal B Tester finishes
powershell -File ops\tester_queue\postrun.ps1 -Preset Candidate_X1 -DD <max_dd_bal_pct>
powershell -File ops\sync\sync.ps1 -Source tester
cd AI
python -m fema_ops ingest --source tester
python -m fema_ops register --baskets <path> --preset Candidate_X1 --role candidate
python -m fema_ops gate-check
```

Demo watch (Terminal A only):

```powershell
powershell -File ops\sync\sync.ps1 -Source demo
cd AI
python -m fema_ops pipeline
```

---

## 4. What the pipeline may / must not do

| May | Must not |
| --- | -------- |
| Ingest CSVs, attach `run_id`, compute PF/DD/WR | Change live `Inp*` on Terminal A |
| Compare to birth certificate / G1 | Auto-swap PRODUCTION mid-flight |
| Update KB (`candidates.csv`, failure reasons) | Treat tester collect as demo health |
| Recommend next subsystem (`recommend` / `factory`) | Auto-promote or “AI says so” promote |
| Archive rejects / lineage parent-child | Run Discovery on Terminal A by default |

Promote gate (**G1**): PF ≥ PRODUCTION **and** max DD ≤ PRODUCTION — see [`AI/kb/gate_rules.json`](AI/kb/gate_rules.json) and [`AI/templates/promotion_checklist.md`](AI/templates/promotion_checklist.md).

---

## 5. Day / night operating split

| When | Terminal A (PRODUCTION) | Terminal B (Discovery) | Ops |
| ---- | ----------------------- | ---------------------- | --- |
| Day | Runs / manages baskets | Idle or one smoke job | `pipeline` on **demo** |
| Night | Untouched | Drain `queue.json` (≤3) | Sync **tester** → register → gate-check |
| Morning | Still PRODUCTION | Results waiting | Human scorecard + checklist |

---

## 6. Automation maturity (do not skip levels)

| Level | ID | Capability |
| ----- | -- | ---------- |
| L0 | `AER-L0` | Human drains queue: open Terminal B Tester from `queue.json` |
| L1 | `AER-L1` | Task Scheduler: post-run `sync` + `ingest` (+ optional `gate-check`) |
| L2 | `AER-L2` | Scripted `.ini` / Tester launch on Terminal B (still local) |
| L3 | `AER-L3` | Unattended multi-job drain on Terminal B (one-at-a-time) |

**Start at L0.** L2/L3 are polish — architecture is valid without them.

---

## 7. Implementation phases (with IDs)

Phased delivery. Existing infra marked **done** where already shipped; remaining work is explicit.

### Phase 0 — Charter & path split · `AER-P0`

| ID | Task | Status | Notes |
| -- | ---- | ------ | ----- |
| `AER-P0-01` | Document two-terminal topology (A=PRODUCTION, B=Discovery) | **done** | This file |
| `AER-P0-02` | Forbid VPS as a requirement; second local terminal only | **done** | §2 |
| `AER-P0-03` | Separate demo vs tester sync/ingest paths | **done** | `ops/sync/sync.ps1` · `IS-P4-01` |
| `AER-P0-04` | Park auto-promote / live retune / TV-as-authority | **done** | Wave 6 `PARK-01` / `PARK-02` |

**Exit:** Operator can explain A vs B without mixing CSVs.

---

### Phase 1 — Terminal B standup · `AER-P1`

| ID | Task | Status | Notes |
| -- | ---- | ------ | ----- |
| `AER-P1-01` | Install / open **second MT5 terminal** (Terminal B) on the same machine | **done** | `0E1EDD540A3CC541130B9A608E1932D2` · `C:\MT5_FEMA_Discovery` |
| `AER-P1-02` | Compile `FEMA.mq5` into Terminal B; copy `Presets/*.set` | **done** | v1.26 · 5 presets in Tester profiles |
| `AER-P1-03` | Smoke Tester: `PRODUCTION.set` on canonical window once | **done** | PF 1.42 · +$257 · DD 18.14% / 21.19% · 434 trades |
| `AER-P1-04` | Verify `sync.ps1 -Source tester` finds Agent CSV | **done** | 109 basket rows · `ingest --source tester` OK |
| `AER-P1-05` | Confirm Terminal A demo path unchanged after B run | **done** | B CSV from `Tester\0E1E...\Agent-*` only |

**Exit:** One known-good Tester CSV from Terminal B ingested as `--source tester`. **Phase 1 complete (2026-07-13).**

---

### Phase 2 — Queue + factory habit (L0) · `AER-P2`

| ID | Task | Status | Notes |
| -- | ---- | ------ | ----- |
| `AER-P2-01` | Use `ops/tester_queue/enqueue.ps1` + `status.ps1` as the job list | **done** | `postrun.ps1` added for after-Tester chain |
| `AER-P2-02` | Drain one queued job on Terminal B (manual Tester) | **done** | `job_20260713_003828` · PF 1.47 · +$272 · 426 trades |
| `AER-P2-03` | `register` + `gate-check` for that candidate | **done** | `20260101_Candidate_X1_bcc8b9b0` · G1 **fail** DD 19.17% |
| `AER-P2-04` | Cap ≤3 candidates per wave; one-subsystem diffs | **done** (policy) | EL7 / factory |
| `AER-P2-05` | Run `Candidate_X1` through full L0 loop | **done** | **Reject** — keep PRODUCTION (same as P2D NO23 pattern) |

**Exit:** At least one factory preset scored vs G1 without touching Terminal A. **Phase 2 complete (2026-07-13).**

---

### Phase 3 — Post-run glue (L1) · `AER-P3`

| ID | Task | Status | Notes |
| -- | ---- | ------ | ----- |
| `AER-P3-01` | Task Scheduler: tester sync after hours | **done** | `ops/scheduler/scheduled_tester.ps1` + `register_tasks.ps1` |
| `AER-P3-02` | Chain `ingest --source tester` | **done** | Via `sync.ps1` + scheduled_tester |
| `AER-P3-03` | Demo pipeline on separate schedule | **done** | `scheduled_demo.ps1` → `fema_ops pipeline` |
| `AER-P3-04` | Heartbeat if CSV missing | **done** | `sync_heartbeat.json` + `scheduler_last.json` |

**Install once:**

```powershell
powershell -ExecutionPolicy Bypass -File ops\scheduler\register_tasks.ps1
```

**Manual / morning check:**

```powershell
powershell -File ops\scheduler\scheduled_demo.ps1
powershell -File ops\scheduler\scheduled_tester.ps1
# G1 still manual: ops\tester_queue\postrun.ps1 -Preset <id> -DD <pct>
```

Docs: [`ops/scheduler/README.md`](ops/scheduler/README.md)

**Exit:** Morning review sees tester scorecard without re-running sync by hand. **Phase 3 complete (2026-07-13).**

---

### Phase 4 — Scripted Tester launch (L2) · `AER-P4`

| ID | Task | Status | Notes |
| -- | ---- | ------ | ----- |
| `AER-P4-01` | Generate / maintain Tester `.ini` per queued preset | **done** | `build_ini.ps1` · `ini/` · ProfitInPips=0 · ShutdownTerminal=1 |
| `AER-P4-02` | Launch Strategy Tester on **Terminal B** from queue head | **done** | `launch.ps1` · `C:\MT5_FEMA_Discovery\terminal64.exe /config:` |
| `AER-P4-03` | Detect run complete → stamp `queue.json` + postrun | **done** | Waits process exit · report DD parse · `postrun.ps1` |
| `AER-P4-04` | Guard: refuse launch if Terminal A path selected | **done** | `discovery_paths.json` · hash/install checks |

**Verified (2026-07-13):**

| Mode | Result |
| ---- | ------ |
| Dry-run | guard_ok · ini generated · Terminal B only |
| Live | `job_20260713_014807` Candidate_X1 ~2m30s → register PF **1.477**, G1 **fail** DD 19.17% |

**Ini lessons (embedded in `build_ini.ps1`):** embed `[TesterInputs]` from `.set` (not only `ExpertParameters`); `Leverage=500`; flat report name; clamp future `ToDate`; search reports under Terminal B **data** hash as well as install dir.

```powershell
powershell -File ops\tester_queue\launch.ps1 -DryRun
powershell -File ops\tester_queue\launch.ps1          # real overnight job
powershell -File ops\tester_queue\launch.ps1 -SkipPostrun
```

Docs: [`ops/tester_queue/README.md`](ops/tester_queue/README.md)

**Exit:** Overnight unattended single-job Discovery on Terminal B (still human promote). **Phase 4 complete (2026-07-13).**

---

### Phase 5 — Multi-job drain + EL7 wire-up (L3) · `AER-P5`

| ID | Task | Status | Notes |
| -- | ---- | ------ | ----- |
| `AER-P5-01` | Drain queue FIFO until empty or max 3 / night | **done** | `ops/tester_queue/drain.ps1` · one-at-a-time · `drain_latest.json` |
| `AER-P5-02` | Hook EL7 dry-run → enqueue recommended factory clones | **done** | `el7_enqueue.ps1` · needs open_discovery **or** `-Force` · max 3 · copies `.set` to Terminal B |
| `AER-P5-03` | Scorecard pack for morning (PF/DD vs PRODUCTION + G1 pass/fail) | **done** | `scorecard.ps1` → `AI/data/live/discovery_scorecard_latest.{json,md}` |
| `AER-P5-04` | Explicit **no** auto-promote endpoint or cron | **done** | Charter + scripts stamp “NO AUTO-PROMOTE”; no promote cron registered |

**Night / morning flow:**

```powershell
# Human opens Discovery (or wait for ladder open_discovery=true)
powershell -File ops\tester_queue\el7_enqueue.ps1           # skip if ladder closed
powershell -File ops\tester_queue\el7_enqueue.ps1 -Force    # human-opened EL7 wave

# Overnight drain (max 3)
powershell -File ops\tester_queue\drain.ps1 -Max 3

# Morning pack — read-only; still no promote
powershell -File ops\tester_queue\scorecard.ps1
```

When `recommend` returns `cloneable=0` but `-Force` is set, wave defaults to subsystems `session,adx,grid` (factory one-axis recipes). See [`el7_rediscovery_runbook.md`](AI/kb/el7_rediscovery_runbook.md).

**Exit:** EL7 trigger (or human `-Force`) can fill overnight queue; human still signs promote/reject. **Phase 5 complete (2026-07-13).**

---

### Phase 6 — Promote & redeploy (human gate) · `AER-P6`

| ID | Task | Status | Notes |
| -- | ---- | ------ | ----- |
| `AER-P6-01` | Fill [`AI/templates/promotion_checklist.md`](AI/templates/promotion_checklist.md) | **done** (tooling) | `ops/tester_queue/decision.ps1` → `AI/kb/decisions/*.md` |
| `AER-P6-02` | Record decision in `AI/kb/el2_promote_decision.md` | **done** (tooling) | Script appends; refuse Promote if G1 fail |
| `AER-P6-03` | On promote: new lock + certificate bump + EL8 archive | **armed** | Printed next-steps only — never auto |
| `AER-P6-04` | Redeploy Terminal A deliberately (new `.set`); Terminal B stays Discovery | **armed** | Manual chart swap after sign-off |
| `AER-P6-05` | On reject: KB `failure_reason`; keep `20260101_PRODUCTION_13c52cd9` | **done** (smoke) | X1 Reject · X2 Alternate · PRODUCTION kept |

**Smoke (2026-07-13):**

| Preset | PF | DD | G1 | Decision |
| ------ | --: | --: | --- | -------- |
| `Candidate_X1` (NO23) | 1.477 | 19.17% | fail | **Reject** `dd_breach` |
| `Candidate_X2` (FriClose) | 1.432 | 18.13% | fail | **Alternate** `dd_breach` |

```powershell
powershell -File ops\tester_queue\decision.ps1 -Preset Candidate_X1 -PF 1.477 -DD 19.17 -Decision Reject -FailureReason dd_breach -Signer "operator"
# Promote refused unless G1 pass; even then no Terminal A swap:
powershell -File ops\tester_queue\decision.ps1 -Preset <id> -PF <pf> -DD <dd> -Decision Promote -Signer "operator"
```

**Exit:** PRODUCTION changes only via signed promote + Terminal A redeploy. **Phase 6 tooling complete (2026-07-13)** — no PRODUCTION change this cycle.

---

## 8. Phase dependency graph

```text
AER-P0 (charter / paths)
    └─► AER-P1 (Terminal B standup)
            └─► AER-P2 (L0 queue habit)
                    └─► AER-P3 (L1 scheduler glue)
                            └─► AER-P4 (L2 scripted Tester)
                                    └─► AER-P5 (L3 multi-job + EL7)
                                            └─► AER-P6 (human promote / redeploy A)
```

Parallel allowed: doc/KB updates anytime; **never** block P1–P5 on a VPS purchase.

---

## 9. Why not TradingView (in this pipeline)

| Role | Allowed? |
| ---- | -------- |
| Cheap idea screen / sketch | Optional research only |
| G1 / promote authority | **No** — MT5 Tester on Terminal B only |
| Feed foreign trades as if FEMA AI0 CSV | **No** without explicit schema adapter + still MT5 confirm |

Foreign backtesters may sit **in front** of enqueue; they do not replace Terminal B.

---

## 10. Definition of done (pipeline MVP)

MVP = **`AER-P0` + `AER-P1` + `AER-P2`** complete:

1. Terminal A = PRODUCTION only.  
2. Terminal B = Discovery Tester.  
3. At least one queued candidate run → tester sync → register → gate-check.  
4. Human checklist used once (promote or reject).  
5. No VPS, no auto-promote, no live retune.

L1–L3 (`AER-P3`–`AER-P5`) and human-gate tooling (`AER-P6`) are complete on this machine (2026-07-13). No auto-promote; Terminal A stays on `PRODUCTION` until a signed G1 pass + redeploy.

---

## 11. Related IDs (existing)

| Existing ID | Relation |
| ----------- | -------- |
| `IS-P4-01` | Tester queue folder shipped |
| `IS-EL7-01` / `IS-EL7-02` | Trigger table + rediscovery runbook |
| `RG-FAC-01` / `RG-FAC-02` | `recommend` / `factory` |
| `PARK-01` / `PARK-02` / `PARK-03` | No auto-promote · no live retune · no MT5-in-Docker |
| `G1` | Promote gate vs PRODUCTION |

---

## 12. License / ownership

Ops plane still: **MT5 executes · Python scores · Human promotes.**  
This document owns the **automated Re-Discovery testing path** on a second local terminal only.
