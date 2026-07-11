# FEMA — Edge Scale-Up Roadmap

**Status:** Active build plan  
**Job:** Ship a **minimal Edge Ops loop** (certificate → health → pause/alert → re-Discovery trigger) without building a full quant platform.  
**Authoritative vision / gap answers:** [`edgecontainment.md`](edgecontainment.md)  
**Lifecycle charter:** [`edgelifecycle.md`](edgelifecycle.md)  
**Live lock:** [`System Profile EURUSD.md`](System%20Profile%20EURUSD.md) · Discovery log: [`Edge Discovery.md`](Edge%20Discovery.md)

> **One sentence:** Watch the living PRODUCTION edge first; candidate factory and AI retrain only after health is trusted on demo.

---

## Charter

Build the smallest system that answers, every week:

> **Is the reason PRODUCTION used to make money still true — and what do we do if not?**

MT5 **executes**. Offline Python + docs **think**. Humans **promote**.

---

## Scope

### In scope (MVP)

| # | Capability |
| - | ---------- |
| 1 | Edge **certificate** checked into repo (bands from lock + demo) |
| 2 | Rolling **health 0–100** from basket telemetry (offline) |
| 3 | Daily health update + weekly operator review |
| 4 | Action ladder (Investigate → Watch → Re-Discovery → Retire) — **human-gated** |
| 5 | Pause policy **spec** + shadow “would pause new” log (wire later) |
| 6 | Simple drift tags (market / execution / performance) — rule-based v0 |
| 7 | Candidate **knowledge base** (CSV/JSON) — every test kept |
| 8 | Candidate factory **v1** = manual preset clones + Edge Discovery G-rules |
| 9 | Doc merge: one lifecycle spine; retire overlapping AI plans as chapters |

### Explicitly out of scope (do not build yet)

| Forbidden until MVP health is trusted |
| ------------------------------------- |
| Genetic / swarm / RL auto-optimization |
| Auto-promote to PRODUCTION |
| Live EMA / TP / SL / lot / BSL changes from AI |
| Multi-EA / multi-symbol “Ops Platform” UI |
| Re-opening EC1/EC2 open-time fail predictors as the main path |
| Full walk-forward automation farm |
| Broker latency / fill microstructure lab |
| Rewriting FEMA state machine for AI |
| Requiring AI to beat 2026 demo PF |

If a task smells like the table above → **defer**, don’t sneak it into a weekly ID.

---

## Build principles (anti-overengineering)

1. **One symbol first** — EURUSD M5 PRODUCTION only.  
2. **Reuse** AI0 basket/event CSVs and existing Edge Discovery gates — don’t rebuild tester infra.  
3. **Shadow before wire** — health and pause are logs/reports until a human opts in.  
4. **Rules before models** — health v1 is weighted formula from [`edgecontainment.md`](edgecontainment.md); no new ML until Watch works.  
5. **Human promote always** — AI/scripts recommend; never deploy.  
6. **One deliverable per week** — ship something operable (doc, script, report), not architecture slides.  
7. **Stop at MVP** — freeze after Week 12; only then schedule Scale-Up Phase B.

---

## ID scheme

| Prefix | Meaning |
| ------ | ------- |
| `ESR-Wnn` | Week `nn` epic |
| `ESR-Wnn-mmm` | Task inside that week |
| `ESR-DEF-*` | Explicitly deferred (parking lot) |
| `ESR-DONE` | Exit criteria for MVP |

Aligns with lifecycle phases: Weeks 1–6 ≈ **EL3–EL5**, Weeks 7–8 ≈ **EL6**, Weeks 9–11 ≈ **EL7 + factory v1**, Week 12 ≈ doc merge / freeze.

---

## Phase overview

| Weeks | Theme | Lifecycle | Outcome |
| ----- | ----- | --------- | ------- |
| 1–2 | Certificate + telemetry | EL3 | Written bands + data contract |
| 3–4 | Health engine (offline) | EL5 | Daily score from baskets |
| 5–6 | Operator cadence | EL4–EL5 | Weekly review habit |
| 7–8 | Pause shadow + drift v0 | EL6 | Would-pause log + drift tags |
| 9–10 | Knowledge base + factory v1 | EL7 lite | Manual candidates, stored |
| 11–12 | Validation checklist + doc merge | EL2/EL8 | MVP freeze |

```text
W1–2 Certificate     W3–4 Health      W5–6 Cadence
        │                 │                 │
        └────────────┬────┴────────┬────────┘
                     ▼             ▼
              W7–8 Pause/Drift   (demo shadow)
                     │
                     ▼
              W9–10 KB + manual candidates
                     │
                     ▼
              W11–12 Gates + single doc spine · MVP FREEZE
```

---

## Week 1 — Edge certificate lock

**Epic:** `ESR-W01` · **Theme:** Write the PRODUCTION health certificate into the repo.

| ID | Task | Description | Done when |
| -- | ---- | ----------- | --------- |
| `ESR-W01-001` | Draft certificate doc | Copy Green/Amber/Red bands from [`edgecontainment.md`](edgecontainment.md) §1 into a short `AI/certificate_PRODUCTION_EURUSD.md` (or System Profile appendix). | File exists; linked from System Profile |
| `ESR-W01-002` | Bind to lock fingerprint | List journal must-haves (`adx_gate=on`, `bsl=25`, preset path). | Checklist matches live demo load |
| `ESR-W01-003` | Pick rolling windows | Confirm **50 / 100 / 250** baskets as primary windows (no more). | One sentence in certificate |
| `ESR-W01-004` | Baseline snapshot | Record lock-window reference metrics (PF/WR/DD/trades) as certificate “birth” numbers. | Table filled from Edge Discovery / System Profile |

**Out of week:** Health code, pause wiring, candidate generation.

---

## Week 2 — Telemetry contract

**Epic:** `ESR-W02` · **Theme:** Ensure demo/tester can feed health without new EA philosophy.

| ID | Task | Description | Done when |
| -- | ---- | ----------- | --------- |
| `ESR-W02-001` | Inventory fields | Map certificate metrics → existing basket/event CSV columns (or mark “derive”). | Gap table: have / derive / missing |
| `ESR-W02-002` | Fill only critical gaps | If a certificate metric is missing (e.g. depth, bars_alive), add **minimal** EA log fields — no redesign. | Logger change compiled **or** metric deferred with reason |
| `ESR-W02-003` | Demo export path | Document where demo/live CSVs land and how to copy into `AI/data/live/`. | README steps ≤10 lines |
| `ESR-W02-004` | One dry collect | Pull a recent demo or tester slice; confirm rows parse. | Sample file in `AI/data/live/` (gitignored OK) |

**Out of week:** Scoring formula implementation (next week). **Do not** add AI models.

---

## Week 3 — Health score v0

**Epic:** `ESR-W03` · **Theme:** Offline 0–100 health from weights in containment §2.

| ID | Task | Description | Done when |
| -- | ---- | ----------- | --------- |
| `ESR-W03-001` | Script `edge_health_cert.py` | Compute rolling PF, WR, TP hit, duration, depth, MAE ratio, frequency vs certificate bands → component scores → weighted 0–100. | Script runs on sample CSV |
| `ESR-W03-002` | Ladder labels | Map score → Normal / Investigate / Watch / Re-Discovery / Retire per containment §3. | Printed on report |
| `ESR-W03-003` | Persistence stub | Flag “deteriorating” only after **3** consecutive window updates (even if daily job runs once). | Flag logic unit-tested or documented with example |
| `ESR-W03-004` | JSON + MD report | Write `AI/data/live/health_latest.json` + short `.md`. | Artifacts regenerate cleanly |

**Out of week:** MT5 pause input, drift classifiers, ML.

---

## Week 4 — Health on real demo history

**Epic:** `ESR-W04` · **Theme:** Prove the score moves sensibly on *your* demo, not toy data.

| ID | Task | Description | Done when |
| -- | ---- | ----------- | --------- |
| `ESR-W04-001` | Backfill demo baskets | Export longest practical demo PRODUCTION log into `AI/data/live/`. | File dated; n baskets recorded |
| `ESR-W04-002` | Calibrate band friction | If everything is Red or everything Green, adjust **only** band edges in certificate (document why) — do not add features. | One calibration note |
| `ESR-W04-003` | Sanity vs intuition | Operator writes 5-line “does this match how demo felt?” | Note in health report |
| `ESR-W04-004` | Freeze health v0 | Tag formula version `health_v0` in JSON; no further tweaks until Week 6 review. | Version field set |

**Out of week:** Auto candidate spawn when health &lt; 70.

---

## Week 5 — Daily cadence (manual)

**Epic:** `ESR-W05` · **Theme:** Habit before automation.

| ID | Task | Description | Done when |
| -- | ---- | ----------- | --------- |
| `ESR-W05-001` | Daily runbook | Steps: export/copy CSV → run health script → glance ladder. | `AI/runbook_daily_health.md` |
| `ESR-W05-002` | Optional one-command | Tiny shell/ps1 wrapper calling the script (no scheduler required). | `AI/run_daily_health.ps1` or `.sh` |
| `ESR-W05-003` | Alert rule (human) | If ladder ≤ Watch for 3 days → ping yourself (email/Telegram optional; phone note OK). | Written rule only |
| `ESR-W05-004` | Keep PRODUCTION unchanged | Confirm no Inputs drift on demo. | Checklist tick |

**Out of week:** Cloud dashboards, multi-account monitors.

---

## Week 6 — Weekly operator review

**Epic:** `ESR-W06` · **Theme:** Containment §11 weekly slice — decisions, not dashboards.

| ID | Task | Description | Done when |
| -- | ---- | ----------- | --------- |
| `ESR-W06-001` | Weekly template | Sections: health trend, certificate breaches, action ladder decision, “do nothing” default. | `AI/templates/weekly_edge_review.md` |
| `ESR-W06-002` | First real weekly | Fill template once from demo. | Saved under `AI/data/live/reviews/` |
| `ESR-W06-003` | Action discipline | If Investigate: report only. If Watch: queue **offline** candidate ideas (no live change). | Decision logged |
| `ESR-W06-004` | MVP Watch gate | Declare “health trusted enough to design pause shadow” or list blockers. | Go / no-go note |

**Out of week:** Monthly walk-forward automation.

---

## Week 7 — Pause policy shadow

**Epic:** `ESR-W07` · **Theme:** Containment §4 — pause **new** only; shadow first.

| ID | Task | Description | Done when |
| -- | ---- | ----------- | --------- |
| `ESR-W07-001` | Spec in System Profile | Allowed / forbidden pause list copied from containment. | Profile or lifecycle updated |
| `ESR-W07-002` | Shadow column | Health report adds `would_pause_new` when ladder ≤ Re-Discovery (or Critical persistence). | Field in JSON/MD |
| `ESR-W07-003` | Replay check | On backfilled demo: count % of days/baskets that would pause; must not be “always on.” | One paragraph metrics |
| `ESR-W07-004` | Wire decision | Explicit **no wire** this week unless go-criteria met (optional later epic). | Decision logged |

**Out of week:** EA `InpAiPauseNew` live on demo (defer to `ESR-DEF-PAUSE-WIRE`).

---

## Week 8 — Drift tags v0 (rules)

**Epic:** `ESR-W08` · **Theme:** Containment §8 simplified — classify, don’t overfit.

| ID | Task | Description | Done when |
| -- | ---- | ----------- | --------- |
| `ESR-W08-001` | Three tags only | Implement **Market / Execution / Performance** rule tags (skip Feature Drift ML for now). | Tags on weekly report |
| `ESR-W08-002` | Market rules | e.g. ATR or duration distribution shift vs certificate birth window. | Documented thresholds |
| `ESR-W08-003` | Execution rules | Spread rejects / spread points vs baseline. | Documented thresholds |
| `ESR-W08-004` | Map tag → action | Market→candidate queue; Execution→broker note; Performance→health ladder only. | Table in runbook |

**Out of week:** Feature-importance drift, model retraining pipelines.

---

## Week 9 — Knowledge base v0

**Epic:** `ESR-W09` · **Theme:** Containment §9 — store every candidate, including failures.

| ID | Task | Description | Done when |
| -- | ---- | ----------- | --------- |
| `ESR-W09-001` | Schema file | JSON/CSV columns: id, parent, diffs, window, symbol, PF, WR, DD, status, failure_reason. | `AI/kb/schema.md` |
| `ESR-W09-002` | Store bootstrap | Enter PRODUCTION + baseline + any known Discovery rejects as rows. | `AI/kb/candidates.csv` started |
| `ESR-W09-003` | Failure reason enum | Short list from containment (ATR expand, deep pullback, …). | Enum in schema |
| `ESR-W09-004` | Add-row helper | Script or template to append one candidate after a tester run. | One CLI or MD checklist |

**Out of week:** Vector DB, web UI, auto lesson LLM.

---

## Week 10 — Candidate factory v1 (manual)

**Epic:** `ESR-W10` · **Theme:** Containment §5–§6 — clones only; localized knobs.

| ID | Task | Description | Done when |
| -- | ---- | ----------- | --------- |
| `ESR-W10-001` | Search map card | One-pager: may-adapt pairs vs frozen (from containment §6). | In Edge Discovery or KB |
| `ESR-W10-002` | Clone playbook | How to fork PRODUCTION → Candidate_Xn with **one subsystem** changed. | Playbook ≤1 page |
| `ESR-W10-003` | Queue from health | If weekly ladder = Watch: create **≤3** manual candidates, not 30. | Queue logged in KB |
| `ESR-W10-004` | Run offline tests | Tester on agreed window; log results into KB (pass or fail). | ≥1 candidate fully logged |

**Out of week:** Auto param sweep, genetic search, parallel agent farm.

---

## Week 11 — Validation & promotion checklist

**Epic:** `ESR-W11` · **Theme:** Containment §7 — evidence, not “AI says so.”

| ID | Task | Description | Done when |
| -- | ---- | ----------- | --------- |
| `ESR-W11-001` | Promotion checklist | Walk-forward / OOS / vs PRODUCTION / G-rules / human sign-off. | `AI/templates/promotion_checklist.md` |
| `ESR-W11-002` | Link Edge Discovery gates | Reuse existing G1 (and friends); do not invent a second scoreboard. | Checklist cites Edge Discovery |
| `ESR-W11-003` | Dry-run promote | Paper-promote or paper-reject the Week 10 candidate through the checklist. | Signed decision in KB |
| `ESR-W11-004` | Re-Discovery trigger table | When health/persistence says Re-Discovery → open EL1 campaign (process only). | Table in lifecycle / this roadmap |

**Out of week:** Auto-promote scripts.

---

## Week 12 — Doc merge & MVP freeze

**Epic:** `ESR-W12` · **Theme:** Containment §12 — one spine; stop building.

| ID | Task | Description | Done when |
| -- | ---- | ----------- | --------- |
| `ESR-W12-001` | Spine update | Make [`edgelifecycle.md`](edgelifecycle.md) the TOC; point chapters to containment certificate/health, this roadmap, Edge Discovery, System Profile. | Lifecycle top links updated |
| `ESR-W12-002` | Archive banners | Mark [`aiedgecontain.md`](aiedgecontain.md) / [`ai_enhance.md`](ai_enhance.md) as tooling/archive chapters (not competing roadmaps). | Banner lines added |
| `ESR-W12-003` | MVP freeze list | List what shipped (certificate, health_v0, cadence, pause shadow, KB, factory v1). | `ESR-DONE` section filled |
| `ESR-W12-004` | Phase B parking only | Move temptations to `ESR-DEF-*`; **no new builds** until 2–4 weeks of stable weekly reviews. | Parking lot dated |

---

## MVP exit (`ESR-DONE`)

MVP is done when **all** are true:

- [ ] Certificate published and linked to PRODUCTION fingerprint  
- [ ] `health_v0` runs on demo export without manual spreadsheet heroics  
- [ ] Daily runbook + at least **4** weekly reviews completed  
- [ ] Pause remains shadow (or explicitly deferred wire with reason)  
- [ ] KB has PRODUCTION + ≥1 candidate row with failure/success reason  
- [ ] Promotion checklist used once (even if reject)  
- [ ] Single doc spine; no parallel “AI strategy of the week”

**Then stop.** Operate the loop. Only open Phase B if Watch is boringly reliable.

---

## Deferred parking lot (`ESR-DEF`)

| ID | Item | Why deferred |
| -- | ---- | ------------ |
| `ESR-DEF-PAUSE-WIRE` | EA input to pause new baskets from health file/flag | After shadow false-positive rate known |
| `ESR-DEF-FEATURE-DRIFT` | Feature-distribution / importance drift | Needs stable feature store; not MVP |
| `ESR-DEF-AUTO-FACTORY` | Auto candidate generation / genetic search | Containment explicitly Phase-later |
| `ESR-DEF-WF-FARM` | Automated walk-forward battery | Manual checklist first |
| `ESR-DEF-MULTI-EA` | Platform for FEG+VRG+… | One EA proof first |
| `ESR-DEF-EC2-RETRY` | Reopen open-time fail predictor | Failed transfer; not the lifecycle path |
| `ESR-DEF-LIVE-TUNE` | Any live param AI | Forbidden by charter |

---

## Weekly operating rhythm (after Week 5)

| When | Owner | Action | ID ref |
| ---- | ----- | ------ | ------ |
| Daily | You | Export → health script → glance ladder | `ESR-W05` |
| Weekly | You | Fill weekly review; decide Investigate / Watch / nothing | `ESR-W06` |
| On Watch | You | ≤3 manual candidates → tester → KB | `ESR-W10` |
| On Re-Discovery | You | New Edge Discovery campaign; no live retune | `ESR-W11-004` |
| Never | AI/EA | Auto-promote or live TP/SL/EMA edit | Scope out |

---

## Relation to other docs

| Doc | Role after this roadmap |
| --- | ------------------------ |
| **`edgescaleuproadmap.md` (this file)** | **Weekly build plan** — what to implement when |
| [`edgecontainment.md`](edgecontainment.md) | Vision + **answered gaps** (certificate, formula, ladder, …) |
| [`edgelifecycle.md`](edgelifecycle.md) | Charter / phase IDs (EL0–EL8) |
| [`aiedgecontain.md`](aiedgecontain.md) | Offline contain experiments — archive/tooling chapter |
| [`Edge Discovery.md`](Edge%20Discovery.md) | Discovery lab + promote gates |
| [`System Profile EURUSD.md`](System%20Profile%20EURUSD.md) | Frozen PRODUCTION fingerprint |

---

## Immediate next step

Start **`ESR-W01`**: publish `AI/certificate_PRODUCTION_EURUSD.md` from containment §1 bands and link it from System Profile — still **no** new AI models.
