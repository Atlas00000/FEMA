# Promotion checklist (filled) - AER-P6 / DLR-P1

**Candidate id:** `Challenger_P1BASE_adx_01`
**run_id:** `(unknown - fill from kb/runs)`
**Lane / parent / role:** `B` / `P1-BASELINE` / `challenger`
**profile_id:** `prof_Challenger_P1BASE_adx_01`
**subsystem:** `adx`
**Parent lock (G1 bench):** `PRODUCTION` (`20260101_PRODUCTION_13c52cd9`)
**Window:** `2026.01.01-2026.07.31` EURUSD M5
**Generated:** 2026-07-14T13:43:45.5652764Z
**Signer:** p2_smoke

## Evidence

- [x] Same tester contract ($400 Â· every tick Â· ProfitInPips=0) - assumed from AER launch.ini
- [ ] **G1:** PF >= PRODUCTION **and** max DD <= PRODUCTION
  - Candidate PF **1.1** vs bench **1.36** -> FAIL
  - Candidate DD **22%** vs bench **18%** -> FAIL
  - Gate: **FAIL**
- [x] Not a stale-slice-only win (canonical 2026 window)
- [ ] Walk-forward / holdout note attached (or N/A) - human
- [x] Diff is one subsystem (factory / search_map)
- [x] KB decision packet written (this file + `el2_promote_decision.md`)
- [x] Human sign-off: **p2_smoke** / 2026-07-14

## Forbidden

- [x] Not promoting because "AI says so"
- [x] No live EMA / TP / SL / lot / grid change
- [x] No auto-promote

## Decision

- [ ] **Promote** -> new lock + certificate bump + EL8 archive old (**manual next steps below**)
- [x] **Reject** -> `failure_reason=pf_breach` Â· keep PRODUCTION
- [ ] **Alternate** -> stay candidate; do not deploy

**Notes:** 

## Next steps (human only)

1. Keep `PRODUCTION.set` on Terminal A.
2. Leave Discovery queue free for next EL7 wave (max 3).
3. Record `failure_reason=pf_breach` in candidates KB (done by this script when possible).

**Template:** `AI/templates/promotion_checklist.md`
**Signed decision log:** `AI/kb/el2_promote_decision.md`
