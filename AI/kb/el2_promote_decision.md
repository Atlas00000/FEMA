# EL2 — Promote decision (EURUSD 2026)

**Date:** 2026-07-11  
**Gate data:** [`gate_rules.json`](gate_rules.json) · scorecard [`el2_gate_scorecard.json`](el2_gate_scorecard.json)  
**Checklist:** [`../templates/promotion_checklist.md`](../templates/promotion_checklist.md)

## Production lock (promoted)

| Field | Value |
| ----- | ----- |
| Decision | **PROMOTE / LOCK** |
| Preset | `PRODUCTION` (`P2C-001_REG_ADX30`) |
| run_id | `20260101_PRODUCTION_13c52cd9` |
| G1 | Pass vs prior BSL_25 control (PF 1.36 · DD 18% on canonical window) |
| G3 | Fail (GBPUSD) — EURUSD-only deploy |
| Human | Discovery campaign closed; System Profile locked |

## Paper rejects / demotions (dry-run through checklist)

| Row | Preset | Decision | failure_reason | Why |
| --- | ------ | -------- | -------------- | --- |
| 21 | `P2C002_ATRP70` | Reject | `regime` | 2026 PF/DD worse than BSL stack |
| 16–17 | ADX30 / ATRP70 **2025** | Demote stale | `other` | Slice-only; fails canonical 2026 |
| 23 | `P2D-001_SES_NO23` | Alternate (no promote) | `dd_breach` | PF 1.40 beats lock; DD +1pp fails G1 |
| 24 | `P2D-002_SES_NOFRI` | Alternate (no promote) | `dd_breach` | PF 1.38; DD +0.1pp fails G1 |
| 34 | `PRODUCTION` GBPUSD | Reject G3 | `other` | PF 0.80 — edge EURUSD-specific |
| 1 | `P1-BASELINE` | Reject | `other` | Steamroller; no BSL |

## Rules enforced (EL2)

1. **G1** = PF **and** DD vs PRODUCTION on the **same** window/symbol.
2. **Stale-slice** wins (wrong window) cannot promote.
3. KB `candidates.csv` carries `status` + `failure_reason` for every Discovery row.
4. **Never** auto-promote; never live-retune.

## Sign-off

EL2 polish: gates as data · KB scorecard regenerated · this decision file is the written exit for current PRODUCTION.
