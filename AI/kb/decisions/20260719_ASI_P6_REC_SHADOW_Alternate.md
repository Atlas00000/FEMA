# Decision — ASI-P6 recovery probability (shadow)

**Date:** 2026-07-19  
**Candidate:** ASI-P6 recovery model (`y_recover` · exit_thr ~0.341)  
**Verdict:** **Alternate** — offline shadow only; **not** promoted; no MQL wire

## Evidence

| Window | Signal |
| ------ | ------ |
| Calibrate 2025 mid-rows | AUC 0.612 · exit ~5% · fail prec 0.58 · net exit set −$332 |
| 2018–2025 shadow | exit baskets net **−$1341** · fail prec ~0.59 |
| Promote-frozen slice | Weak fail precision — reinforces no auto-act |

## Policy

Accepted ADR [`../asi/rec_policy_adr.md`](../asi/rec_policy_adr.md):

- KEEP / CAUTION / early-BSL **recommend** bands documented
- Default = **shadow recommend only**
- Early BSL remains Mode B preset only

## Consequences

- PRODUCTION unchanged
- No new EA inputs
- Keep artifacts under `AI/kb/asi/rec_*` for later combine experiments
