# FEMA — Edge Lifecycle

**Status:** **Active charter** — two build groups: **A Infra** → **B Lifecycle**  
**Job:** Keep a **living edge** honest: Discovery finds it, the EA runs it frozen, health watches death, Discovery returns only when the edge is dead.  
**Live / demo now:** `FEMA_EURUSD_M5_PRODUCTION` unchanged (see [`System Profile EURUSD.md`](System%20Profile%20EURUSD.md)).  
**Weekly plan:** [`edgescaleuproadmap.md`](edgescaleuproadmap.md) · **Vision / bands:** [`edgecontainment.md`](edgecontainment.md)

> **Spine doc.** Other AI notes are chapters/archives — not competing roadmaps.  
> [`aiedgecontain.md`](aiedgecontain.md) = offline contain experiments · [`ai_enhance.md`](ai_enhance.md) = legacy beat-2026.

---

## One-line charter

> **Discovery finds the edge; the EA runs it frozen; health detects fade and pauses new risk; only a new Discovery cycle may replace the preset — AI never reinvent the engine live.**

---

## Two groups (build order)

```text
Group A — INFRA (EA + ops plumbing)
        schema · logs · run registry · presets · CLI · certificate JSON
        │
        │  (must land before Watch is trustworthy)
        ▼
Group B — LIFECYCLE (operator loop on that infra)
        lock → run → health → pause → rediscover → retire
```

| Group | Name | Prefix | Job |
| ----- | ---- | ------ | --- |
| **A** | Infra upgrade (EA as a whole) | `INF-*` | Reproducible telemetry, config-as-code, thin offline ops |
| **B** | Lifecycle phases | `EL-*` | Find → run → watch fade → rediscover — **using Group A** |

**Rule:** Do not start serious EL5/EL6 wiring until Group A P0 items (`INF-LOG`, `INF-CERT`, `INF-EXPORT`) exist. Weekly ESR tasks map onto both (see roadmap).

---

## The problem

| Fact | Implication |
| ---- | ----------- |
| Baseline → Edge Discovery produced a **2026** PRODUCTION that looks good on demo | Edge is **window-bound**, not eternal |
| Same stack on long history (e.g. 2020–2025) can be ~PF 0.96 | “Works forever” is false; fade is expected |
| No edge stays forever | Need **lifecycle**, not endless live retune |
| Open-time AI skips (EC1/EC2) didn’t transfer | Fade is **rolling health / path**, not one bad entry tick |
| Logs live under Tester `Agent-…` paths; schemas drift | Infra must fix **access + contract** before fancy health |

---

## Three layers (do not mix jobs)

```
┌─────────────────────────────────────────────────────────┐
│  EL-DISCOVER   Edge Discovery (offline tester)          │
│  Find / promote / demote · run_id + KB · human-gated     │
└──────────────────────────┬──────────────────────────────┘
                           │ locks PRODUCTION + certificate JSON
                           ▼
┌─────────────────────────────────────────────────────────┐
│  EL-RUN        FEMA engine (demo / live)                │
│  Frozen stack · schema-versioned logs · run fingerprint │
└──────────────────────────┬──────────────────────────────┘
                           │ AI/data/live/latest_* 
                           ▼
┌─────────────────────────────────────────────────────────┐
│  EL-WATCH      Edge health (Python ops · shadow→opt-in) │
│  Certificate bands · health_v0 · pause-new shadow       │
│  Does NOT retune TP/SL/EMA live                         │
└──────────────────────────┬──────────────────────────────┘
                           │ edge dead / sick too long
                           ▼
                    back to EL-DISCOVER
```

| Layer | Owns | Must not |
| ----- | ---- | -------- |
| **Discover** | Preset search, gates, promote/demote | Live experiments / auto-promote |
| **Run** | Execution of locked PRODUCTION | Self-retune mid-flight |
| **Watch** | “Is *this* certificate still true?” | Redesign the strategy inside OnTick |

**Ops split:** MT5 **executes** · Python **thinks** · Human **promotes**. Docker = Python ops only (not MT5).

---

# Group A — Infra upgrade (EA as a whole)

**Goal:** Industry-shaped plumbing — typed telemetry, config-as-code, run registry, agent-friendly paths — **without** a multi-EA “platform.”

**Priority:** P0 before health trust · P1 with early Watch · P2 after MVP · Later = parking lot.

### Group A phase map

| ID | Name | Pri | Goal |
| -- | ---- | --- | ---- |
| **INF-LOG** | Schema-versioned logging | P0 | Stable event/basket contract + fingerprint |
| **INF-EXPORT** | Stable export paths | P0 | `AI/data/live/latest_*` — no Agent archaeology |
| **INF-CERT** | Certificate as data | P0 | JSON bands + fingerprint (scripts + agents) |
| **INF-RUN** | Run registry | P1 | Every tester/demo slice has `run_id` |
| **INF-PRESET** | Preset pipeline | P1 | Manifest + clone CLI · bookkeeping not genetics |
| **INF-OPS** | Python ops package | P1 | `fema_ops` CLI · requirements · ASCII-safe |
| **INF-EA** | EA config snapshot | P1 | Init writes `run_config` · pause-flag ready later |
| **INF-STATUS** | Operator / agent status | P2 | `AI/STATUS.md` one-pager |
| **INF-DOCKER** | Offline container | P2 | Docker for Python only |
| **INF-DEF** | Deferred infra | — | Explicit non-goals |

---

### INF-LOG — Schema-versioned logging

**ID:** `INF-LOG` · **Pri:** P0  
**Objective:** Every artifact carries a schema version and run fingerprint.

| ID | Task |
| -- | ---- |
| `INF-LOG-001` | Define `fema_baskets_vN` / `fema_events_vN` field lists (certificate metrics must map) |
| `INF-LOG-002` | Stamp `schema=` on file header or first row |
| `INF-LOG-003` | Fingerprint in Init journal + log: magic, preset id, EA build, `adx_gate`, `bsl` |
| `INF-LOG-004` | Structured retcodes / suspend reasons (enums, not free text only) |
| `INF-LOG-005` | Execution quality fields: spread at fill, reject reason |

**Exit:** New collects parse with one schema; repair scripts know the version.  
**ESR:** `ESR-W02`

---

### INF-EXPORT — Stable export paths

**ID:** `INF-EXPORT` · **Pri:** P0  
**Objective:** Repo-local latest pointers for humans and agents.

| ID | Task |
| -- | ---- |
| `INF-EXPORT-001` | Convention: copy/symlink Agent CSVs → `AI/data/live/` |
| `INF-EXPORT-002` | Maintain `latest_baskets.csv` / `latest_events.csv` (gitignored data OK) |
| `INF-EXPORT-003` | Document ≤10-line copy steps in `AI/README.md` |
| `INF-EXPORT-004` | Optional: small `sync_from_agent.ps1` |

**Exit:** Health/ingest never hardcode `Tester\Agent-127.0.0.1-3000\…`.  
**ESR:** `ESR-W02`

---

### INF-CERT — Certificate as data

**ID:** `INF-CERT` · **Pri:** P0  
**Objective:** Green/Amber/Red bands live in JSON; markdown is human mirror.

| ID | Task |
| -- | ---- |
| `INF-CERT-001` | Publish `AI/certificate_PRODUCTION_EURUSD.json` from [`edgecontainment.md`](edgecontainment.md) §1–2 |
| `INF-CERT-002` | Include windows **50 / 100 / 250**, weights, persistence (3 down / 2 recover) |
| `INF-CERT-003` | Link from System Profile + this doc |
| `INF-CERT-004` | Birth metrics table (lock PF/WR/DD/trades) |

**Exit:** Scripts load bands from JSON only (no magic numbers in code).  
**ESR:** `ESR-W01`

---

### INF-RUN — Run registry

**ID:** `INF-RUN` · **Pri:** P1  
**Objective:** Append-only experiment log — industry default for Discovery.

| ID | Task |
| -- | ---- |
| `INF-RUN-001` | Define `run_id` = date + preset + window hash (document format) |
| `INF-RUN-002` | Store under `AI/kb/runs/<run_id>/` (metrics JSON + path to CSV) |
| `INF-RUN-003` | Edge Discovery rows must cite `run_id` when materially updated |
| `INF-RUN-004` | Never overwrite prior run folders |

**Exit:** At least PRODUCTION lock + one demo slice registered.  
**ESR:** `ESR-W09` (bootstrap with KB)

---

### INF-PRESET — Preset / candidate pipeline

**ID:** `INF-PRESET` · **Pri:** P1  
**Objective:** Presets as code; clone bookkeeping — **not** genetic search.

| ID | Task |
| -- | ---- |
| `INF-PRESET-001` | `presets/manifest.json` (id, parent, diff summary, status) |
| `INF-PRESET-002` | CLI/helper: clone PRODUCTION → Candidate_Xn (one subsystem) |
| `INF-PRESET-003` | Localized search map card (may-adapt vs frozen) — containment §6 |
| `INF-PRESET-004` | Gate rules as data (optional JSON) matching Edge Discovery G-rules |

**Exit:** Manual factory can spawn ≤3 candidates with KB rows.  
**ESR:** `ESR-W10` · **Out:** auto genetic / RL optimize (`INF-DEF`)

---

### INF-OPS — Python ops package

**ID:** `INF-OPS` · **Pri:** P1  
**Objective:** One offline entrypoint; less one-off script chaos.

| ID | Task |
| -- | ---- |
| `INF-OPS-001` | `requirements.txt` (or pyproject) pinned |
| `INF-OPS-002` | Package layout `AI/fema_ops/` (ingest, health, kb) |
| `INF-OPS-003` | CLI: `python -m fema_ops health|ingest|weekly` |
| `INF-OPS-004` | ASCII-only console output (Windows cp1252 safe) |
| `INF-OPS-005` | Unit tests for health weights + persistence flags |

**Exit:** Daily health is one command from repo root.  
**ESR:** `ESR-W03`–`W05`

---

### INF-EA — EA-side infra (still deterministic)

**ID:** `INF-EA` · **Pri:** P1  
**Objective:** Better logs/config snapshot — **no** AI brain in the engine.

| ID | Task |
| -- | ---- |
| `INF-EA-001` | On Init: write `run_config.json` (Inp* that define the edge) |
| `INF-EA-002` | Ensure certificate metrics available (depth, bars, MAE/MFE, …) |
| `INF-EA-003` | Keep retcode fail-soft taxonomy (v1.24+) |
| `INF-EA-004` | Later: read local **pause-new flag file** (shadow→wire) — not OnTick ML |

**Exit:** New build fingerprints match certificate; logs feed health without spreadsheets.  
**ESR:** `ESR-W02`, `ESR-DEF-PAUSE-WIRE`

---

### INF-STATUS — Operator / agent access

**ID:** `INF-STATUS` · **Pri:** P2  
**Objective:** One glance for humans and coding agents.

| ID | Task |
| -- | ---- |
| `INF-STATUS-001` | `AI/STATUS.md` — phase, last health, last `run_id`, open ESR week |
| `INF-STATUS-002` | Commit schemas + empty templates; gitignore fat CSVs |
| `INF-STATUS-003` | Keep docs linked from this spine only |

**Exit:** Agent session starts from STATUS + certificate JSON + latest CSV.

---

### INF-DOCKER — Offline container (optional)

**ID:** `INF-DOCKER` · **Pri:** P2  
**Objective:** Reproducible **Python** env only.

| ID | Task |
| -- | ---- |
| `INF-DOCKER-001` | Dockerfile for `fema_ops` (Linux) |
| `INF-DOCKER-002` | Mount `AI/data` read/write; no MT5 inside |

**Exit:** `docker run … health` works.  
**Out:** Dockerized MetaTrader / tester farm (`INF-DEF`).

---

### INF-DEF — Deferred infra (do not build in MVP)

| ID | Item |
| -- | ---- |
| `INF-DEF-001` | MT5 in Docker / remote tester farm |
| `INF-DEF-002` | Multi-EA control plane UI |
| `INF-DEF-003` | Genetic / swarm / RL auto-optimize |
| `INF-DEF-004` | Live EMA/TP/SL/lot AI |
| `INF-DEF-005` | Feature-drift ML pipelines |
| `INF-DEF-006` | Reopen EC2 open-time fail predictor as main path |

---

# Group B — Lifecycle phases (on Group A infra)

**Goal:** Operator loop. Every EL task **consumes** INF artifacts (certificate JSON, `latest_*`, run_id, KB, health CLI).

### Lifecycle stages

```
Baseline / prior lock
        │
        ▼
   Discovery campaign     ← EL0–EL2   (+ INF-RUN, INF-PRESET)
        │
        ▼
   Lock PRODUCTION        ← EL3       (+ INF-CERT)
        │
        ▼
   Demo / live run        ← EL4       (+ INF-LOG, INF-EXPORT, INF-EA)
        │
        ├─ healthy ───────► keep running
        │
        ▼
   Fade / death signal    ← EL5–EL6   (+ INF-OPS, INF-CERT)
        │
        ├─ pause new risk (soft / shadow)
        │
        ▼
   Re-Discovery trigger   ← EL7       (+ INF-PRESET, INF-RUN)
        │
        ▼
   New lock or retire     ← EL3 / EL8
```

### Group B phase map

| ID | Name | Wire? | Needs infra | Goal |
| -- | ---- | ----- | ------------ | ---- |
| **EL0** | Baseline & inventory | No | — | Know starting point |
| **EL1** | Discovery campaign | No | INF-RUN, INF-PRESET | Find candidates |
| **EL2** | Promote / demote gates | No | INF-RUN, INF-PRESET | Honest lock criteria |
| **EL3** | Production lock & certificate | Docs | **INF-CERT** | Freeze stack + JSON bands |
| **EL4** | Run (demo → live) | Yes | **INF-LOG**, **INF-EXPORT**, INF-EA | Trade lock; stable telemetry |
| **EL5** | Edge health watch | Shadow | **INF-OPS**, INF-CERT, INF-EXPORT | Rolling death / fade detect |
| **EL6** | Soft pause & alert | Opt-in | INF-EA flag, INF-OPS | Pause *new* only |
| **EL7** | Re-Discovery trigger | Process | INF-PRESET, INF-RUN | Leave lock → search again |
| **EL8** | Retire / archive | Docs | INF-RUN, INF-CERT | One active lock |

**ESR mapping:** W1–2 → EL3+INF-CERT/LOG · W3–6 → EL5 · W7–8 → EL6 · W9–11 → EL7+factory · W12 → spine freeze.

---

### EL0 — Baseline & inventory

**ID:** `EL0-BASE`  
**Status:** Done for EURUSD (historical)  
**Objective:** Record pre-Discovery baseline.

| ID | Task |
| -- | ---- |
| `EL0-001` | Name baseline preset / stack (pre-PRODUCTION) |
| `EL0-002` | Record symbol · TF · deposit · tester model |
| `EL0-003` | Snapshot key metrics on then-canonical window |
| `EL0-004` | Link journal / preset files · optional `run_id` backfill |

**Exit:** “We started from X; Discovery moved us to Y.”

---

### EL1 — Discovery campaign

**ID:** `EL1-DISC`  
**Status:** Done for EURUSD 2026 → PRODUCTION; **ongoing lab**  
**Infra:** `INF-RUN`, `INF-PRESET`  
**Objective:** Structured search via [`Edge Discovery.md`](Edge%20Discovery.md).

| ID | Task |
| -- | ---- |
| `EL1-001` | Fix canonical Discovery window |
| `EL1-002` | Run phase rows with gates |
| `EL1-003` | Log every material run with **`run_id`** + KB path |
| `EL1-004` | Prefer preset diffs; minimal engine churn |

**Exit:** Shortlist with comparable windows and registered runs.  
**Rule:** Offline only; demo keeps prior lock while search runs.

---

### EL2 — Promote / demote gates

**ID:** `EL2-GATE`  
**Status:** Done for current PRODUCTION  
**Infra:** `INF-RUN`, `INF-PRESET`  
**Objective:** Promote on evidence; never “AI says so.”

| ID | Task |
| -- | ---- |
| `EL2-001` | Define G1 (etc.) vs control |
| `EL2-002` | Require PF **and** DD (or agreed pair) |
| `EL2-003` | Demote stale-slice-only wins |
| `EL2-004` | Document rejects in KB (`failure_reason`) |
| `EL2-005` | Use promotion checklist ([`edgescaleuproadmap.md`](edgescaleuproadmap.md) W11) |

**Exit:** Written promote decision + KB status=`locked` or `rejected`.

---

### EL3 — Production lock & edge certificate

**ID:** `EL3-LOCK`  
**Status:** **Active** · certificate JSON = Group A deliverable  
**Infra:** **`INF-CERT`** (required)  
**Objective:** Freeze *what* we run and *how we know it’s still healthy*.

| ID | Task |
| -- | ---- |
| `EL3-001` | Lock preset + `.ini` ([`System Profile EURUSD.md`](System%20Profile%20EURUSD.md)) |
| `EL3-002` | Freeze stack (EMA / grid / BSL / ADX / TP) |
| `EL3-003` | Publish MD + **`AI/certificate_PRODUCTION_EURUSD.json`** |
| `EL3-004` | EA/journal fingerprint must match certificate |
| `EL3-005` | Birth metrics + Green/Amber/Red bands (containment §1) |

**Exit:** Certificate data + docs checked in; demo load matches fingerprint.  
**ESR:** `ESR-W01`

---

### EL4 — Run (demo → live)

**ID:** `EL4-RUN`  
**Status:** **Active** — demo looking good  
**Infra:** **`INF-LOG`**, **`INF-EXPORT`**, `INF-EA`  
**Objective:** Trade the lock. Observe. No mid-flight “improvements.”

| ID | Task |
| -- | ---- |
| `EL4-001` | Deploy PRODUCTION via Settings `.ini` only |
| `EL4-002` | `InpUseAiEventLog` on; schema-versioned exports |
| `EL4-003` | Daily/weekly: sync → `AI/data/live/latest_*` |
| `EL4-004` | Operator checklist: fingerprint · spread · session |
| `EL4-005` | Update `AI/STATUS.md` when materially changing |

**Exit:** Stable run; latest pointers always valid.  
**Hard rule:** No live EMA / TP / SL / grid / lot from AI.

---

### EL5 — Edge health watch

**ID:** `EL5-HEALTH`  
**Status:** **Next focus** (after INF-CERT + INF-EXPORT)  
**Infra:** **`INF-OPS`**, `INF-CERT`, `INF-EXPORT`  
**Objective:** Is *this* certificate still true? Rolling path — not open-time P(fail).

| ID | Task |
| -- | ---- |
| `EL5-001` | Rolling windows **50 / 100 / 250** from certificate JSON |
| `EL5-002` | `health_v0` weighted 0–100 (containment §2) via `fema_ops health` |
| `EL5-003` | Ladder: Normal → Investigate → Watch → Re-Discovery → Retire |
| `EL5-004` | Persistence: **3** deteriorating windows; **2** recoveries to clear |
| `EL5-005` | Shadow artifacts: `health_latest.json` + MD |
| `EL5-006` | Drift tags v0: Market / Execution / Performance (rules only) |
| `EL5-007` | Weekly review template filled (ESR-W06) |

**Exit:** Operator trusts score enough to act (still human-gated).  
**ESR:** `ESR-W03`–`W06`, `ESR-W08`  
**Not EL5:** EC2-style basket fail predictor (failed transfer).

---

### EL6 — Soft pause & alert

**ID:** `EL6-PAUSE`  
**Status:** Blocked on trusted EL5  
**Infra:** `INF-OPS` shadow · later `INF-EA` flag file  
**Objective:** Pause **new** baskets only; existing baskets use engine TP/SL.

| ID | Task |
| -- | ---- |
| `EL6-001` | Policy from containment §4 (allowed / forbidden) |
| `EL6-002` | Shadow field `would_pause_new` on health report |
| `EL6-003` | False-positive check on demo backfill (must not always-on) |
| `EL6-004` | Resume: R healthy windows **or** human ack |
| `EL6-005` | Opt-in wire via flag file only after shadow OK (`ESR-DEF-PAUSE-WIRE`) |

```
critical health (persistent)  → pause new + alert
uncertain                     → keep running
healthy again                 → resume (auto or ack)
```

**ESR:** `ESR-W07`

---

### EL7 — Re-Discovery trigger

**ID:** `EL7-REDISC`  
**Status:** Process until EL5/EL6 trusted  
**Infra:** `INF-PRESET`, `INF-RUN`  
**Objective:** Leave the lock without weekly panic retunes.

| ID | Task |
| -- | ---- |
| `EL7-001` | Trigger table: health ladder, persistence, pause duration |
| `EL7-002` | Snapshot current lock into KB as retired/parent |
| `EL7-003` | Open EL1 on fresh canonical window; ≤3 manual candidates first |
| `EL7-004` | Promote only via EL2 + checklist |
| `EL7-005` | If no promote: stay paused / last acceptable lock |

**Rule:** Watch may **trigger**; it may not **author** the new preset.  
**ESR:** `ESR-W10`–`W11`

---

### EL8 — Retire / archive

**ID:** `EL8-RETIRE`  
**Status:** As needed  
**Infra:** `INF-RUN`, `INF-CERT`, `INF-PRESET`  
**Objective:** One active lock; history intact.

| ID | Task |
| -- | ---- |
| `EL8-001` | Archive old PRODUCTION (date + why + `run_id`) |
| `EL8-002` | Keep presets / certificates / KB reproducible |
| `EL8-003` | Update System Profile + Edge Discovery status |
| `EL8-004` | Switch demo/live only after new EL3 complete |

---

## What AI / scripts are for

| May | Must not |
| --- | -------- |
| Score rolling health / fade (`INF-OPS`) | Invent entries live |
| Soft-pause new risk after EL6 pass | Retune EMA / TP / SL / grid online |
| Clone preset bookkeeping (`INF-PRESET`) | Auto-promote PRODUCTION |
| Trigger Re-Discovery | Replace Edge Discovery judgment |
| Log shadow decisions | Require beat-2026 demo PF |

---

## Relation to other docs

| Doc | Role |
| --- | ---- |
| **`edgelifecycle.md` (this file)** | **Spine** — Group A infra + Group B lifecycle |
| [`edgescaleuproadmap.md`](edgescaleuproadmap.md) | Weekly `ESR-W*` implementation order |
| [`edgecontainment.md`](edgecontainment.md) | Vision + answered gaps (bands, formula, ladder) |
| [`Edge Discovery.md`](Edge%20Discovery.md) | Discovery lab + G-rules |
| [`System Profile EURUSD.md`](System%20Profile%20EURUSD.md) | Locked PRODUCTION fingerprint |
| [`aiedgecontain.md`](aiedgecontain.md) | Offline contain tooling — archive/chapter |
| [`ai_enhance.md`](ai_enhance.md) | Legacy AI — archive |

---

## Immediate next step

**Group A P0 first** (in parallel with ESR-W01/W02):

1. `INF-CERT-001` — certificate JSON  
2. `INF-LOG-001` / `INF-EXPORT-001` — schema + `AI/data/live/latest_*`  

Then **Group B `EL5`** via `INF-OPS` health_v0 — not another open-time fail model.
