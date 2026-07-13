# EL2 â€” Promote decision (EURUSD 2026)

**Date:** 2026-07-11  
**Gate data:** [`gate_rules.json`](gate_rules.json) Â· scorecard [`el2_gate_scorecard.json`](el2_gate_scorecard.json)  
**Checklist:** [`../templates/promotion_checklist.md`](../templates/promotion_checklist.md)

## Production lock (promoted)

| Field | Value |
| ----- | ----- |
| Decision | **PROMOTE / LOCK** |
| Preset | `PRODUCTION` (`P2C-001_REG_ADX30`) |
| run_id | `20260101_PRODUCTION_13c52cd9` |
| G1 | Pass vs prior BSL_25 control (PF 1.36 Â· DD 18% on canonical window) |
| G3 | Fail (GBPUSD) â€” EURUSD-only deploy |
| Human | Discovery campaign closed; System Profile locked |

## Paper rejects / demotions (dry-run through checklist)

| Row | Preset | Decision | failure_reason | Why |
| --- | ------ | -------- | -------------- | --- |
| 21 | `P2C002_ATRP70` | Reject | `regime` | 2026 PF/DD worse than BSL stack |
| 16â€“17 | ADX30 / ATRP70 **2025** | Demote stale | `other` | Slice-only; fails canonical 2026 |
| 23 | `P2D-001_SES_NO23` | Alternate (no promote) | `dd_breach` | PF 1.40 beats lock; DD +1pp fails G1 |
| 24 | `P2D-002_SES_NOFRI` | Alternate (no promote) | `dd_breach` | PF 1.38; DD +0.1pp fails G1 |
| 34 | `PRODUCTION` GBPUSD | Reject G3 | `other` | PF 0.80 â€” edge EURUSD-specific |
| 1 | `P1-BASELINE` | Reject | `other` | Steamroller; no BSL |

## Rules enforced (EL2)

1. **G1** = PF **and** DD vs PRODUCTION on the **same** window/symbol.
2. **Stale-slice** wins (wrong window) cannot promote.
3. KB `candidates.csv` carries `status` + `failure_reason` for every Discovery row.
4. **Never** auto-promote; never live-retune.

## Sign-off

EL2 polish: gates as data Â· KB scorecard regenerated Â· this decision file is the written exit for current PRODUCTION.

## AER-P6 - Candidate_X1 (20260713_020417)

| Field | Value |
| ----- | ----- |
| Decision | **REJECT** |
| Preset | `Candidate_X1` |
| run_id | `20260101_Candidate_X1_bcc8b9b0_03` |
| PF / DD | 1.477 / 19.17% |
| G1 | FAIL (bench PF 1.36 / DD 18%) |
| failure_reason | dd_breach |
| Signer | AER-P6 |
| Checklist | `kb/decisions/20260713_020417_Candidate_X1_Reject.md` |
| Notes | AER-P2/P4 session NO23 smoke; PF beats lock, DD fails G1. |

**PRODUCTION lock unchanged unless Decision=PROMOTE and human completes AER-P6-03/04.**

## AER-P6 - Candidate_X2 (20260713_020418)

| Field | Value |
| ----- | ----- |
| Decision | **ALTERNATE** |
| Preset | `Candidate_X2` |
| run_id | `20260101_Candidate_X2_bcc8b9b0` |
| PF / DD | 1.4316 / 18.13% |
| G1 | FAIL (bench PF 1.36 / DD 18%) |
| failure_reason | dd_breach |
| Signer | AER-P6 |
| Checklist | `kb/decisions/20260713_020418_Candidate_X2_Alternate.md` |
| Notes | AER-P5/P6 FriClose factory; PF beats lock, DD +0.13pp fails G1. Keep PRODUCTION. |

**PRODUCTION lock unchanged unless Decision=PROMOTE and human completes AER-P6-03/04.**
