# Decision — ASI-P8 regime intelligence (shadow)

**Date:** 2026-07-19  
**Candidate:** ASI-P8 regime taxonomy + policy map  
**Verdict:** **Alternate** — offline shadow only; **not** promoted; no MQL wire

## Evidence

| Item | Result |
| ---- | ------ |
| Taxonomy | 9 regimes at open (rule-based) |
| Research scorecard | 1820 baskets · overall PF ~1.00 |
| Lock slice | `pullback_trend` healthy (PF ~1.47) → allow upgrade |
| Skip set | **empty** (permissive) |
| Caution | `false_breakout`, `grind`, `rotation` |

## Policy

Accepted ADR [`../asi/regime_policy_adr.md`](../asi/regime_policy_adr.md): allow / caution / skip with lock override; default shadow-only.

## Consequences

- PRODUCTION unchanged
- No new EA inputs
- Regime map informs later Track J / Discovery notes — does not auto-skip
