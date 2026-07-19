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

## AER-P6 / DLR-P1 - Candidate_X2 (20260714_143251)

| Field | Value |
| ----- | ----- |
| Decision | **ALTERNATE** |
| Preset | `Candidate_X2` |
| lane / parent / role | `A` / `PRODUCTION` / `candidate` |
| profile_id | - |
| subsystem | session |
| run_id | `20260101_Candidate_X2_bcc8b9b0` |
| PF / DD | 1.4316 / 18.13% |
| G1 | FAIL (bench PF 1.36 / DD 18%) |
| failure_reason | dd_breach |
| Signer | dlr_p1_smoke |
| Checklist | `kb/decisions/20260714_143251_Candidate_X2_Alternate.md` |
| Notes |  |

**PRODUCTION lock unchanged unless Decision=PROMOTE and human completes AER-P6-03/04.**

## AER-P6 / DLR-P1 - DLR_P1_VERIFY_DUMMY (20260714_143632)

| Field | Value |
| ----- | ----- |
| Decision | **REJECT** |
| Preset | `DLR_P1_VERIFY_DUMMY` |
| lane / parent / role | `A` / `PRODUCTION` / `candidate` |
| profile_id | - |
| subsystem | adx |
| run_id | `(unknown - fill from kb/runs)` |
| PF / DD | 1.2 / 20% |
| G1 | FAIL (bench PF 1.36 / DD 18%) |
| failure_reason | pf_breach |
| Signer | verify_p01 |
| Checklist | `kb/decisions/20260714_143632_DLR_P1_VERIFY_DUMMY_Reject.md` |
| Notes |  |

**PRODUCTION lock unchanged unless Decision=PROMOTE and human completes AER-P6-03/04.**

## AER-P6 / DLR-P1 - Lookup_Tag (20260714_143633)

| Field | Value |
| ----- | ----- |
| Decision | **REJECT** |
| Preset | `Lookup_Tag` |
| lane / parent / role | `A` / `PRODUCTION` / `candidate` |
| profile_id | - |
| subsystem | htf |
| run_id | `(unknown - fill from kb/runs)` |
| PF / DD | 1.1 / 22% |
| G1 | FAIL (bench PF 1.36 / DD 18%) |
| failure_reason | pf_breach |
| Signer | verify_lookup |
| Checklist | `kb/decisions/20260714_143633_Lookup_Tag_Reject.md` |
| Notes |  |

**PRODUCTION lock unchanged unless Decision=PROMOTE and human completes AER-P6-03/04.**

## AER-P6 / DLR-P1 - Challenger_P1BASE_adx_01 (20260714_144322)

| Field | Value |
| ----- | ----- |
| Decision | **REJECT** |
| Preset | `Challenger_P1BASE_adx_01` |
| lane / parent / role | `B` / `P1-BASELINE` / `challenger` |
| profile_id | prof_Challenger_P1BASE_adx_01 |
| subsystem | adx |
| run_id | `(unknown - fill from kb/runs)` |
| PF / DD | 1.1 / 22% |
| G1 | FAIL (bench PF 1.36 / DD 18%) |
| failure_reason | pf_breach |
| Signer | p2_smoke |
| Checklist | `kb/decisions/20260714_144322_Challenger_P1BASE_adx_01_Reject.md` |
| Notes |  |

**PRODUCTION lock unchanged unless Decision=PROMOTE and human completes AER-P6-03/04.**

## AER-P6 / DLR-P1 - Challenger_P1BASE_adx_01 (20260714_144345)

| Field | Value |
| ----- | ----- |
| Decision | **REJECT** |
| Preset | `Challenger_P1BASE_adx_01` |
| lane / parent / role | `B` / `P1-BASELINE` / `challenger` |
| profile_id | prof_Challenger_P1BASE_adx_01 |
| subsystem | adx |
| run_id | `(unknown - fill from kb/runs)` |
| PF / DD | 1.1 / 22% |
| G1 | FAIL (bench PF 1.36 / DD 18%) |
| failure_reason | pf_breach |
| Signer | p2_smoke |
| Checklist | `kb/decisions/20260714_144345_Challenger_P1BASE_adx_01_Reject.md` |
| Notes |  |

**PRODUCTION lock unchanged unless Decision=PROMOTE and human completes AER-P6-03/04.**

## AER-P6 / DLR-P1 - Challenger_P1BASE_adx_02 (20260714_144416)

| Field | Value |
| ----- | ----- |
| Decision | **ALTERNATE** |
| Preset | `Challenger_P1BASE_adx_02` |
| lane / parent / role | `B` / `P1-BASELINE` / `challenger` |
| profile_id | prof_Challenger_P1BASE_adx_02 |
| subsystem | - |
| run_id | `(unknown - fill from kb/runs)` |
| PF / DD | 1 / 25% |
| G1 | FAIL (bench PF 1.36 / DD 18%) |
| failure_reason | dd_breach |
| Signer | p2_smoke2 |
| Checklist | `kb/decisions/20260714_144416_Challenger_P1BASE_adx_02_Alternate.md` |
| Notes |  |

**PRODUCTION lock unchanged unless Decision=PROMOTE and human completes AER-P6-03/04.**

## AER-P6 / DLR-P1 - Challenger_P2_VERIFY_ALT (20260714_145618)

| Field | Value |
| ----- | ----- |
| Decision | **ALTERNATE** |
| Preset | `Challenger_P2_VERIFY_ALT` |
| lane / parent / role | `B` / `P1-BASELINE` / `challenger` |
| profile_id | prof_Challenger_P2_VERIFY_ALT |
| subsystem | adx |
| run_id | `(unknown - fill from kb/runs)` |
| PF / DD | 1.45 / 18.5% |
| G1 | FAIL (bench PF 1.36 / DD 18%) |
| failure_reason | dd_breach |
| Signer | dlr_p2_verify |
| Checklist | `kb/decisions/20260714_145618_Challenger_P2_VERIFY_ALT_Alternate.md` |
| Notes |  |

**PRODUCTION lock unchanged unless Decision=PROMOTE and human completes AER-P6-03/04.**

## AER-P6 / DLR-P1 - Challenger_P2_VERIFY_REJ (20260714_145619)

| Field | Value |
| ----- | ----- |
| Decision | **REJECT** |
| Preset | `Challenger_P2_VERIFY_REJ` |
| lane / parent / role | `B` / `Candidate_X2` / `challenger` |
| profile_id | prof_Challenger_P2_VERIFY_REJ |
| subsystem | - |
| run_id | `(unknown - fill from kb/runs)` |
| PF / DD | 1 / 25% |
| G1 | FAIL (bench PF 1.36 / DD 18%) |
| failure_reason | pf_breach |
| Signer | dlr_p2_verify |
| Checklist | `kb/decisions/20260714_145619_Challenger_P2_VERIFY_REJ_Reject.md` |
| Notes |  |

**PRODUCTION lock unchanged unless Decision=PROMOTE and human completes AER-P6-03/04.**

## AER-P6 / DLR-P1 - Candidate_DLR_P3_A (20260714_150516)

| Field | Value |
| ----- | ----- |
| Decision | **REJECT** |
| Preset | `Candidate_DLR_P3_A` |
| lane / parent / role | `A` / `PRODUCTION` / `candidate` |
| profile_id | prof_Candidate_DLR_P3_A |
| subsystem | adx |
| run_id | `20260101_Candidate_DLR_P3_A_p3smoke` |
| PF / DD | 1.41 / 19.5% |
| G1 | FAIL (bench PF 1.36 / DD 18%) |
| failure_reason | dd_breach |
| Signer | dlr_p3_smoke |
| Checklist | `kb/decisions/20260714_150516_Candidate_DLR_P3_A_Reject.md` |
| Notes |  |

**PRODUCTION lock unchanged unless Decision=PROMOTE and human completes AER-P6-03/04.**

## ERG-P7 - ERG_P3_adx_ADX28_01 (20260716_190850)

| Field | Value |
| ----- | ----- |
| Decision | **REJECT** |
| Preset | `ERG_P3_adx_ADX28_01` |
| lane / parent / role | `B` / `P1-BASELINE→BSL25` / `research_survivor` |
| profile_id | `prof_ERG_P3_adx_ADX28_01` |
| subsystem | adx |
| run_id | `mt5_canon_20260716` |
| PF / DD | 1.21 / 24.62% (eq 27.27%) · Net +147.86 · 443 trades |
| G1 | FAIL dual (bench PF 1.36 / DD 18%) |
| failure_reason | pf_breach (also dd_breach) |
| Signer | human (ERG-P7) |
| Checklist | `kb/decisions/20260716_190850_ERG_P3_adx_ADX28_01_Reject.md` |
| Pack | `doc/ERG_P6_g1_pack.md` |
| Notes | 2021–25 research centre; canon underperforms PRODUCTION (ADX30). Not a lock successor. |

**PRODUCTION lock unchanged.** Keep `PRODUCTION.set` (BSL25 + ADX30 + TP10).

## ASI-P5 Mode B - ASI_P5_TEP_MID_BSL_01 (20260719)

| Field | Value |
| ----- | ----- |
| Decision | **ALTERNATE** (own preset) |
| Preset | `ASI_P5_TEP_MID_BSL_01` |
| lane / parent / role | `A` / `ASI_P5_TEP_MID_01` / `guardrail_candidate` |
| profile_id | `prof_ASI_P5_TEP_MID_BSL_01` |
| subsystem | regime_extra |
| Promote bar | Survival across regimes (not beat PRODUCTION) |
| 2026 | PF 1.44 · DD~19% · net +200 · n 409 |
| 2018–25 | PF 1.35 · DD~23% · net +162 · n 517 |
| Checklist | `kb/decisions/20260719_ASI_P5_TEP_MID_BSL_01_Alternate.md` |
| Pack | `doc/ASI_P5_midbasket_pack.md` |
| Notes | Keep separate from Mode A / P4 / PRODUCTION. |

**PRODUCTION lock unchanged.**
