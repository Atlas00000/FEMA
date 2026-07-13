# Promotion checklist (filled) - AER-P6

**Candidate id:** `Candidate_X1`
**run_id:** `20260101_Candidate_X1_bcc8b9b0_03`
**Parent lock:** `PRODUCTION` (`20260101_PRODUCTION_13c52cd9`)
**Window:** `2026.01.01-2026.07.31` EURUSD M5
**Generated:** 2026-07-13T01:04:17.9947724Z
**Signer:** AER-P6

## Evidence

- [x] Same tester contract ($400 Â· every tick Â· ProfitInPips=0) - assumed from AER launch.ini
- [ ] **G1:** PF >= PRODUCTION **and** max DD <= PRODUCTION
  - Candidate PF **1.477** vs bench **1.36** -> ok
  - Candidate DD **19.17%** vs bench **18%** -> FAIL
  - Gate: **FAIL**
- [x] Not a stale-slice-only win (canonical 2026 window)
- [ ] Walk-forward / holdout note attached (or N/A) - human
- [x] Diff is one subsystem (factory / search_map)
- [x] KB decision packet written (this file + `el2_promote_decision.md`)
- [x] Human sign-off: **AER-P6** / 2026-07-13

## Forbidden

- [x] Not promoting because "AI says so"
- [x] No live EMA / TP / SL / lot / grid change
- [x] No auto-promote

## Decision

- [ ] **Promote** -> new lock + certificate bump + EL8 archive old (**manual next steps below**)
- [x] **Reject** -> `failure_reason=dd_breach` Â· keep PRODUCTION
- [ ] **Alternate** -> stay candidate; do not deploy

**Notes:** AER-P2/P4 session NO23 smoke; PF beats lock, DD fails G1.

## Next steps (human only)

1. Keep `PRODUCTION.set` on Terminal A.
2. Leave Discovery queue free for next EL7 wave (max 3).
3. Record `failure_reason=dd_breach` in candidates KB (done by this script when possible).

**Template:** `AI/templates/promotion_checklist.md`
**Signed decision log:** `AI/kb/el2_promote_decision.md`
