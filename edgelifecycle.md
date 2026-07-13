# FEMA — Edge Lifecycle

**Status:** **Active charter** — two build groups: **A Infra** → **B Lifecycle**  
**Job:** Keep a **living edge** honest: Discovery finds it, the EA runs it frozen, health watches death, Discovery returns only when the edge is dead.  
**Live / demo now:** `FEMA_EURUSD_M5_PRODUCTION` unchanged (see [`System Profile EURUSD.md`](System%20Profile%20EURUSD.md)).  
**Operator glance:** [`AI/STATUS.md`](AI/STATUS.md) · **System map:** [`system_audit.md`](system_audit.md) · **Weekly plan:** [`edgescaleuproadmap.md`](edgescaleuproadmap.md) · **Vision / bands:** [`edgecontainment.md`](edgecontainment.md) · **Ops plane:** [`infrascaleup.md`](infrascaleup.md)

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
| **INF-RUN** | Run registry | P1 | **Done** — `AI/kb/runs/` · `fema_ops register` |
| **INF-PRESET** | Preset pipeline | P1 | **Done** — manifest · clone · search map · gates |
| **INF-OPS** | Python ops package | P1 | **Done** — `fema_ops` · health_v0 |
| **INF-EA** | EA config snapshot | P1 | **Done** v1.26 — run_config · pause flag opt-in |
| **INF-STATUS** | Operator / agent status | P2 | **Done** — `AI/STATUS.md` · `fema_ops status` |
| **INF-DOCKER** | Offline container | P2 | **Done** — `AI/Dockerfile` · no MT5 |
| **INF-DEF** | Deferred infra | — | Explicit non-goals |

---

### INF-LOG — Schema-versioned logging

**ID:** `INF-LOG` · **Pri:** P0 · **Status:** **Done** (EA **v1.25**)  
**Objective:** Every artifact carries a schema version and run fingerprint.

| ID | Task | Status |
| -- | ---- | ------ |
| `INF-LOG-001` | Define `fema_baskets_v2` / `fema_events_v2` field lists | ✅ [`AI/schemas/`](AI/schemas/) |
| `INF-LOG-002` | Stamp `# FEMA_META schema=` on CSV headers | ✅ |
| `INF-LOG-003` | Fingerprint in Init journal + `_run.meta.txt` | ✅ magic · ea_build · adx_gate · bsl · preset |
| `INF-LOG-004` | Structured retcodes / suspend reasons | ✅ `ORDER_FAIL` · `LIFECYCLE` · `reject_class` · `transient` |
| `INF-LOG-005` | Execution quality fields | ✅ `spread_points` · `retcode` · `reject_class` |

**Exit:** New collects parse with one schema; Python uses `AI/csv_util.py` (skips `#` meta).  
**ESR:** `ESR-W02`  
**Compile:** `FEMA.mq5` **v1.25** — journal shows `AI log fema_baskets_v2/... run_id=... fp=adx_gate=...`

---

### INF-EXPORT — Stable export paths

**ID:** `INF-EXPORT` · **Pri:** P0 · **Status:** **Done**  
**Objective:** Repo-local latest pointers for humans and agents.

| ID | Task | Status |
| -- | ---- | ------ |
| `INF-EXPORT-001` | Convention: copy Agent CSVs → `AI/data/live/` | ✅ |
| `INF-EXPORT-002` | Maintain `latest_baskets.csv` / `latest_events.csv` | ✅ (gitignored data) |
| `INF-EXPORT-003` | Document ≤10-line copy steps in `AI/README.md` | ✅ |
| `INF-EXPORT-004` | `sync_from_agent.ps1` / `.py` | ✅ |

**Exit:** Health/ingest use `AI/paths.py` → `LATEST_BASKETS` — never hardcode Agent paths.  
**ESR:** `ESR-W02`  
**Run:** `python AI/sync_from_agent.py` (from Experts/FEMA)

---

### INF-CERT — Certificate as data

**ID:** `INF-CERT` · **Pri:** P0 · **Status:** **Done**  
**Objective:** Green/Amber/Red bands live in JSON; markdown is human mirror.

| ID | Task | Status |
| -- | ---- | ------ |
| `INF-CERT-001` | Publish `AI/certificate_PRODUCTION_EURUSD.json` | ✅ |
| `INF-CERT-002` | Windows 50/100/250 · weights · persistence 3/2 | ✅ |
| `INF-CERT-003` | Link from System Profile + this doc | ✅ |
| `INF-CERT-004` | Birth metrics (PF 1.36 · WR 71% · 424 trades · DD 18%) | ✅ |

**Exit:** Scripts use `AI/cert_loader.py` / `paths.CERTIFICATE_JSON` — no magic numbers.  
**ESR:** `ESR-W01`  
**Human mirror:** [`AI/certificate_PRODUCTION_EURUSD.md`](AI/certificate_PRODUCTION_EURUSD.md)

---

### INF-RUN — Run registry

**ID:** `INF-RUN` · **Pri:** P1 · **Status:** **Done**  
**Objective:** Append-only experiment log — industry default for Discovery.

| ID | Task | Status |
| -- | ---- | ------ |
| `INF-RUN-001` | Define `run_id` = date + preset + window hash | ✅ [`AI/kb/runs/README.md`](AI/kb/runs/README.md) |
| `INF-RUN-002` | Store under `AI/kb/runs/<run_id>/` | ✅ + `fema_ops register` |
| `INF-RUN-003` | Edge Discovery cites `run_id` when materially updated | ✅ PRODUCTION lock cited |
| `INF-RUN-004` | Never overwrite prior run folders | ✅ suffix `_02`… |

**Exit:** PRODUCTION lock + one collect slice registered.  
**Bootstrap:** `20260101_PRODUCTION_13c52cd9` (lock) · `20200101_PRODUCTION_abfae89a` (collect)  
**ESR:** `ESR-W09` (runs done; candidates CSV still W09)

---

### INF-PRESET — Preset / candidate pipeline

**ID:** `INF-PRESET` · **Pri:** P1 · **Status:** **Done**  
**Objective:** Presets as code; clone bookkeeping — **not** genetic search.

| ID | Task | Status |
| -- | ---- | ------ |
| `INF-PRESET-001` | `Presets/manifest.json` | ✅ |
| `INF-PRESET-002` | CLI: `fema_ops clone` (one subsystem) | ✅ |
| `INF-PRESET-003` | Search map may-adapt vs frozen | ✅ `AI/kb/search_map.*` |
| `INF-PRESET-004` | Gate rules JSON (G1/G2/G3) | ✅ `AI/kb/gate_rules.json` |

**Exit:** Manual factory can spawn ≤3 candidates with KB rows.  
**Playbook:** [`AI/kb/clone_playbook.md`](AI/kb/clone_playbook.md) · **KB:** [`AI/kb/candidates.csv`](AI/kb/candidates.csv)  
**ESR:** `ESR-W10` · **Out:** auto genetic / RL (`INF-DEF`)

---

### INF-OPS — Python ops package

**ID:** `INF-OPS` · **Pri:** P1 · **Status:** **Done** (`health_v0`)  
**Objective:** One offline entrypoint; less one-off script chaos.

| ID | Task | Status |
| -- | ---- | ------ |
| `INF-OPS-001` | `AI/requirements.txt` | ✅ |
| `INF-OPS-002` | Package `AI/fema_ops/` (health, ingest, persistence) | ✅ |
| `INF-OPS-003` | CLI: `python -m fema_ops health\|ingest\|weekly` | ✅ |
| `INF-OPS-004` | ASCII-only console output | ✅ |
| `INF-OPS-005` | Unit tests weights + persistence | ✅ |

**Exit:** Daily health is one command from `AI/`.  
**ESR:** `ESR-W03`–`W05`  
**Artifacts:** `AI/data/live/health_latest.json` · `.md` · `health_state.json`

---

### INF-EA — EA-side infra (still deterministic)

**ID:** `INF-EA` · **Pri:** P1 · **Status:** **Done** (v1.26)  
**Objective:** Better logs/config snapshot — **no** AI brain in the engine.

| ID | Task | Status |
| -- | ---- | ------ |
| `INF-EA-001` | On Init: write `*_run_config.json` (edge Inp*) | ✅ |
| `INF-EA-002` | Certificate metrics in basket CSV (depth, bars, MAE/MFE) | ✅ (v1.25+) |
| `INF-EA-003` | Retcode fail-soft taxonomy | ✅ (v1.24+) |
| `INF-EA-004` | Opt-in read `pause_new.flag` (default OFF) | ✅ shadow→wire |

**Compile:** `FEMA.mq5` **v1.26** — journal `pause_flag=off|armed|ON` · `run_config.json` next to meta.  
**Exit:** Fingerprint matches certificate; logs feed health.  
**ESR:** `ESR-W02`, `ESR-DEF-PAUSE-WIRE`

---

### INF-STATUS — Operator / agent access

**ID:** `INF-STATUS` · **Pri:** P2 · **Status:** **Done**  
**Objective:** One glance for humans and coding agents.

| ID | Task | Status |
| -- | ---- | ------ |
| `INF-STATUS-001` | `AI/STATUS.md` — phase, health, run_id, open ESR | ✅ + `STATUS.json` |
| `INF-STATUS-002` | Schemas + templates committed; fat CSVs gitignored | ✅ |
| `INF-STATUS-003` | Docs linked from spine / STATUS only | ✅ |

**Refresh:** `cd AI && python -m fema_ops status`  
**Exit:** Agent session starts from STATUS + certificate JSON + latest CSV.  
**Templates:** [`AI/templates/daily_health.md`](AI/templates/daily_health.md) · [`weekly_edge_review.md`](AI/templates/weekly_edge_review.md)

---

### INF-DOCKER — Offline container (optional)

**ID:** `INF-DOCKER` · **Pri:** P2 · **Status:** **Done**  
**Objective:** Reproducible **Python** env only.

| ID | Task | Status |
| -- | ---- | ------ |
| `INF-DOCKER-001` | Dockerfile for `fema_ops` (Linux) | ✅ [`AI/Dockerfile`](AI/Dockerfile) |
| `INF-DOCKER-002` | Mount `AI/data` read/write; no MT5 inside | ✅ compose + [`AI/DOCKER.md`](AI/DOCKER.md) |

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
| **EL0** | Baseline & inventory | No | — | **Done** — [`AI/kb/el0_baseline_inventory.md`](AI/kb/el0_baseline_inventory.md) |
| **EL1** | Discovery campaign | No | INF-RUN, INF-PRESET | **Done** backfill — 34 `run_id`s |
| **EL2** | Promote / demote gates | No | INF-RUN, INF-PRESET | **Done** — G1 scorecard + decision log |
| **EL3** | Production lock & certificate | Docs | **INF-CERT** | **Done** — `cert-confirm` |
| **EL4** | Run (demo → live) | Yes | **INF-LOG**, **INF-EXPORT**, INF-EA | Trade lock; stable telemetry |
| **EL5** | Edge health watch | Shadow | **INF-OPS**, INF-CERT, INF-EXPORT | Rolling death / fade detect |
| **EL6** | Soft pause & alert | Shadow / opt-in | INF-EA flag, INF-OPS | Pause *new* only |

| **EL7** | Re-Discovery trigger | Process | INF-PRESET, INF-RUN | Leave lock → search again |
| **EL8** | Retire / archive | Docs | INF-RUN, INF-CERT | One active lock |

**ESR mapping:** W1–2 → EL3+INF-CERT/LOG · W3–6 → EL5 · W7–8 → EL6 · W9–11 → EL7+factory · W12 → spine freeze.

### Expanded lifecycle names (alias map — do not fork)

| Expanded name | Lifecycle ID | Notes |
| --- | --- | --- |
| Discover | EL1 | Edge Discovery campaign |
| Validate | EL2 | G1 / checklist |
| Lock | EL3 | Certificate + preset freeze |
| Deploy | EL4 | Demo → live run |
| Observe | EL5 | `health_v0` / Observatory |
| Watch / Investigate | EL5 ladder | Persistence, not panic |
| Generate candidate | EL7 → factory / `clone` | Offline only |
| Validate (candidate) | EL2 | Same gates |
| Promote | EL2 + EL3 | Human only |
| Archive / Retire | EL8 | One active lock |

Ops Plane roadmap: [`infrascaleup.md`](infrascaleup.md) §16.

---

### EL0 — Baseline & inventory

**ID:** `EL0-BASE`  
**Status:** **Done** (EURUSD formalized)  
**Objective:** Record pre-Discovery baseline.

| ID | Task | Status |
| -- | ---- | ------ |
| `EL0-001` | Name baseline preset / stack (pre-PRODUCTION) | ✅ `P1-BASELINE` |
| `EL0-002` | Record symbol · TF · deposit · tester model | ✅ EURUSD M5 · $400 · every tick |
| `EL0-003` | Snapshot key metrics on then-canonical window | ✅ PF 0.17 → 1.27 → 1.36 |
| `EL0-004` | Link journal / preset files · optional `run_id` | ✅ inventory + PRODUCTION `run_id` |

**Artifact:** [`AI/kb/el0_baseline_inventory.md`](AI/kb/el0_baseline_inventory.md) · JSON twin  
**Exit:** “We started from **P1-BASELINE**; Discovery moved us to **PRODUCTION**.”

---

### EL1 — Discovery campaign

**ID:** `EL1-DISC`  
**Status:** **Done** for EURUSD 2026 table backfill; lab remains open for new rows  
**Infra:** `INF-RUN`, `INF-PRESET`  
**Objective:** Structured search via [`Edge Discovery.md`](Edge%20Discovery.md).

| ID | Task | Status |
| -- | ---- | ------ |
| `EL1-001` | Fix canonical Discovery window | ✅ 2026.01.01–2026.07.31 |
| `EL1-002` | Run phase rows with gates | ✅ P2A–P2F closed |
| `EL1-003` | Log every material run with **`run_id`** + KB path | ✅ 34 rows → `kb/runs/` |
| `EL1-004` | Prefer preset diffs; minimal engine churn | ✅ factory / presets |

**Backfill:** `python -m fema_ops backfill-discovery` · map [`AI/kb/discovery_run_ids.json`](AI/kb/discovery_run_ids.json)  
**Exit:** Shortlist with comparable windows and registered runs.  
**Rule:** Offline only; demo keeps prior lock while search runs.

---

### EL2 — Promote / demote gates

**ID:** `EL2-GATE`  
**Status:** **Done** (polish)  
**Infra:** `INF-RUN`, `INF-PRESET`  
**Objective:** Promote on evidence; never “AI says so.”

| ID | Task | Status |
| -- | ---- | ------ |
| `EL2-001` | Define G1 (etc.) vs control | ✅ `gate_rules.json` |
| `EL2-002` | Require PF **and** DD | ✅ `fema_ops gate-check` |
| `EL2-003` | Demote stale-slice-only wins | ✅ STALE_SLICE rule |
| `EL2-004` | Document rejects in KB (`failure_reason`) | ✅ `candidates.csv` + scorecard |
| `EL2-005` | Promotion checklist | ✅ `templates/promotion_checklist.md` |

**Decision log:** [`AI/kb/el2_promote_decision.md`](AI/kb/el2_promote_decision.md)  
**Commands:** `python -m fema_ops gate-polish` · `gate-check --pf 1.40 --dd 19`  
**Exit:** Written promote decision + KB status=`locked` or `rejected`.

---

### EL3 — Production lock & edge certificate

**ID:** `EL3-LOCK`  
**Status:** **Done** (cert/lock confirm)  
**Infra:** **`INF-CERT`** (required)  
**Objective:** Freeze *what* we run and *how we know it’s still healthy*.

| ID | Task | Status |
| -- | ---- | ------ |
| `EL3-001` | Lock preset + `.ini` ([`System Profile EURUSD.md`](System%20Profile%20EURUSD.md)) | ✅ `PRODUCTION.set` + lock run |
| `EL3-002` | Freeze stack (EMA / grid / BSL / ADX / TP) | ✅ fingerprint vs `.set` |
| `EL3-003` | Publish MD + **`AI/certificate_PRODUCTION_EURUSD.json`** | ✅ |
| `EL3-004` | EA/journal fingerprint must match certificate | ✅ preset check; journal = operator |
| `EL3-005` | Birth metrics + Green/Amber/Red bands (containment §1) | ✅ aligned with `gate_rules` |

**Confirm:** `python -m fema_ops cert-confirm` → [`AI/kb/el3_lock_confirm.md`](AI/kb/el3_lock_confirm.md)  
**Exit:** Certificate data + docs checked in; demo load matches fingerprint.  
**ESR:** `ESR-W01`

---

### EL4 — Run (demo → live)

**ID:** `EL4-RUN`  
**Status:** **Active** — Wave 0 evidence path  
**Infra:** **`INF-LOG`**, **`INF-EXPORT`**, `INF-EA`  
**Objective:** Trade the lock. Observe. No mid-flight “improvements.”

| ID | Task | Status |
| -- | ---- | ------ |
| `EL4-001` | Deploy PRODUCTION via Settings `.ini` only | Active on demo |
| `EL4-002` | `InpUseAiEventLog` on; schema-versioned exports | ✅ v1.26 |
| `EL4-003` | Daily/weekly: sync → `AI/data/live/latest_*` | ✅ `ingest --source demo` |
| `EL4-004` | Operator checklist: fingerprint · spread · session | ✅ Init fingerprint |
| `EL4-005` | Update `AI/STATUS.md` when materially changing | ✅ `fema_ops status` |

**CSV paths (Wave 0):**

| Role | Path |
| ---- | ---- |
| **Demo (EL4)** | `%APPDATA%\MetaQuotes\Terminal\Common\Files\FEMA_AI\` (preferred) · else Terminal `MQL5\Files\FEMA_AI\` |
| **Tester (Discovery)** | `%APPDATA%\MetaQuotes\Tester\<id>\Agent-*\MQL5\Files\FEMA_AI\` |
| **Stable pointers** | `AI/data/live/latest_*.csv` + `sync_heartbeat.json` |

```powershell
cd AI
python -m fema_ops ingest --source demo    # EL4 default
python -m fema_ops health
python -m fema_ops observatory
python -m fema_ops status
```

**Exit:** Stable run; latest pointers always valid; STATUS shows `source=demo` when on demo path.  
**Hard rule:** No live EMA / TP / SL / grid / lot from AI.

---

### EL5 — Edge health watch

**ID:** `EL5-HEALTH`  
**Status:** **Shadow** (`health_v0` shipped)  
**Infra:** **`INF-OPS`**, `INF-CERT`, `INF-EXPORT`  
**Objective:** Is *this* certificate still true? Rolling path — not open-time P(fail).

| ID | Task | Status |
| -- | ---- | ------ |
| `EL5-001` | Rolling windows **50 / 100 / 250** from certificate JSON | ✅ |
| `EL5-002` | `health_v0` weighted 0–100 via `fema_ops health` | ✅ |
| `EL5-003` | Ladder: Normal → Investigate → Watch → Re-Discovery → Retire | ✅ |
| `EL5-004` | Persistence: **3** deteriorating · **2** recoveries | ✅ |
| `EL5-005` | Shadow artifacts: `health_latest.json` + MD | ✅ |
| `EL5-006` | Drift tags v0: Market / Execution / Performance | ✅ |
| `EL5-007` | Weekly review template filled (ESR-W06) | ✅ template shipped |

**Command:** `cd AI && python -m fema_ops health` · wrapper `python AI/edge_health_cert.py`  
**Exit:** Operator trusts score enough to act (still human-gated).  
**ESR:** `ESR-W03`–`W06`, `ESR-W08`  
**Not EL5:** EC2-style basket fail predictor (failed transfer).

---

### EL6 — Soft pause & alert

**ID:** `EL6-PAUSE`  
**Status:** **Shadow** (wire opt-in, default OFF)  
**Infra:** `INF-OPS` shadow · `INF-EA` flag file  
**Objective:** Pause **new** baskets only; existing baskets use engine TP/SL.

| ID | Task | Status |
| -- | ---- | ------ |
| `EL6-001` | Policy from containment §4 | ✅ [`AI/kb/pause_policy.md`](AI/kb/pause_policy.md) |
| `EL6-002` | Shadow field `would_pause_new` on health report | ✅ |
| `EL6-003` | False-positive check on backfill | ✅ `fema_ops pause-check` |
| `EL6-004` | Resume: recover windows **or** human clear flag | ✅ |
| `EL6-005` | Opt-in wire via flag (`InpReadPauseNewFlag`) | ✅ default **false** |

```
critical health (persistent)  → would_pause_new (+ alert in report)
uncertain                     → keep running
healthy again                 → resume (auto recover or clear flag)
```

**Wire:** set `InpReadPauseNewFlag=true` and place `FEMA_AI\\pause_new.flag` only after `pause-check` OK.  
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

**Trigger table:** [`AI/kb/el7_trigger_table.md`](AI/kb/el7_trigger_table.md) · CLI `python -m fema_ops el7-dry-run`  
**Local automation:** [`automated_edge_rediscovery_pipeline.md`](automated_edge_rediscovery_pipeline.md) (`AER-P0`…`P6` · Terminal B)  
**Rule:** Watch may **trigger**; it may not **author** the new preset.  
**SOP:** [`AI/kb/research_loop_sop.md`](AI/kb/research_loop_sop.md) · runbook [`AI/kb/el7_rediscovery_runbook.md`](AI/kb/el7_rediscovery_runbook.md) · RACI [`AI/kb/raci.md`](AI/kb/raci.md) · lineage [`AI/kb/lineage.json`](AI/kb/lineage.json) · factory `recommend` / `factory`  
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
| [`infrascaleup.md`](infrascaleup.md) | Ops plane — Docker/Postgres/API/sync architecture |
| [`Edge Discovery.md`](Edge%20Discovery.md) | Discovery lab + G-rules |
| [`System Profile EURUSD.md`](System%20Profile%20EURUSD.md) | Locked PRODUCTION fingerprint |
| [`aiedgecontain.md`](aiedgecontain.md) | Offline contain tooling — archive/chapter |
| [`ai_enhance.md`](ai_enhance.md) | Legacy AI — archive |

---

## Immediate next step

**Wave 6** = park freeze only ([`AI/kb/wave6_park_freeze.md`](AI/kb/wave6_park_freeze.md)) — no auto-promote / live retune / MT5-Docker / UI.  
After demo basket close: `python -m fema_ops pipeline` for Wave 0 `on_demo_path` health.
