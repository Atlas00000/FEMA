# ASI-P5 policy ADR — mid-basket steamroller warn

**ADR id:** `asi_mid_policy_v1`  
**Phase:** `ASI-P5-03`  
**Status:** **Accepted** (default = warn only) · 2026-07-19  
**Charter:** MT5 executes · Python scores · Human promotes

## Context

TEP (`ASI-P4`) may skip **opening** a basket. Track E scores **during** an open basket when grid depth first hits a milestone. Wrong action mid-basket can force BSL / cut winners — higher blast radius than open skip.

## Decision

| Mode | Behaviour | Gate |
| ---- | --------- | ---- |
| **A — Warn only (default)** | Log / shadow `P(mid_steamroller)`; no EA trade change | Always allowed after offline review |
| **B — Optional early BSL** | Close basket early when warn fires (`exit_reason=MID_WARN`) | `InpUseAiMidEarlyBsl=true` · preset `ASI_P5_TEP_MID_BSL_01` |
| **C — Stop deepen** | Freeze further grid adds | Not implemented |

**Chosen default:** **Mode A**. **Mode B** accepted as **own Alternate preset** `ASI_P5_TEP_MID_BSL_01` (2026-07-19) — do not merge into Mode A.

## Consequences

- No silent lot / TP / trail / architecture thaw.
- Mid-warn and TEP open-gate stay **separate** axes; Mode A and Mode B stay **separate presets**.
- Mode B promote bar = survival across regimes; never auto-promote to PRODUCTION.

## Non-goals

- Auto early-BSL on live Terminal A
- Tuning threshold on 2026 canonical G1 window
- Merging mid-warn into `InpUseAiTepGate`
