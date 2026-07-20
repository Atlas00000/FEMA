# Localized search map (INF-PRESET / containment §6)

**Machine:** [`search_map.json`](search_map.json) · **Playbook:** [`clone_playbook.md`](clone_playbook.md)  
**Dual-lane:** [`../../doc/dual_lane_rediscovery_pipeline.md`](../../doc/dual_lane_rediscovery_pipeline.md) · **Lane B roster:** [`challenger_roster.md`](challenger_roster.md)  
**Adaptive selection (ASI):** [`../../doc/adaptive_selection_phases.md`](../../doc/adaptive_selection_phases.md) (`ASI-P8` Complete · **AI preset** `aistack`)

## Job (nutshell)

Search map is the **containment constitution** for Discovery clones — not the regime detector and not the scorer.

It answers: *which PRODUCTION input groups may move*, *which `Inp*` keys belong to each group*, and *what must never be the experiment*. Every retune must stay **one axis** so failures and wins are attributable.

| Owns | Does not own |
| ---- | ------------ |
| Legal axes + keys (`may_adapt_pairs`) | Drift detection (fingerprint / compat) |
| One-subsystem clone fence | First-try values (`DEFAULT_RECIPES` in `factory.py`) |
| Frozen keys (not a search axis) | G1 PF/DD pass (`gate_rules.json`) |
| Promotion checklist: “one subsystem diff” | Tester window / deposit (lock canonical) |

**Rule:** Only optimize the subsystem showing drift. **One subsystem per candidate clone.**

---

## How we treat PRODUCTION retuning

PRODUCTION is the **certified lock**. Retuning means: *neighbour of that lock*, not a new EA.

1. **Window unchanged** — Tester still uses the lock canonical period (e.g. `2026.01.01–2026.07.31`). Search map never sets dates.
2. **Parent is the lock (Lane A)** — Clone from current `PRODUCTION.set`; copy all frozen / non-axis keys unchanged.
3. **One axis only** — Overrides must resolve to a single `may_adapt_pairs.id`. Cross-axis diffs fail `validate_overrides`.
4. **Frozen stay copied** — Lots, risk %, magic, strategy type, execution architecture are **identity**, not search.
5. **Recipe = first poke** — Factory attaches a conservative one-key (or one-axis) recipe; human may adjust within the same axis before Tester.
6. **Measure then human** — Register → G1 vs lock → promote / reject / alternate. Never auto-promote.

If compat tags something with **no** map axis (e.g. `execution`), treat as **observe only** — no clone.

---

## Axes (may adapt)

Each **id** is a hypothesis class: “if this drifted, poke only these keys.”

### When / regime (time & filters)

| Id | Pair (intent) | Typical keys | First recipe (factory) |
| -- | ------------- | ------------ | ---------------------- |
| `adx` | ADX threshold ↔ EMA slope/sep | `InpUseAdxGate`, `InpAdxMax`, `InpAdxPeriod`, slope/sep gates | `InpAdxMax=28` (alt `25`) |
| `session` | Session blocks ↔ whitelist | `InpUseSessionBlock*`, `InpUseSessionWhitelistLdnNy` | FriClose block on |
| `htf` | HTF filter ↔ HTF EMA | `InpUseHtfFilter`, TF / EMA / slope | HTF on + EMA 200 |
| `regime_extra` | ATR% gate ↔ breakout suspend | percentile keys + `InpUseBreakoutSuspend` | ATR% gate max 70 |
| `entry_filter` | Candle confirm ↔ RSI exhaustion | confirm + RSI period/bounds | candle confirm on |

### Structure / sizing of the trade plan

| Id | Pair (intent) | Typical keys | First recipe (factory) |
| -- | ------------- | ------------ | ---------------------- |
| `ema` | EMA20 ↔ EMA Trend | `InpEmaFastPeriod`, `InpEmaTrendPeriod` | fast → 18 |
| `atr` | ATR period ↔ multiplier | `InpAtrPeriod`, `InpAtrMultiplier`, rebuild ATR | mult → 1.2 |
| `grid` | Spacing ↔ levels / depth | `InpGridLevels`, `InpMaxEntryDepth`, rebuild | depth 4 (alt levels 4) |

### Exposure / exit behaviour

| Id | Pair (intent) | Typical keys | First recipe (factory) |
| -- | ------------- | ------------ | ---------------------- |
| `basket_exit` | Basket TP ↔ SL / trail / RTE | TP/SL, trail, RTE, max basket bars | max bars 480 |
| `cooldown` | Cooldown ↔ max trades | cooldown bars (+ after SL), max open | cooldown 2 |

Full key lists live in [`search_map.json`](search_map.json) — that file is authoritative for clone validation.

### Axis selection (how an id gets chosen)

```text
compat / genome suggest_subsystems
        → normalize against search_map (aliases like execution → observe only)
        → attach DEFAULT_RECIPES[axis]
        → ≤3 cloneable for a Lane A wave
```

- Operator pass `-Subsystem` → that axis only (still must be a map id).
- EL7 `-Force` with empty recommend → default fallback wave `session`, `adx`, `grid` (still map ids).

---

## Lane A vs Lane B (same map, different parents)

Search map axes apply to **both** lanes as the legal tweak vocabulary. The lanes differ by **who the parent is** and **when** you run them.

| | **Lane A — Localized retune** | **Lane B — Multi-base challenger** |
| --- | --- | --- |
| Question | “Is a neighbour of the **current lock** better?” | “Is a lineage from **another base / kept profile** better?” |
| Parent | Always current `PRODUCTION` | Roster: `P1-BASELINE`, alternates, kept profiles — **not** the live lock |
| Diff | **Required:** one search-map subsystem | Thesis logged; usually one map axis; not overnight genetic mash |
| Naming | `Candidate_{Token}` | `Challenger_{ParentToken}_{ThesisToken}_{NN}` |
| Cap | ≤3 queued A / wave | ≤2 queued B (separate) |
| Default night / soft fade | **Yes** — A first | **No** — escalate after repeated A fails, or human hunt |
| On lose | `failure_reason` | Profile stays on roster (no amnesia) |
| On win | Promote → new lock; A thereafter clones that lock | Same G1 + human promote; old lock → archived profile |

**Shared:** Terminal B · canonical window · same G1 · frozen architecture · never auto-promote.

Lane B still should name a search-map axis as `ThesisToken` / `-Subsystem` when the thesis is a retune-style poke (e.g. `adx` off `P1-BASELINE`). Broad “rebuild the EA” is out of scope for this map.

See playbook: [`clone_playbook.md`](clone_playbook.md) · enqueue: `ops/tester_queue/enqueue.ps1` / `enqueue_lane_b.ps1`.

---

## ASI / TEP bookkeeping (`ASI-P0-05`)

Trend Expansion Predictor and other ASI gates are **selection layers**, not a thaw of frozen architecture.

| Stage | How to bookkeep |
| ----- | --------------- |
| **P1–P3** (offline / shadow) | No new `Inp*` — no clone axis required. Log `asi_track=tep` on reports. |
| **P4 candidate** (live skip) | Preset `ASI_P4_TEP_GUARD_01` · `subsystem=regime_extra` · `InpUseAiTepGate` only · gate file `FEMA_AI\tep_gate_v1.txt` · **Alternate** |
| **P5 Mode A** (mid warn log) | Preset `ASI_P5_TEP_MID_01` · TEP + `InpUseAiMidWarn` · keep separate from Mode B |
| **P5 Mode B** (early close) | Preset `ASI_P5_TEP_MID_BSL_01` · + `InpUseAiMidEarlyBsl` · `asi_track=tep_mid_bsl` · **Alternate** (own preset) |
| **P8 AI preset** (full stack) | Preset `aistack` (alias `ASI_P8_TEP_MID_BSL_01`) · TEP + mid + Mode B + regime · `asi_track=regime_tep_mid_bsl` · **AI preset** |
| **P8 research** | Preset `ASI_P8_REGIME_01` · regime only — do not deploy long-term without stack |
| **Promote bar** | Survival / guardrail holdout — **not** required to beat PRODUCTION PF on 2026 |

**Do not:** mash TEP + mid-BSL + ADX + session in one unlogged candidate · fold Mode B into Mode A/P4 · treat ASI as license to edit lots/TP/SL · skip the permissive n/WR contract in [`adaptive_selection_phases.md`](../../doc/adaptive_selection_phases.md).

---

## Frozen (do not “search”)

Philosophy (`frozen` in JSON) and hard keys (`frozen_keys_do_not_clone_as_search`):

- Lot sizing philosophy · risk model · basket management philosophy  
- Market-order execution · strategy type (pullback continuation)  
- Position sizing framework · state machine · execution architecture  
- Concrete: `InpBaseLot`, `InpRiskPercent`, `InpMagicNumber`, `InpTradePermission`, `InpManualSuspend`

Clone **copies** these from the parent unchanged — never treat them as the experiment axis.

---

## Operator checklist

- [ ] Hypothesis names **one** map `id`
- [ ] Overrides only use that id’s keys (JSON list)
- [ ] No frozen key in the override set
- [ ] Lane A → parent `PRODUCTION`; Lane B → roster parent + challenger name
- [ ] Same Tester window as the G1 lock
- [ ] Human promote only after G1
