# FEMA Ops Plane — Infra Scale-Up

**Status:** Proposed architecture (execution engine unchanged) · **Roadmap:** §16  
**Scope:** Infra around the frozen MT5 execution engine (FEMA PRODUCTION).  
**Non-goals:** Live retune, auto-promote, MT5-in-Docker (MVP), new strategy logic.  
**Date:** 2026-07-12  
**Spine:** `[edgelifecycle.md](edgelifecycle.md)` · vision `[edgecontainment.md](edgecontainment.md)` · weekly `[edgescaleuproadmap.md](edgescaleuproadmap.md)`

---

## 1. Executive summary

FEMA already has a working **execution + evidence** philosophy (lock → certificate → health → human promote). The main limitations are environmental: Tester/Agent paths, file locks, weekend quiet, and no always-on query layer for operators/agents.

This document proposes an **Ops Plane**: Linux host + Postgres + object store + Dockerized `fema_ops` + read-only API, fed by a Windows MT5 worker that only runs the EA and pushes CSV/meta artifacts. The EA binary and PRODUCTION stack stay unchanged.

---

## 2. Architecture

```text
┌─────────────────────────────────────┐
│  Windows MT5 Worker (execution)     │
│  - Terminal demo (account)          │
│  - Strategy Tester (Discovery)      │
│  - FEMA.ex5 PRODUCTION (frozen)     │
│  - Writes: FEMA_AI/*.csv + meta     │
└─────────────────┬───────────────────┘
                  │ sync (SFTP / agent / scheduled copy)
                  ▼
┌─────────────────────────────────────┐
│  Linux Ops Host (evidence + jobs)   │
│  Docker Compose:                    │
│    postgres | minio | fema-ops      │
│    api (read-only) | optionally     │
│    grafana / cron                   │
│  Postgres ← parsed runs/baskets     │
│  Object store ← immutable CSV blobs │
└─────────────────┬───────────────────┘
                  │ HTTPS read-only
                  ▼
         Operator / Cursor agents
```

**Rule:** MT5 **executes**. Ops host **stores, scores, alerts**. Humans **promote**.

---

## 3. Tech stack


| Layer                | Choice                                            | Role                              |
| -------------------- | ------------------------------------------------- | --------------------------------- |
| Execution            | MetaTrader 5 + `FEMA.mq5` (v1.26+)                | Unchanged engine                  |
| Worker OS            | Windows 10/11 (dedicated box or cloud Windows)    | Demo + Tester only                |
| Ops OS               | Ubuntu 22.04/24.04 LTS                            | Always-on jobs                    |
| Containers           | Docker + Docker Compose                           | Package non-MT5 services          |
| Language             | Python 3.11+ (existing `fema_ops`)                | Ingest, health, gates, CLI        |
| DB                   | PostgreSQL 16                                     | Runs, baskets, health, candidates |
| Blob store           | MinIO (S3 API) or local `artifacts/` volume       | Immutable CSV/meta per `run_id`   |
| API                  | FastAPI (read-only)                               | STATUS / health / runs for agents |
| Schedulers           | `cron` or Compose `ofelia` / systemd timers       | Sync, health, weekly              |
| Schemas              | JSON Schema (+ optional SQL migrations Alembic)   | Contract tests                    |
| Secrets              | `.env` / Docker secrets (no secrets in git)       | DB URL, API tokens                |
| Optional later       | Prometheus + Grafana                              | Health time series                |
| Explicitly out (MVP) | MT5 in Docker, Kubernetes, genetic farms, live AI | INF-DEF                           |


Reuse existing: `certificate_PRODUCTION_EURUSD.json`, `fema_baskets_v2` / `fema_events_v2`, `run_id` format, G1 `gate_rules.json`.

---

## 4. Folder structure

### 4.1 Repo (Experts/FEMA) — source of truth for code/docs

```text
FEMA/
├── FEMA.mq5
├── Include/ ...
├── Presets/
│   ├── PRODUCTION.set
│   └── manifest.json
├── edgelifecycle.md              # spine
├── infrascaleup.md               # this file — ops-plane architecture
├── System Profile EURUSD.md
├── AI/
│   ├── fema_ops/                 # CLI + library (extend, don't fork)
│   ├── schemas/                  # fema_baskets_v2, events, certificate
│   ├── certificate_PRODUCTION_EURUSD.json
│   ├── kb/
│   │   ├── runs/                 # lightweight index (optional mirror)
│   │   ├── gate_rules.json
│   │   └── ...
│   ├── data/                     # gitignored fat data OR thin pointers
│   │   └── live/                 # post-sync pointers for local use
│   ├── Dockerfile
│   ├── docker-compose.yml        # local/dev ops stack
│   └── tests/
└── ops/                          # NEW: deploy manifests for the ops host
    ├── README.md
    ├── docker-compose.prod.yml
    ├── postgres/init/
    ├── api/                      # FastAPI app (thin)
    ├── sync/                     # windows→linux agent specs
    └── schemas/                  # OpenAPI + JSON Schema copies
```

### 4.2 Ops host data layout (outside git)

```text
/var/fema/
├── incoming/                     # drop zone from Windows sync
│   ├── demo/
│   └── tester/
├── artifacts/                    # or MinIO bucket fema-artifacts
│   └── runs/
│       └── {run_id}/
│           ├── baskets.csv
│           ├── events.csv
│           ├── run.meta.txt
│           ├── run_config.json
│           └── SOURCE.txt
├── postgres/                     # volume
└── logs/
```

### 4.3 Windows worker layout (unchanged MT5 paths + thin agent)

```text
MetaQuotes/Terminal/<id>/
  MQL5/Files/FEMA_AI/             # local mirror
Common/Files/FEMA_AI/             # demo preferred (FILE_COMMON)
Tester/.../Agent-*/MQL5/Files/FEMA_AI/

C:\FEMA-worker\                   # NEW small agent
  sync.ps1                        # copy → ops host incoming/
  heartbeat.json
  config.json                     # destination, magic, preset
```

---

## 5. Data model (Postgres sketch)

```text
certificates (id, version, json, active_from)
runs (
  run_id PK, role, preset, symbol, tf,
  window_start, window_end, ea_build, magic,
  artifact_uri, registered_at, notes
)
baskets (
  run_id FK, basket_id, open_time, close_time,
  net, pf_contrib..., max_depth, bars_alive, ...
  schema_version
)
events (run_id, ts, event_type, payload jsonb)
health_snapshots (
  ts, run_id_or_source, score, ladder,
  would_pause_new, components jsonb, cert_version
)
candidates (
  id, parent, subsystem, status, failure_reason, run_id
)
gate_evaluations (
  ts, candidate_id, gate_id, pass, detail jsonb
)
sync_heartbeats (
  source, last_mtime, bytes, ok, detail
)
```

**Invariant:** Artifact files are immutable; DB rows are derived and re-ingestable.

---

## 6. Services (Compose)


| Service                    | Image / build         | Ports           | Responsibility                                 |
| -------------------------- | --------------------- | --------------- | ---------------------------------------------- |
| `postgres`                 | `postgres:16`         | 5432 (internal) | Evidence DB                                    |
| `minio`                    | `minio/minio`         | 9000            | Run blobs                                      |
| `fema-ops`                 | build `AI/Dockerfile` | —               | `health`, `ingest`, `gate-*`, cron entrypoints |
| `fema-api`                 | build `ops/api`       | 8080            | Read-only REST                                 |
| `sync-receiver` (optional) | tiny nginx/sftp       | 22/443          | Accept Windows drops                           |


**API surface (MVP):**

```text
GET /v1/status
GET /v1/certificate
GET /v1/health/latest
GET /v1/runs?role=demo|lock|candidate
GET /v1/runs/{run_id}
GET /v1/runs/{run_id}/baskets?limit=
```

Auth: static bearer token for agents; no write endpoints in MVP.

---

## 7. Pipelines

### 7.1 Demo cadence (EL4)

1. EA writes Common `FEMA_AI/*`
2. Windows `sync.ps1` every N minutes (or on file size change) → `/var/fema/incoming/demo/`
3. `fema_ops ingest --source demo` → copy to `artifacts/runs/{run_id}/` + upsert Postgres
4. `fema_ops health --source demo` → `health_snapshots` + STATUS
5. Stale alert if market session and no CSV growth / heartbeat miss

### 7.2 Tester / Discovery

1. Tester finishes → Agent CSVs
2. Sync as `role=candidate|lock|collect`
3. `register` + optional `gate-check`
4. Human promote only (existing EL2 checklist)

### 7.3 Contract tests (CI on git push)

- JSON Schema validate certificate + sample CSVs
- Unit tests: weights sum, G1, lock-confirm, persistence
- Compose smoke: `fema-ops health` on golden fixture

---

## 8. Mapping to current FEMA IDs


| Existing          | Ops-plane extension                                           |
| ----------------- | ------------------------------------------------------------- |
| INF-LOG / schemas | CI contract tests + DB columns typed to v2                    |
| INF-EXPORT        | Windows→Linux sync replaces “Agent archaeology”               |
| INF-CERT          | Versioned rows in `certificates`                              |
| INF-RUN           | Postgres `runs` + MinIO artifacts (file KB can remain mirror) |
| INF-OPS           | Containerized jobs on ops host                                |
| INF-DOCKER        | Expand compose: postgres + api + minio                        |
| INF-STATUS        | Served by API; generated from DB                              |
| EL4–EL6           | Depend on reliable demo ingest + heartbeats                   |
| EL7               | Trigger table reads `health_snapshots` persistence            |
| INF-DEF           | Still deferred: MT5 Docker, auto-promote, live retune         |


Suggested new track IDs (when chartered): `INF-OPS-HOST` · `INF-SYNC` · `INF-DB` · `INF-API`.

---

## 9. Hardware / sizing (MVP)


| Node           | Spec (starting)                                   |
| -------------- | ------------------------------------------------- |
| Windows worker | 4–8 vCPU, 16 GB RAM, SSD; MT5 + network to broker |
| Linux ops      | 2–4 vCPU, 8 GB RAM, 100+ GB SSD                   |
| Network        | Worker can reach ops on SSH/SFTP or VPN only      |


Single-box phase: run Compose on same Windows via WSL2 **only for Postgres/API**; prefer split hosts when demo must stay up while you rebuild containers.

---

## 10. Security

- Ops API read-only; no promote endpoint
- Sync credentials scoped to drop zone
- No broker passwords in ops host
- Gitignore: CSVs, `.env`, artifacts
- Certificate/preset changes only via PR + human EL2/EL3

---

## 11. Implementation phases


| Phase  | Deliverable                                            | Exit                                       |
| ------ | ------------------------------------------------------ | ------------------------------------------ |
| **P0** | Windows sync → `incoming/` + stale heartbeat in STATUS | Demo CSVs visible without unlocking Common |
| **P1** | Postgres + ingest from drop zone                       | `runs`/`baskets` queryable                 |
| **P2** | Read-only FastAPI                                      | Agents use `/v1/status`                    |
| **P3** | MinIO/artifacts immutability + CI schemas              | Rehydrate DB from blobs                    |
| **P4** | Dedicated Windows tester queue (optional)              | Discovery jobs don’t fight demo            |


EA code changes: **none required** for P0–P2 if Common logging already works (v1.26). Optional later: flush/rotate CSV on basket close to ease locks.

---

## 12. Risks & mitigations


| Risk                          | Mitigation                                                                |
| ----------------------------- | ------------------------------------------------------------------------- |
| Exclusive CSV locks           | Sync copies via share-read or post-close snapshot; never analyze in-place |
| Dual sources (tester vs demo) | Explicit `source=` and `role=` on every run                               |
| Schema drift                  | Version bump + CI fail                                                    |
| Overbuilding                  | No K8s/UI/auto-promote until EL4 demo health trusted                      |


---

## 13. Success criteria

1. Demo fingerprint + last sync age visible in `/v1/status` without opening MT5.
2. Health on **demo** baskets, not mistaken Tester collect.
3. Any historical `run_id` rehydratable from artifacts.
4. Cursor/agent can answer “is the edge healthy?” via API in one call.
5. PRODUCTION preset/EA logic unchanged.

---

## 14. Recommendation

Adopt the **Ops Plane** as the next infra track (charter as `INF-OPS-HOST` / extend INF-DOCKER), sequenced **P0 sync → P1 Postgres → P2 API**. Keep `edgelifecycle.md` as the process spine; this file is the **deployment architecture** for compensating Tester/Terminal limits without touching the execution engine.

**Full prioritized backlog:** see **§16** (infra + §15.3 gaps in wave order).

---

## Relation to other docs


| Doc                                              | Role                                  |
| ------------------------------------------------ | ------------------------------------- |
| `[edgelifecycle.md](edgelifecycle.md)`           | Process spine (INF-* / EL-*)          |
| `[edgescaleuproadmap.md](edgescaleuproadmap.md)` | Weekly ESR build order                |
| `[edgecontainment.md](edgecontainment.md)`       | Vision / bands / ladder               |
| `infrascaleup.md` **(this file)**                | Ops-plane tech stack, folders, phases |
| `[AI/DOCKER.md](AI/DOCKER.md)`                   | Current Python-only Docker notes      |


---

## 15. Remaining gaps (research / platform vision)

Aspirational gaps beyond the Ops Plane MVP. **EA execution engine stays frozen.** Prefer extending this file + `[edgelifecycle.md](edgelifecycle.md)`; do not create a competing architecture spine. Archive/overlap docs (`aiedgecontain.md`, `ai_enhance.md`) stay supporting references.

### 15.1 Already covered (do not rebuild)


| Gap item                                       | Current artifact                                               |
| ---------------------------------------------- | -------------------------------------------------------------- |
| Rolling health windows 50/100/250              | Certificate + `health_v0`                                      |
| Full Edge Discovery trigger (concept)          | Ladder `re_discovery` · EL7 process (trigger table still thin) |
| Human-in-the-loop / no auto production         | EL2 checklist · pause default OFF · INF-DEF                    |
| Basket lifecycle + failure + some exec quality | `fema_*_v2` · ORDER_FAIL · depth/bars/MAE                      |
| Store experiments (success + fail)             | KB `candidates.csv` · `run_id`s · EL1/EL2                      |
| Parent/child presets (basic)                   | `fema_ops clone` · `parent` · EL0 lineage                      |
| Version production / certificate (basic)       | Preset + cert JSON · `cert-confirm` · `ea_build`               |
| Docs hierarchy (start)                         | `edgelifecycle` · `infrascaleup` · `AI/STATUS`                 |


### 15.2 Partial — finish before new platforms


| Gap                             | What’s missing                                                                  |
| ------------------------------- | ------------------------------------------------------------------------------- |
| Edge Observatory / daily health | Templates exist; need **demo** ingest cadence (EL4) + scheduled report          |
| Edge lineage                    | Explicit promotion chain + retired parent on EL7/EL8                            |
| Versioning                      | Formal versions for health formula, `gate_rules`, KB snapshot — not only cert   |
| Data collection                 | Regime / market fingerprint / env metadata mostly missing on baskets            |
| Candidate factory               | `clone` is manual one-subsystem; goal-driven subsystem recommend is next        |
| Lifecycle naming                | Same loop as EL0–EL8 under richer labels — alias map, don’t fork a second spine |
| Governance                      | Implicit (operator); write RACI one-pager                                       |
| Research loop                   | Same as Re-Discovery narrative — SOP once EL4/EL5 trusted                       |


### 15.3 Gap backlog (source list)

#### Edge intelligence

- Define **Market Fingerprint** schema (volatility, trend persistence, liquidity, session, pullback distribution, EMA geometry, etc.).
- Define **Edge Genome** (where the EA thrives vs fails) and use it for market compatibility scoring.
- Create an **Edge Observatory** that generates daily health reports instead of relying on raw metrics.

#### Health & monitoring

- Define retraining policy: feature retrain cadence · AI model retrain cadence · full Edge Discovery trigger.
- Rolling health windows (50/100/250) — **done in certificate**; keep policy docs aligned.

#### Candidate factory

- Evolve from manual candidate creation to **goal-driven candidate generation**.
- AI should recommend **which subsystem** to optimize instead of searching the whole parameter space.
- Offline only; human still clones/promotes.

#### Knowledge base

- Add **Market Fingerprints** to every run.
- Add **Edge Lineage**: parent preset · child preset · promotion chain.
- Store every experiment (successful and failed) — largely done; deepen with fingerprint + lineage.

#### Versioning

Version everything:

- Production preset
- Certificate
- Health model (`health_v0` → `health_vN`)
- Feature store
- Knowledge base
- AI models (shadow / offline only)
- Validation rules (`gate_rules`)

Suggested artifact: `AI/kb/versions.json` (or Postgres `certificates` / config tables on Ops host).

#### Edge lifecycle (alias map — do not fork spine)

Expanded names map onto existing EL IDs:


| Expanded name        | Lifecycle ID            |
| -------------------- | ----------------------- |
| Discover             | EL1                     |
| Validate             | EL2                     |
| Lock                 | EL3                     |
| Deploy               | EL4                     |
| Observe              | EL5                     |
| Watch / Investigate  | EL5 ladder              |
| Generate candidate   | EL7 → factory / `clone` |
| Validate (candidate) | EL2                     |
| Promote              | EL2 + EL3               |
| Archive / Retire     | EL8                     |


#### Documentation

Consolidate AI documentation into one hierarchy:

- `edgelifecycle.md` — process / governance
- `infrascaleup.md` — deployment / infra (this file)
- Remaining AI docs → supporting / archive references (no overlapping architectures)

#### Long-term infrastructure (Edge Operations Platform)

Product name for phased Ops Plane capabilities (not a single big-bang build):

- Edge Observatory
- Health Engine
- Drift Detection
- Candidate Factory
- Knowledge Base
- Validation Engine
- Promotion Pipeline (human-gated)
- Archive System

Phasing stays **P0 sync → P1 Postgres → P2 API** (§11); intelligence features consume that plane.

#### Governance

- Define who approves: candidate creation · promotion · retirement.
- Keep **human-in-the-loop**; no automatic production changes.

#### Data collection

Expand telemetry to include:

- Market fingerprint
- Regime label
- Feature distributions
- Execution quality
- Basket lifecycle
- Failure reason
- Environment metadata

Prefer offline derivation + richer CSV columns only when necessary (minimal EA change).

#### Research framework (permanent loop)

- Detect drift
- Explain degradation
- Generate hypotheses
- Create candidates
- Validate
- Promote or reject
- Archive findings

This is the permanent research loop for keeping the edge alive — same as EL5→EL7→EL1→EL2→EL3, written as an SOP.

### 15.4 Park / dilute (charter or premature)

- AI model retrain as a **driver of live trading** before demo health is trusted
- Automated Generate → Validate → Promote without human gates
- Full “Edge Operations Platform” as one build (use as umbrella name only)
- Reviving `ai_enhance` / EC2 open-time brain as the spine

### 15.5 Ruthless build order (engine unchanged)

Superseded by the full prioritized roadmap in **§16**. Short form: **Ops Plane P0–P2 + EL4 demo health → §15.3 intelligence → P3–P4 / platform umbrella**.

**Rule:** Watch / Observatory / Factory may **score and recommend**; they may not **author** PRODUCTION.

---

## 16. Comprehensive roadmap (priority order)

Single backlog: **infra scale-up (§11)** + **gap list (§15.3)** + partials (§15.2).  
Status: `todo` · `partial` · `done` · `parked`.  
IDs: `IS-…` = infra scale-up · `RG-…` = research/gap · `GOV-…` = governance/docs.

**Do not** finish all of §15.3 before infra. Waves below are sequential; items inside a wave can parallelize.

### Wave 0 — Stabilize EL4 evidence (now)


| Pri | ID            | Todo                                                                                     | Source            | Status      | Done when                                                       |
| --- | ------------- | ---------------------------------------------------------------------------------------- | ----------------- | ----------- | --------------------------------------------------------------- |
| 0.1 | `IS-EL4-01`   | Demo CSV path documented (Common `FEMA_AI` vs Tester Agent)                              | Scale-up / EL4    | **done**    | EL4 section + daily runbook                                     |
| 0.2 | `IS-EL4-02`   | Sync demo (or snapshot) → `AI/data/live` without exclusive-lock failure                  | Scale-up P0 lite  | **done**    | `ingest --source demo` + Win32 share-read                       |
| 0.3 | `IS-EL4-03`   | Stale / heartbeat fields in STATUS (last sync age, bytes, rows)                          | Scale-up P0       | **done**    | `sync_heartbeat.json` + STATUS sync row                         |
| 0.4 | `IS-EL4-04`   | Run `health` on **demo** baskets; don’t confuse with Tester collect                      | EL4 / Observatory | **partial** | Health runs; `on_demo_path` true only when demo has closed rows |
| 0.5 | `RG-OBS-01`   | Daily Observatory note: health + ladder + “do nothing” default                           | §15.3 Observatory | **done**    | `fema_ops observatory` → `observatory_daily.md`                 |
| 0.6 | `GOV-DOC-01`  | Archive banners on `aiedgecontain.md` / `ai_enhance.md` → point to lifecycle + this file | §15.3 Docs        | **done**    | Archive banners added                                           |
| 0.7 | `GOV-LIFE-01` | Publish expanded lifecycle **alias table** in `edgelifecycle.md`                         | §15.3 Lifecycle   | **done**    | Alias map under phase map                                       |


**Wave 0 exit remainder:** file lock cleared (2026-07-12 unload). Demo CSV still **header-only** (0 closed baskets this run) — `on_demo_path=true` after first basket close + re-ingest.

### Wave 1 — Ops Plane core (infra scale-up P0–P2)


| Pri | ID         | Todo                                                                                             | Source        | Status    | Done when                         |
| --- | ---------- | ------------------------------------------------------------------------------------------------ | ------------- | --------- | --------------------------------- |
| 1.1 | `IS-P0-01` | `ops/` folder + Windows `sync.ps1` → drop zone `incoming/demo\|tester`                           | §11 P0        | **done**  | `ops/sync/sync.ps1` + incoming/   |
| 1.2 | `IS-P0-02` | Compose skeleton (`postgres` + `fema_ops` + `fema_api`)                                          | §11 / Docker  | **done**  | `ops/docker-compose.yml`          |
| 1.3 | `IS-P1-01` | PostgreSQL 16 + init schema (`runs`, `baskets`, `events`, `health_snapshots`, `sync_heartbeats`) | §11 P1        | **done**  | `001_schema.sql` · `db-migrate`   |
| 1.4 | `IS-P1-02` | Ingest pipeline: live/drop zone → artifacts + upsert Postgres                                    | §11 P1        | **done**  | `fema_ops db-ingest`              |
| 1.5 | `IS-P1-03` | Distinguish `source=demo\|tester` and `role=` on every run                                       | Scale-up risk | **done**  | columns on `runs`                |
| 1.6 | `IS-P2-01` | Read-only FastAPI `/v1/status` `/health/latest` `/runs` `/certificate`                           | §11 P2        | **done**  | `ops/api/main.py`                 |
| 1.7 | `IS-P2-02` | Bearer auth; **no** write/promote endpoints                                                      | §10 Security  | **done**  | `ops/README.md`                   |
| 1.8 | `IS-CI-01` | Contract tests: schema SQL + certificate weights + API routes                                    | Scale-up §7.3 | **done**  | `AI.tests.test_wave1_ops` (3 OK)  |

**Wave 1 verify (2026-07-12):** **pass** — images `fema-ops:local` / `fema-api:local`; compose up (postgres healthy, api :8080); `docker-compose run --rm fema_ops db-migrate` + `db-ingest --from-live` (1315 baskets, `source=demo`); `/healthz` ok; `/v1/*` 401 without bearer; `/v1/status` DB-backed health 91.72 + sync heartbeat; `/v1/runs` + baskets OK. Unit: 11/11. Note: use `docker build` + `docker-compose` (compose plugin metadata broken); `fema_ops` one-shot `status` exits — use `run --rm` for migrate/ingest. Demo baskets still exclusive-locked (Wave 0).


### Wave 2 — Governance & versioning (cheap, unblocks clarity)


| Pri | ID            | Todo                                                                                               | Source           | Status    | Done when                            |
| --- | ------------- | -------------------------------------------------------------------------------------------------- | ---------------- | --------- | ------------------------------------ |
| 2.1 | `GOV-RACI-01` | RACI: who approves candidate create / promote / retire                                             | §15.3 Governance | **done**  | `AI/kb/raci.md`                      |
| 2.2 | `RG-VER-01`   | `AI/kb/versions.json` — preset, certificate, health model, gate_rules, KB                          | §15.3 Versioning | **done**  | File + STATUS cites versions         |
| 2.3 | `RG-VER-02`   | Version health formula (`health_v0` stamp on every snapshot)                                       | §15.3 Versioning | **done**  | Report + state + DB `cert_version`   |
| 2.4 | `RG-KB-01`    | Edge Lineage fields: parent · child · promotion chain · retired_run_id                             | §15.3 KB / §15.2 | **done**  | `AI/kb/lineage.json`                 |
| 2.5 | `RG-POL-01`   | Retrain / rediscovery **policy doc**: feature cadence · model cadence · EL7 Discovery trigger      | §15.3 Health     | **done**  | `AI/kb/retrain_rediscovery_policy.md`|
| 2.6 | `RG-RES-01`   | Research-loop SOP: drift → explain → hypothesize → candidate → validate → promote/reject → archive | §15.3 Research   | **done**  | `AI/kb/research_loop_sop.md` · EL7   |


### Wave 3 — Edge intelligence (consumes Waves 0–1)


| Pri | ID           | Todo                                                                                                                           | Source             | Status      | Done when                             |
| --- | ------------ | ------------------------------------------------------------------------------------------------------------------------------ | ------------------ | ----------- | ------------------------------------- |
| 3.1 | `RG-FP-01`   | Define **Market Fingerprint** schema (vol, trend persistence, liquidity, session, pullback dist, EMA geometry, …)              | §15.3 Intelligence | **done**    | `AI/schemas/market_fingerprint.schema.json` |
| 3.2 | `RG-FP-02`   | Compute fingerprint offline per window; attach to every `run_id`                                                               | §15.3 KB / Data    | **done**    | `fema_ops fingerprint` → KB + live    |
| 3.3 | `RG-GEN-01`  | Define **Edge Genome** v0 (thrive vs fail regions from Discovery table)                                                        | §15.3 Intelligence | **done**    | `AI/kb/genome_PRODUCTION.*`           |
| 3.4 | `RG-GEN-02`  | Compatibility score: fingerprint × genome → watch/investigate signal                                                           | §15.3 Intelligence | **done**    | Shadow on health + Observatory        |
| 3.5 | `RG-OBS-02`  | Observatory generates **daily** report (not raw metrics dump) from health + fingerprint + lineage                              | §15.3 Observatory  | **done**    | `observatory_daily.md` phase RG-OBS-02 |
| 3.6 | `RG-DATA-01` | Telemetry checklist: regime label, feature distributions, exec quality, env metadata (derive first; EA columns only if needed) | §15.3 Data         | **done**    | `AI/kb/telemetry_checklist.md`        |
| 3.7 | `IS-EL5-01`  | Trust EL5 on demo path (persistence 3/2 reviewed over ≥2 weeks)                                                                | EL5 / ESR-W05–06   | **blocked** | Needs Wave 0 demo unlock (not Sunday) |


### Wave 4 — Candidate factory & Re-Discovery


| Pri | ID          | Todo                                                                                    | Source        | Status      | Done when                            |
| --- | ----------- | --------------------------------------------------------------------------------------- | ------------- | ----------- | ------------------------------------ |
| 4.1 | `RG-FAC-01` | Subsystem **recommender** (offline): which search_map id to touch given genome mismatch | §15.3 Factory | **done**    | `fema_ops recommend` ≤3              |
| 4.2 | `RG-FAC-02` | Goal-driven candidate generation (one subsystem, cited hypothesis)                      | §15.3 Factory | **done**    | `fema_ops factory [--apply]`         |
| 4.3 | `IS-EL7-01` | EL7 trigger table: ladder + persistence + pause duration → open Discovery               | EL7 / §15.3   | **done**    | `AI/kb/el7_trigger_table.md` + CLI   |
| 4.4 | `IS-EL7-02` | On trigger: snapshot lock as parent/retired → EL1 window → EL2 gates → human promote    | EL7–EL8       | **done**    | Runbook + `el7-dry-run` once         |
| 4.5 | `IS-EL6-01` | Pause-new wire decision (only after `pause-check` + demo trust)                         | EL6           | **parked**  | NOT SIGNED — see `pause_policy.md`  |
| 4.6 | `RG-KB-02`  | Every experiment (pass/fail) has fingerprint + lineage + failure_reason                 | §15.3 KB      | **done**    | `experiments_index.json`             |


### Wave 5 — Ops Plane hardening (P3–P4)


| Pri | ID            | Todo                                                                                                                                                       | Source            | Status    | Done when                                    |
| --- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- | --------- | -------------------------------------------- |
| 5.1 | `IS-P3-01`    | MinIO (or immutable `artifacts/runs/{run_id}/`) + rehydrate DB from blobs                                                                                  | §11 P3            | **done**  | `artifacts-*` / `db-rehydrate`               |
| 5.2 | `IS-P3-02`    | CI schema gates on certificate, gates, fingerprint, API OpenAPI                                                                                            | §11 P3            | **done**  | `ci-gates` + `.github/workflows/ci.yml`      |
| 5.3 | `IS-P4-01`    | Dedicated Windows tester queue (Discovery jobs ≠ demo box)                                                                                                 | §11 P4            | **done**  | `ops/tester_queue/` + AER `P0`–`P6` ([`automated_edge_rediscovery_pipeline.md`](automated_edge_rediscovery_pipeline.md)) |
| 5.4 | `IS-DRIFT-01` | Drift detection job (fingerprint / health components vs birth)                                                                                             | Platform umbrella | **done**  | `fema_ops drift` + Observatory section       |
| 5.5 | `IS-PLAT-01`  | Name/document **Edge Operations Platform** modules (Observatory, Health, Drift, Factory, KB, Validation, Promotion, Archive) as *labels on shipped pieces* | §15.3 Long-term   | **done**  | `AI/kb/platform_modules.md` + §16.1 below    |


### Wave 6 — Explicitly parked (do not schedule until charter changes)


| Pri | ID        | Todo                                             | Source  | Status      | Notes                  |
| --- | --------- | ------------------------------------------------ | ------- | ----------- | ---------------------- |
| 6.1 | `PARK-01` | Auto-promote PRODUCTION                          | INF-DEF | **parked**  | Human only             |
| 6.2 | `PARK-02` | Live EMA/TP/SL/lot from AI                       | INF-DEF | **parked**  | Charter break          |
| 6.3 | `PARK-03` | MT5 inside Docker / tester farm K8s              | INF-DEF | **parked**  | Windows worker instead |
| 6.4 | `PARK-04` | AI model retrain drives live risk                | §15.4   | **parked**  | Offline shadow only    |
| 6.5 | `PARK-05` | Reopen EC2 open-time fail predictor as main path | INF-DEF | **parked**  | Fade = rolling health  |
| 6.6 | `PARK-06` | Full platform UI / multi-EA control plane        | INF-DEF | **parked**  | API first              |

**Offline Wave 6 action (2026-07-12):** Park freeze documented — [`AI/kb/wave6_park_freeze.md`](AI/kb/wave6_park_freeze.md). No PARK-* features implemented.


### Dependency sketch

```text
Wave 0 (EL4 evidence)
    └─► Wave 1 (sync → Postgres → API)
            ├─► Wave 2 (RACI, versions, lineage, policies)   [can start early]
            └─► Wave 3 (Fingerprint → Genome → Observatory+)
                    └─► Wave 4 (Factory recommend → EL7 runbook → EL6 wire?)
                            └─► Wave 5 (MinIO, CI, tester queue, drift job)
Wave 6 = parked forever until charter changes
```

### Next concrete actions (top of queue)

1. Monday+: Wave 0 demo unlock after basket close (`ingest --source demo`)
2. After 2w+ trusted demo health: `IS-EL5-01` then reconsider `IS-EL6-01` wire sign-off
3. AER overnight waves when EL7 opens (or human `-Force`); next axes prefer non-session if session DD pattern persists
4. Wave 6 stays parked until charter changes

**AER (2026-07-13):** two-terminal Re-Discovery tooling `AER-P0`…`P6` complete on this machine; PRODUCTION lock unchanged (X1 Reject / X2 Alternate). See [`automated_edge_rediscovery_pipeline.md`](automated_edge_rediscovery_pipeline.md).

**Exit for "MVP Ops Plane":** Waves 0-1 complete + `GOV-RACI-01` + `RG-VER-01`.
**Exit for "Intelligence v0":** Wave 3 items 3.1-3.5.
**Exit for "Living edge loop":** Wave 4 + trusted EL5.
**Exit for "Hardened Ops Plane":** Wave 5 (artifacts + CI + drift + module map).

---

## 16.1 Edge Operations Platform module map (IS-PLAT-01)

See also [`AI/kb/platform_modules.md`](AI/kb/platform_modules.md).

| Module | Shipped as |
| ------ | ---------- |
| Observatory | `fema_ops observatory` |
| Health Engine | `fema_ops health` / `health_v0` |
| Drift Detection | `fema_ops drift` |
| Candidate Factory | `recommend` / `factory` / `clone` |
| Knowledge Base | `AI/kb/*` |
| Validation Engine | `gate_rules` / `gate-check` |
| Promotion Pipeline | RACI + checklist + `cert-confirm` (human) |
| Archive System | `AI/data/artifacts/runs/{run_id}/` + `db-rehydrate` |
| Sync / API | `ops/sync` · `ops/api` |
| Tester Queue | `ops/tester_queue/` (enqueue · launch · drain · scorecard · decision) · AER runbook |
