# ASI-P8 policy ADR — regime allow / caution / skip

**ADR id:** `asi_regime_policy_v1`
**Phase:** `ASI-P8-03`
**Status:** Accepted (shadow only) · 2026-07-19
**Charter:** MT5 executes · Python scores · Human promotes

## Decision

| Action | Regimes | Live behaviour |
| ------ | ------- | -------------- |
| **allow** | `liquidity_vacuum`, `impulse`, `expansion`, `exhaustion`, `compression`, `pullback_trend` | Trade normally |
| **caution** | `false_breakout`, `grind`, `rotation` | Log only; no skip |
| **skip** | — | Shadow recommend skip at open |

Default: **shadow recommend only**. No `InpUseAiRegime*` in P8 MVP.

## Rules

- Skip only if research n≥40, PF<0.85, steam≥1.25× baseline, net<0
- Calibrate PF≥1.0 vetoes skip → caution
- Prefer missed skips over false blocks

## Non-goals

- No silent lot / architecture thaw
- No mash with TEP/mid in one Discovery job
- No tune on 2026 canon
