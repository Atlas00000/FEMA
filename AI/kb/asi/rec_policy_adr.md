# ASI-P6 policy ADR — basket recovery probability

**ADR id:** `asi_rec_policy_v1`  
**Phase:** `ASI-P6-02`  
**Status:** **Accepted** (default = shadow recommend only) · 2026-07-19  
**Charter:** MT5 executes · Python scores · Human promotes

## Context

At depth milestones, mid-warn (`ASI-P5`) estimates P(eventual steamroller). Recovery (`ASI-P6`) estimates the **complementary** question: P(finish TP/profit | open features, warn_depth). Low recovery is a signal to cut losses early; high recovery argues for **KEEP** despite stress depth.

Wrong early exit still has high blast radius — same as Mode B.

## Decision — action map

| Band | Condition | Action |
| ---- | --------- | ------ |
| **KEEP** | `P(recover) ≥ keep_threshold` (advisory ~0.55) | Continue basket; do not early-BSL |
| **CAUTION** | exit_thr < P < keep_thr | Stop-adds / reduce depth — **not wired** |
| **EARLY BSL recommend** | `P(recover) ≤ exit_threshold` | Shadow recommend; human may stack with Mode B |

**Chosen default:** **shadow recommend only**. No new MQL gate in P6 MVP. Early BSL remains opt-in via `ASI_P5_TEP_MID_BSL_01` (`InpUseAiMidEarlyBsl`).

## Relationship to mid-warn

| Score | Question | Typical use |
| ----- | -------- | ----------- |
| Mid (`y_mid_steamroller`) | Will this become a steamroller? | Warn / Mode B early close |
| Recovery (`y_recover`) | Will this still finish green? | KEEP vs recommend cut |

Do **not** replace mid-warn. Optional later: require **both** high mid-steam **and** low recover before Mode B — not in this ADR.

## Consequences

- No silent lot / TP / trail / architecture thaw.
- No auto early-BSL from recovery score alone.
- Threshold never tuned on 2026 canon G1 window.

## Non-goals

- Live Terminal A auto-action
- Merging recovery into `InpUseAiMidWarn` / TEP without a new decision
- Mode C stop-deepen implementation in P6
