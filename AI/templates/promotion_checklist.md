# Promotion checklist (EL2 / ESR-W11 / containment §7)

**Candidate id:** _______________  
**run_id:** _______________  
**Parent lock:** `PRODUCTION` (`20260101_PRODUCTION_13c52cd9`)  
**Window:** must be `2026.01.01`–`2026.07.31` EURUSD M5 unless symbol Discovery

## Evidence (all required)

- [ ] Same tester contract ($400 · every tick · ProfitInPips=0)
- [ ] **G1:** PF ≥ PRODUCTION **and** max DD ≤ PRODUCTION ([`gate_rules.json`](../kb/gate_rules.json))
- [ ] Not a **stale-slice-only** win (e.g. 2025-only ATRP70)
- [ ] Walk-forward / holdout note attached (or explicitly N/A with reason)
- [ ] Diff is **one subsystem** ([`search_map.md`](../kb/search_map.md))
- [ ] KB row updated (`candidates.csv` status + `failure_reason` if reject)
- [ ] Human sign-off name/date: _______________

## Forbidden

- [ ] Not promoting because “AI says so”
- [ ] No live EMA / TP / SL / lot / grid change
- [ ] No auto-promote

## Decision

- [ ] **Promote** → new lock + certificate bump + EL8 archive old
- [ ] **Reject** → `failure_reason=` _______________ · keep PRODUCTION
- [ ] **Alternate** → stay candidate; do not deploy

**Signed decision path:** `AI/kb/el2_promote_decision.md` (append or replace section).
