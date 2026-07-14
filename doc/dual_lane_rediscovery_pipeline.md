# Hybrid Dual-Lane Re-Discovery Pipeline

**Status:** **`DLR-P3` complete** (2026-07-14) · hybrid dual-lane MVP  
**Charter:** MT5 executes · Python scores · Human promotes  
**IDs:** `DLR-*` (Dual-Lane / Hybrid Rediscovery)  
**Parent snapshot:** [`edge_rediscovery_system.md`](edge_rediscovery_system.md)  
**Shipped Lane A tooling:** [`../automated_edge_rediscovery_pipeline.md`](../automated_edge_rediscovery_pipeline.md) (`AER-P0`…`P6`)  
**Roster:** [`../AI/kb/challenger_roster.md`](../AI/kb/challenger_roster.md)  
**EL7 policy:** [`../AI/kb/dlr_policy.json`](../AI/kb/dlr_policy.json) · [`../ops/tester_queue/el7_policy.ps1`](../ops/tester_queue/el7_policy.ps1)

### Adopted way forward

> Dual-lane — **Lane A** retunes **PRODUCTION**; **Lane B** keeps **multiple challenger bases** (`P1-BASELINE`, alternates, kept profiles) on the same G1 / human-promote rail — without genetic free-for-alls, auto-promote, or thawing frozen architecture (lots · execution · strategy type).

---

## 1. Problem → hybrid answer

| Issue | Hybrid answer |
| ----- | ------------- |
| PRODUCTION was tuned on one Discovery path; cloning only that lock **tunnels** the EA into the first winner’s neighbourhood | **Lane B** branches from a **roster of bases**, not only PRODUCTION |
| Soft fade still needs cheap, attributable fixes | **Lane A** one-axis clones of the **live lock** only |
| Unlimited broad search overfits | Caps · same canonical window · shared G1 · human promote |

Lane A: “Is a neighbour of the **current lock** better?”  
Lane B: “Is a lineage from **another base / kept profile** better than the lock?”

---

## 2. Hybrid model

```text
Bases (roster)
  · PRODUCTION        → Lane A only (live lock retune)
  · P1-BASELINE       → Lane B challenger parent
  · kept alternates   → Lane B challenger parents (profile cards)
  · past near-misses  → stay in roster after lose (no amnesia)

EL7 / human
    ├─ Lane A: parent=PRODUCTION · one search-map axis · ≤3/wave
    └─ Lane B: parent∈roster\{lock} · ≤1–2/cycle · human-scoped
              │
              ▼
         Terminal B queue (tagged lane · parent · role · profile_id)
              │
              ▼
         sync → register → G1 vs PRODUCTION lock
              │
              ▼
         scorecard (A vs B pedigrees vs lock) → human decide
              │
              ├─ promote → new lock · Lane A follows new parent
              └─ reject/alternate → keep/update profile card on roster
```

| | **Lane A — Localized** | **Lane B — Multi-base challenger** |
| --- | --- | --- |
| **Parent** | Always current `PRODUCTION` lock | Roster: `P1-BASELINE`, alternates, kept profiles |
| **Diff** | One search-map subsystem | Thesis logged; not overnight genetic mash |
| **Wave cap** | ≤3 per EL7 / Forced night | ≤1–2 per Discovery **cycle** (not every night) |
| **When** | Soft decay · first EL7 wave · default overnight | Repeated A fails · hunt · refresh a roster base |
| **Bookkeeping** | `lane=A` · `parent=PRODUCTION` · `role=candidate` | `lane=B` · `parent=<base>` · `role=challenger` · `profile_id` |
| **On lose** | `failure_reason` | Still a **profile** on the roster (no single-winner amnesia) |
| **On win** | AER-P6 promote | New lock; old PRODUCTION → archived profile; roster updated |
| **Frozen** | Search-map freeze | Architecture freeze (lots / execution / strategy type) |

**Shared:** Terminal B · canonical window · `$400` · every tick · `ProfitInPips=0` · never demo CSV · never auto-promote · never Discovery on PRODUCTION chart.

---

## 3. Challenger roster & profile cards

Lane B is not “one alternate preset.” It is a **small living roster**.

| Concept | Meaning |
| ------- | ------- |
| **Base** | Parent `.set` / preset id you may branch from (`P1-BASELINE`, `PRODUCTION` only for A, etc.) |
| **Profile card** | KB row: preset · parent · window · PF/DD · G1 · status (`alternate`/`reject`/`lock`) · `run_id` · notes |
| **Roster** | Bases + profiles still eligible for Lane B enqueue |

**Rule:** Beating or losing does not erase the profile — promote changes the **lock**; the roster keeps challenger memory so future hunts are not PRODUCTION-only.

Initial roster seeds (examples): `P1-BASELINE` · close G1 alternates (e.g. session near-misses) · any explicit research stack the operator adds.

---

## 4. Compare & promote policy

1. Scorecard shows **lane · parent · profile** vs PRODUCTION bench.  
2. **G1** (PF **and** DD) mandatory for promote — both lanes.  
3. Prefer **one** promote per cycle.  
4. PF-win / DD-fail → `alternate` + stay on roster.  
5. Promoted B becomes new PRODUCTION; Lane A thereafter clones **that** lock.  
6. Demoted lock stays as an archived profile (eligible for later B if operator wants).

---

## 5. Default operating policy

| Situation | Action |
| --------- | ------ |
| Soft decay / first EL7 wave | **Lane A** ≤3 |
| Compat green · Discovery closed | Idle — or `-Force` **A** only |
| Repeated A fails (same family) | Next cycle schedule **1× B** from roster |
| Operator hunt / new regime thesis | **B** from chosen base (human-scoped) |
| After B loses | Keep profile; do not delete base |

---

## 6. Implementation phases & IDs

Build **phase order**. Code starts at Phase 1 only after this charter is accepted.

### Phase 0 — Charter & adopt · `DLR-P0` · **COMPLETE**

| ID | Task | Status | Done when |
| -- | ---- | ------ | --------- |
| `DLR-P0-01` | Hybrid dual-lane charter in `doc/` | **done** | This file |
| `DLR-P0-02` | Snapshot/changelog updated on edge rediscovery system | **done** | [`edge_rediscovery_system.md`](edge_rediscovery_system.md) |
| `DLR-P0-03` | FEMA constraints written (no genetic / auto-promote / thaw) | **done** | §2–3 + §7 Non-goals |
| `DLR-P0-04` | Adopt across STATUS · audit · playbook · EL7 · AER pointer | **done** | Linked docs (2026-07-14) |

**Exit:** Design adopted; no code required. **Phase 0 closed 2026-07-14.** Next: `DLR-P1-01`.

#### Adoption record

| Field | Value |
| ----- | ----- |
| Decision | **ADOPT** hybrid dual-lane (multi-base Lane B) |
| Date | 2026-07-14 |
| Charter one-liner | See header “Adopted way forward” |
| Code | None in P0 — Lane A remains shipped AER |
| Next ID | _(hybrid MVP closed — ops continue via EL7 runbook)_ |

### Phase 1 — Schema & Lane A tagging · `DLR-P1` · **COMPLETE**

| ID | Task | Status | Done when |
| -- | ---- | ------ | --------- |
| `DLR-P1-01` | Queue fields: `lane` · `parent` · `role` · `profile_id` | **done** | `queue.json` schema `fema_tester_queue_v1` + `enqueue.ps1` (default `lane=A`, `parent=PRODUCTION`) |
| `DLR-P1-02` | Scorecard columns for lane / parent / role | **done** | `scorecard.ps1` → `fema_dlr_p1_scorecard_v0` |
| `DLR-P1-03` | Decision pack records lane / parent / profile | **done** | `decision.ps1` + checklist + `fema_dlr_p1_decision_v0` |
| `DLR-P1-04` | Lane A = existing factory path explicitly tagged | **done** | `el7_enqueue` stamps `lane=A` / `parent=PRODUCTION` |
| `DLR-P1-05` | Lane A one-axis + max-3 wave guards | **done** | Parent/role/subsystem/search_map + max 3 queued A |

**Exit:** Today’s AER behaviour preserved; every new job tagged as Lane A. **Phase 1 closed 2026-07-14.** Next: `DLR-P2-01`.

### Phase 2 — Multi-base Lane B · `DLR-P2` · **COMPLETE**

| ID | Task | Status | Done when |
| -- | ---- | ------ | --------- |
| `DLR-P2-01` | Challenger roster artifact (JSON/MD seeds: `P1-BASELINE` + alternates) | **done** | [`AI/kb/challenger_roster.json`](../AI/kb/challenger_roster.json) |
| `DLR-P2-02` | Profile-card fields on candidates / decisions | **done** | [`AI/kb/profiles/`](../AI/kb/profiles/) + decision upsert |
| `DLR-P2-03` | Enqueue Lane B from chosen base (`-Lane B -Parent …`) | **done** | `enqueue_lane_b.ps1` + `enqueue.ps1` Lane B path |
| `DLR-P2-04` | Lane B cycle cap ≤1–2 separate from A | **done** | max 2 queued B (roster `policy.max_queued_lane_b`) |
| `DLR-P2-05` | On reject/alternate: upsert profile onto roster (no delete) | **done** | `decision.ps1` → `Upsert-FemaProfileCard` |
| `DLR-P2-06` | Naming convention for challenger presets | **done** | [`challenger_roster.md`](../AI/kb/challenger_roster.md) |

**Exit:** Can run 1× B from `P1-BASELINE` (or an alternate) beside Lane A without amnesia on lose. **Phase 2 closed 2026-07-14.** Next: `DLR-P3-01`.

### Phase 3 — Policy, smoke, ops surface · `DLR-P3` · **COMPLETE**

| ID | Task | Status | Done when |
| -- | ---- | ------ | --------- |
| `DLR-P3-01` | EL7 policy: default A; escalate B after N A-fails | **done** | [`dlr_policy.json`](../AI/kb/dlr_policy.json) + [`el7_policy.ps1`](../ops/tester_queue/el7_policy.ps1) + EL7 runbook |
| `DLR-P3-02` | Smoke: 1x A + 1x B -> scorecard compare | **done** | [`smoke_dlr_p3.ps1`](../ops/tester_queue/smoke_dlr_p3.ps1) · `dlr_p3_smoke_latest.json` |
| `DLR-P3-03` | STATUS + system_audit mention hybrid dual-lane | **done** | Linked docs (2026-07-14) |
| `DLR-P3-04` | Reconfirm promote = human AER-P6 only | **done** | Policy `auto_promote=false` · `decision.ps1` refuses G1-fail Promote · no Terminal A swap |

**Exit (hybrid MVP):** Phase 1–2 done + `DLR-P3-02` smoke green; Lane A safe; multi-base B visible on scorecard. **Phase 3 closed 2026-07-14 — hybrid MVP complete.**

```text
AER-P0…P6 (shipped · Lane A tooling)
    └─► DLR-P0 charter · COMPLETE
            └─► DLR-P1 schema + A tags · COMPLETE
                    └─► DLR-P2 roster + B enqueue · COMPLETE
                            └─► DLR-P3 policy + smoke · COMPLETE  ◄ hybrid MVP
```

---

## 7. Non-goals (FEMA constraints)

- Genetic / multi-EA optimizer farm  
- Auto-promote of either lane  
- Lane B every night by default  
- Thawing frozen architecture (lot philosophy · execution · strategy type)  
- TradingView as G1 authority  
- Discovery on Terminal A / live PRODUCTION chart  

---

## 8. Related

| Doc | Role |
| --- | ---- |
| [`edge_rediscovery_system.md`](edge_rediscovery_system.md) | Discover snapshot + changelog |
| [`../automated_edge_rediscovery_pipeline.md`](../automated_edge_rediscovery_pipeline.md) | Shipped single-lane AER |
| [`../AI/kb/search_map.md`](../AI/kb/search_map.md) | Lane A axes |
| [`../AI/kb/clone_playbook.md`](../AI/kb/clone_playbook.md) | Clone SOP |
| [`localizaed_tuning.md`](localizaed_tuning.md) | Why not only broad Discovery |
| [`../AI/kb/el7_rediscovery_runbook.md`](../AI/kb/el7_rediscovery_runbook.md) | EL7 steps |
| [`../AI/kb/dlr_policy.json`](../AI/kb/dlr_policy.json) | Dual-lane EL7 policy |
| [`../AI/kb/challenger_roster.md`](../AI/kb/challenger_roster.md) | Lane B roster |
