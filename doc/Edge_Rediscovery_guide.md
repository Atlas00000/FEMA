# Edge Rediscovery Guide

**Role:** Isolate the FEMA edge from **P1-BASELINE 2021–2025**, then refine **trade quality, failure containment, and exits** — one axis at a time.  
**Charter:** MT5 executes · Python scores · Human promotes  
**Updated:** 2026-07-15  
**Evidence:** P1-BASELINE Strategy Tester report · EURUSD M5 · **2021.01.01–2025.12.31** · $400 · Every tick · 100% history quality  
**Parent guide:** `[backtesting_guide.md](backtesting_guide.md)` · Baseline DNA `[baseline_profile.md](baseline_profile.md)` · Discover plane `[edge_rediscovery_system.md](edge_rediscovery_system.md)` · Axes `[../AI/kb/search_map.md](../AI/kb/search_map.md)`

> **Not a promote-from-2021–2025 path.** Extended-window diagnosis → one-axis presets → IS/VAL → **canonical G1** (`2026.01.01–2026.07.31`) vs PRODUCTION. Stale-slice wins do not promote.

---

## 0. Verdict on this run (read first)


| Metric             | P1-BASELINE 2021–2025 | What it means                          |
| ------------------ | --------------------- | -------------------------------------- |
| Net profit         | **+$936.62**          | Edge exists in aggregate               |
| Profit factor      | **2.21**              | Headline looks strong                  |
| Max DD bal / eq    | **36.1% / 40.6%**     | Path is not deployable as-is           |
| Recovery factor    | **1.10**              | Profit barely covers one max DD        |
| Trades / WR        | **687 / 95.8%**       | High-hit, small-win machine            |
| Avg win / avg loss | **+$2.60 / −$26.61**  | ~**10:1** loss asymmetry               |
| Largest loss       | **−$152**             | Single steamroller ≫ weeks of TPs      |
| Avg / max hold     | **~9d / ~297d**       | Bag-holding losers                     |
| Corr(profit, MFE)  | **0.15**              | Wins capped — TP not capturing runners |
| Corr(profit, MAE)  | **0.76**              | Losses scale with adverse excursion    |


**One-liner:** The strategy **harvests many good pullbacks**, then **pays them back** in a few unbounded (or late-contained) failures. Rediscovery focus is **failure containment + toxic-condition filters + exit discipline** — not more entries.

**Do not confuse windows:**


| Window                                | Role this cycle                                                                    |
| ------------------------------------- | ---------------------------------------------------------------------------------- |
| **2021–2025**                         | Characterisation / IS diagnosis for P1-BASELINE (this report)                      |
| **Canonical `2026.01.01–2026.07.31`** | G1 vs PRODUCTION before any promote                                                |
| Prior EL0 note                        | Same P1 stack on 2026 → PF **0.17**, DD **66%** — steamroller **regime-dependent** |


So: the 4-year PF 2.21 proves the *shape* of the edge; it does **not** license promoting an unbounded grid. PRODUCTION already fixed the worst with **BSL $25 + ADX<30**; this guide hunts **additive** quality controls that survive one-axis tests and G1.

---

## 1. Fundamental edge profile (wins vs losses)

### 1.1 What the wins are

```text
EMA trend bias → shallow ATR pullback → grid fills → basket TP (~$10)
```


| Property                             | Evidence                                                                |
| ------------------------------------ | ----------------------------------------------------------------------- |
| High hit rate                        | ~96% long/short win rates                                               |
| Small absolute wins                  | Avg profit **$2.60**; largest win **$11.10**                            |
| Fast-or-medium resolution when right | Many TPs; low MFE→profit correlation → **you exit winners early/fixed** |
| Directionally flat edge              | Long WR 97.7% · Short WR 95.5% — not a long-only quirk                  |
| Works across the day                 | Profit bars present Asia → London → NY; not session-exclusive           |


**Edge hypothesis (frozen):** In an EMA20/EMA100 trend, shallow ATR-spaced pullbacks revert enough that a **small basket TP** fires often. Quality lives in **mean-reversion continuation after pullback**, not in trend-riding.

### 1.2 What the losses are


| Property              | Evidence                                                                                                          |
| --------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Rare but catastrophic | 29 loss trades vs 658 wins — **4.2% of trades, ~45% of absolute P&L mass** (gross loss −771 vs gross profit 1708) |
| Asymmetric R          | Avg loss ≈ **10×** avg win                                                                                        |
| MAE-linear wipe       | Corr(profit, MAE) **0.76** + outlier near −170: adverse excursion **is** the loss                                 |
| Bag-holding           | Max hold **7129h (~297d)**; avg hold **213h** — losers are nursed until ruin or rare recovery                     |
| Clustered failure     | Consecutive-losses contribution to DD **−756** — one steamroller episode can erase months                         |


**Failure hypothesis:** When pullbacks **do not revert** (trend expansion / breakout / thin liquidity), the grid **adds depth**, equity sinks, and without hard containment the exit is a **fat tail**. This is classic **pennies in front of a steamroller**.

### 1.3 What we already know from Discovery lineage

Do not re-learn settled stack facts blindly — re-test only with **named presets** and **one axis**.


| Known                             | Evidence                                | Implication for ERG                                                             |
| --------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------- |
| Raw P1 = steamroller              | EL0 PF 0.17 on 2026; this run DD 36–40% | Containment is mandatory                                                        |
| **BSL $25** is the big lever      | Path P1 → P2A-002_BSL_25 → PRODUCTION   | Re-prove BSL on 2021–25 **before** exotic exits                                 |
| **ADX<30** lifts BSL → lock       | PRODUCTION PF 1.36 / DD 18%             | Regime gate already earns its keep                                              |
| Session NO23 helps PF, DD fragile | P2D-001 / Candidate_X1: PF↑ DD≥18       | Session = priority toxin; DD still the bar                                      |
| Trail 50 / RTE rejected on G1     | P2E-003, P2E-001                        | Exit experiments need new thesis **or** different activation — not blind re-run |
| HTF H1/H4 rejected                | P2B-001/002                             | Do not re-open HTF early                                                        |
| ATR%70 can hurt                   | P2C002                                  | `regime_extra` is last resort, careful                                          |


---

## 2. Sessions & structure: when it performs vs fails

From the report histograms (diagnosis only — **not** yet filters to ship):

### 2.1 By hour


| Signal                    | Observation                     | Working hypothesis                                                                                             |
| ------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Hour 23 loss spike**    | Dominant red bar in P&L-by-hour | Rollover / thin book / gap risk → **block new entries** (`InpUseSessionBlockNo23`) — prior Discovery nearly G1 |
| Entries peak **13–16**    | NY open / overlap               | Liquidity is available; not inherently toxic                                                                   |
| Asia / London still green | Steady small blue bars          | Edge not exclusive to NY                                                                                       |
| Overnight holds into 23   | Avg hold days                   | Session block alone may not close open baskets — pair with **max basket bars** or BSL                          |


### 2.2 By weekday


| Signal                   | Observation       | Working hypothesis                                                                                  |
| ------------------------ | ----------------- | --------------------------------------------------------------------------------------------------- |
| **Tuesday loss outlier** | Large red P&L bar | Likely **few large baskets**, not “Tuesday alpha” — investigate via basket CSVs before blocking Tue |
| Wed–Fri profit bias      | Blue dominates    | Do **not** whitelist Wed–Fri only until Tuesday losses are catalogued (overfit risk)                |
| Fri entry dip            | Fewer entries     | Soft filter candidate later (`FriClose`) — already Alternate on X2                                  |


### 2.3 By month


| Signal               | Observation            | Working hypothesis                                                                                     |
| -------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------ |
| **December blow-up** | Outlier red month      | Holiday / thin liquidity / trend continuation — candidate **calendar block** or tighter ADX/ATR in Dec |
| Other months         | Relatively steady blue | Edge is “most of the year” — good for containment thesis                                               |


### 2.4 Strengths map (optimise toward)

```text
STRENGTHS                          WEAKNESSES
─────────────────────              ─────────────────────────────
High WR small TP hits              Fat-tail MAE losses
Works both long & short            Unbounded / late exits (no BSL here)
Profit across most hours           Hour-23 toxicity
Liquidity windows (Ldn/NY)         Dec / thin-liq regimes
Pullback mean-reversion            Trend-expansion / steamroller
                                   Bag-holding (max hold months)
```

**Optimisation principle:** Protect the high-frequency small wins; **cut the right tail of losses**. Raising WR further is secondary — **loss size control** is primary.

---

## 3. Problem statement (this rediscovery cycle)


| Problem             | Target                                                      | Not the target                                |
| ------------------- | ----------------------------------------------------------- | --------------------------------------------- |
| Trade quality       | Fewer entries into doomed steamrollers                      | Random filter stacking                        |
| Failure containment | Cap MAE → loss before DD > lock                             | Hope grid averages out                        |
| Exit & management   | Bound hold time; optional trail **after** containment works | Trail that cuts winners without cutting tails |
| PF / DD jointly     | Improve PF **without** DD > PRODUCTION                      | PF-only or WR-only victories                  |


**Success criteria (write before next tests):**


| Gate        | Extended research (2021–25 splits)                                 | Canonical G1                   |
| ----------- | ------------------------------------------------------------------ | ------------------------------ |
| Containment | Balance DD ≤ **25%** on IS stitch (pre-G1 screen)                  | DD ≤ **18%** vs PRODUCTION     |
| Quality     | Gross loss ÷ gross profit ↓ vs P1 raw; avg loss / avg win ≤ **6×** | PF ≥ **1.36**                  |
| Sample      | ≥ **200** trades on research stretch for screen                    | Same window / contract as lock |
| Discipline  | **One search-map axis** per preset                                 | Human promote only             |


---

## 4. Process rules (from `backtesting_guide.md`)

1. **One axis per preset** — `adx` *or* `session` *or* `basket_exit` *or* `regime_extra` … never mash in one load.
2. **Parent is explicit** — start Lane B from `P1-BASELINE` for isolation; compare survivors to `PRODUCTION` on canonical.
3. **Time splits on 2021–2025** (example — document actual dates in run meta):

```text
2021.01 – 2022.12   IS      (develop)
2023.01 – 2024.06   VAL     (select ≤3 survivors)
2024.07 – 2025.12   HOLD    (one look — no retune)
2026.01 – 2026.07   CANON   (G1 vs PRODUCTION)
```

1. **Holdout sacred** — fail holdout ⇒ stop that thesis; do not sand the same holdout.
2. **Sensitivity** — for any survivor, ±10–20% on the tuned key; need a plateau.
3. **Cost stress** — re-run survivor with worse spread before promote.
4. **No auto-promote · no stale-slice promote.**

---

## 5. Preset naming (context load-and-test)

**Pattern:**

```text
ERG_{PhaseId}_{Axis}_{Thesis}_{NN}.set
```


| Token     |                              | Examples                                             |
| --------- | ---------------------------- | ---------------------------------------------------- |
| `ERG`     | Edge Rediscovery Guide cycle | fixed                                                |
| `PhaseId` | Phase id below               | `P1`, `P2`, `P3`                                     |
| `Axis`    | Search-map subsystem         | `bexit`, `session`, `adx`, `regime`, `entry`, `grid` |
| `Thesis`  | Short human thesis           | `BSL25`, `NO23`, `ADX30`, `MaxBars480`, `Trail50`    |
| `NN`      | Variant                      | `01`, `02`                                           |


**Header comment (required in every preset file):**

```text
; ID: ERG_P2_session_NO23_01
; parent=P1-BASELINE | axis=session | phase=ERG-P2
; thesis: Block new entries hour 23 (rollover toxin)
; research_window=2021.01.01-2025.12.31 | canon=2026.01.01-2026.07.31
; compare_to: P1 raw + PRODUCTION G1
; status: ready_to_test | pass_is | fail_hold | canon_g1 | reject
```

**Load path:** Terminal B → Inputs → load `Presets/ERG_….set` → run Tester with documented window → sync/register → score.

**Lane B enqueue mirror** (optional, same thesis):

```text
Challenger_P1BASE_{axis}_{NN}   e.g. Challenger_P1BASE_session_01
```

Keep ERG name as the **human load presets**; Challenger name if using queue automation.

---

## 6. Phases & task IDs (one task at a time)

Work **top → bottom**. Do not start `ERG-P4` before containment (`ERG-P1`) is proven on research splits. Each ID is a single shippable task.

---

### ERG-P0 — Document & baseline (no code)

**Status: complete · 2026-07-15** · Pack: `[ERG_P0_baseline_pack.md](ERG_P0_baseline_pack.md)` · `run_id` `20210101_P1-BASELINE_60e646e5`


| ID            | Task                                                                   | Done when                                                                     |
| ------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **ERG-P0-01** | Archive this P1 2021–25 report metrics into Run KB / note file         | **Done** — metrics + window hash `60e646e5`                                   |
| **ERG-P0-02** | Export / sync baskets+events for the run (if Agent logged)             | **Done (partial)** — CSVs archived; **TP-only gap** (0 loss exits in baskets) |
| **ERG-P0-03** | Catalogue the worst N losses (hour, weekday, month, depth, bars_alive) | **Done** — MT5 loss profile + top-15 MAE paths; Tue ≥2 steamrollers           |
| **ERG-P0-04** | Freeze success criteria (§3) signed by operator                        | **Done** — frozen in P0 pack                                                  |


**Output:** Loser atlas + frozen hurdles. **No new filters yet.** → next **ERG-P1-01**.

---

### ERG-P1 — Failure containment (`basket_exit` / BSL)

**Status: ERG-P1 closed · BSL25 centre · MaxBars rejected** · Pack: `[ERG_P1_containment_pack.md](ERG_P1_containment_pack.md)`

**Thesis:** Cap steamroller MAE. Without this, session/ADX cannot save bag-holds.


| ID             | Task                                                    | Preset(s)                                                                                               | Keys (one axis)                                |
| -------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **ERG-P1-01**  | Replicate BSL $25 on P1 parent (known good containment) | `[ERG_P1_bexit_BSL25_01](../Presets/ERG_P1_bexit_BSL25_01.set)`                                         | `InpUseBasketSl=true`, `InpBasketSl=25`        |
| **ERG-P1-02**  | Softer / tighter BSL probe (plateau, not hunt)          | `[BSL20_01](../Presets/ERG_P1_bexit_BSL20_01.set)` · `[BSL30_01](../Presets/ERG_P1_bexit_BSL30_01.set)` | `InpBasketSl` only                             |
| **ERG-P1-03**  | Time stop: max basket bars                              | `[MaxBars480_01](../Presets/ERG_P1_bexit_MaxBars480_01.set)`                                            | `InpMaxBasketBars=480` (~40h M5) — after BSL25 |
| **ERG-P1-03b** | MaxBars on BSL25 parent                                 | `[MaxBarsBSL_01](../Presets/ERG_P1_bexit_MaxBarsBSL_01.set)`                                            | MaxBars only vs BSL25                          |
| **ERG-P1-04**  | Score IS → VAL; reject if DD not ↓ vs P1 raw            | —                                                                                                       | Compare DD, avg loss, RF                       |


**Pass screen (research):** DD↓ materially vs P1 raw; avg loss / avg win ≤ 6×; PF may fall (acceptable if DD collapses).

**Known:** BSL25 already in PRODUCTION — P1-01 is the **control bridge** between steamroller and lock.

---

### ERG-P2 — Session toxins (`session`)

**Thesis:** Hour-23 (and optionally FriClose) remove **known toxic entry times** without redesigning the edge.


| ID            | Task                              | Preset(s)                    | Keys                                                                          |
| ------------- | --------------------------------- | ---------------------------- | ----------------------------------------------------------------------------- |
| **ERG-P2-01** | Block hour 23 entries             | `ERG_P2_session_NO23_01`     | `InpUseSessionBlockNo23=true` · **on BSL parent** if P1-01 passed             |
| **ERG-P2-02** | Fri close block                   | `ERG_P2_session_FriClose_01` | `InpUseSessionBlockFriClose=true`                                             |
| **ERG-P2-03** | London+NY whitelist (aggressive)  | `ERG_P2_session_LdnNy_01`    | `InpUseSessionWhitelistLdnNy=true`                                            |
| **ERG-P2-04** | Tuesday deep-dive only (analysis) | —                            | From ERG-P0-03; **no Tue block** until ≥2 independent steamrollers tagged Tue |


**Order:** Prefer **P2-01 after P1-01** (session + BSL), not session on raw unbounded grid.

**Prior art:** P2D-001 / X1 — PF helped, DD still fail G1. Treat as **partial toxin fix**, not complete edge.

---

### ERG-P3 — Regime detection (`adx` → then `regime_extra`)

**Status: ERG-P3 complete · winner ADX28 · BrkSus/ATRP/ADX25/30 reject** · Pack: `[ERG_P3_regime_pack.md](ERG_P3_regime_pack.md)`

**Thesis:** Do not open (or deepen) grids when trend strength / expansion makes pullback failure likely.


| ID            | Task                                               | Preset(s)                                                                                     | Keys                                                      |
| ------------- | -------------------------------------------------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| **ERG-P3-01** | ADX gate 30 (PRODUCTION parity on research window) | `[ERG_P3_adx_ADX30_01](../Presets/ERG_P3_adx_ADX30_01.set)`                                   | `InpUseAdxGate=true`, `InpAdxMax=30` · parent = BSL25     |
| **ERG-P3-02** | ADX plateau                                        | `[ADX28](../Presets/ERG_P3_adx_ADX28_01.set)` · `[ADX25](../Presets/ERG_P3_adx_ADX25_01.set)` | `InpAdxMax` only                                          |
| **ERG-P3-03** | Breakout suspend                                   | `[BrkSus_01](../Presets/ERG_P3_regime_BrkSus_01.set)`                                         | `InpUseBreakoutSuspend=true` (ADX off · after ADX scored) |
| **ERG-P3-04** | ATR percentile gate (last)                         | `[ATRP70_01](../Presets/ERG_P3_regime_ATRP70_01.set)`                                         | Careful — prior ATRP70 **hurt** on 2026                   |


**Do not** combine ADX + ATR% + breakout in one preset. **No MaxBars** (rejected in P1).

---

### ERG-P4 — Exit & trade management (`basket_exit` — new theses only)

**Status: ERG-P4 closed · keep ADX28+TP10 · Trail/TP/MaxBars reject** · Pack: [`ERG_P4_exit_pack.md`](ERG_P4_exit_pack.md)

**Thesis:** After containment + regime, shape **how** winners/losers exit. Low MFE correlation ⇒ optional trail **or** TP tweak — but prior Trail50/RTE **failed G1**. New attempts need a **different** activation thesis, not nostalgia.


| ID            | Task                                        | Preset(s)                                                                                         | Keys / idea                                           |
| ------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| **ERG-P4-02** | Trail with **late** activate (**load 1st**) | `[Trail70_01](../Presets/ERG_P4_bexit_Trail70_01.set)`                                            | Trail on · activate **70%** · giveback 50%            |
| **ERG-P4-03** | TP probe ±20%                               | `[TP8_01](../Presets/ERG_P4_bexit_TP8_01.set)` · `[TP12_01](../Presets/ERG_P4_bexit_TP12_01.set)` | `InpBasketTp` 8 or 12                                 |
| **ERG-P4-01** | MaxBars on ADX28 (optional / caution)       | `[MaxBars480_01](../Presets/ERG_P4_bexit_MaxBars480_01.set)`                                      | MaxBars=480 — P1 MaxBarsBSL **failed** on BSL-only    |
| **ERG-P4-04** | BSL:TP ratio note                           | —                                                                                                 | Reference **2.5:1** (25/10); document TP8/TP12 ratios |


**Anti-goal:** Do not trail if it **clips the good $2–11 wins** and leaves December steamrollers intact. **Parent = ADX28**, not raw BSL.

---

### ERG-P5 — Entry quality (`entry_filter` / optional `htf`)

**Status: ERG-P5 closed · Candle/RSI reject · keep ADX28** · Pack: [`ERG_P5_entry_pack.md`](ERG_P5_entry_pack.md)

**Thesis:** Skip low-quality first fills on the locked stack (**BSL25 + ADX28 + TP10**). One entry axis per preset. HTF parked.


| ID            | Task             | Preset(s)                                                              | Keys                                                                  |
| ------------- | ---------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **ERG-P5-01** | Candle confirm   | [`Candle_01`](../Presets/ERG_P5_entry_Candle_01.set)                   | `InpUseCandleConfirm=true`                                            |
| **ERG-P5-02** | RSI exhaustion   | [`RSI_01`](../Presets/ERG_P5_entry_RSI_01.set)                         | `InpUseRsiExhaustionFilter=true` · RSI14 · buy max 70 · sell min 30 |
| **ERG-P5-03** | HTF — **parked** | —                                                                      | Prior H1/H4 rejects; reopen only if P0 loser atlas shows HTF mismatch |

**Anti-goal:** Do not combine candle + RSI in one load. Do not re-open trail/TP/MaxBars.


---

### ERG-P6 — Integrate ≤3 survivors → canonical G1

**Status: ADX28 fail_g1 · keep PRODUCTION** · Pack: [`ERG_P6_g1_pack.md`](ERG_P6_g1_pack.md)


| ID            | Task                                              | Done when              |
| ------------- | ------------------------------------------------- | ---------------------- |
| **ERG-P6-01** | Pick ≤3 presets that passed VAL (+ optional HOLD) | ADX28 only             |
| **ERG-P6-02** | Re-run each on **canonical** window Terminal B    | MT5 report scored      |
| **ERG-P6-03** | Score G1 (PF **and** DD vs PRODUCTION)            | **fail_g1** (both)     |
| **ERG-P6-04** | Sensitivity ±10–20% on winning axis               | skipped (G1 fail)      |
| **ERG-P6-05** | Cost stress (+0.5–1 pip equiv)                    | skipped (G1 fail)      |


---

### ERG-P7 — Promote / Alternate / Reject

**Status: Reject signed · PRODUCTION lock unchanged** · Decision: [`../AI/kb/decisions/20260716_190850_ERG_P3_adx_ADX28_01_Reject.md`](../AI/kb/decisions/20260716_190850_ERG_P3_adx_ADX28_01_Reject.md) · Profile: [`../AI/kb/profiles/prof_ERG_P3_adx_ADX28_01.json`](../AI/kb/profiles/prof_ERG_P3_adx_ADX28_01.json)


| ID            | Task                                                                    | Done when                    |
| ------------- | ----------------------------------------------------------------------- | ---------------------------- |
| **ERG-P7-01** | Fill promotion checklist                                                | **done** (Reject)            |
| **ERG-P7-02** | Attach walk-forward / holdout note                                      | N/A — canon decisive         |
| **ERG-P7-03** | Human decision log                                                      | **Reject** · keep PRODUCTION |
| **ERG-P7-04** | Upsert roster profile                                                   | **done** · no amnesia        |


---

## 7. Recommended execution order (single focus)

```text
ERG-P0  characterise losers          ← done
   ↓
ERG-P1  BSL25 centre                 ← done (MaxBars reject)
   ↓
ERG-P3  ADX28 winner                 ← done (25/30/BrkSus/ATRP reject)
   ↓
ERG-P4  exits rejected               ← keep ADX28+TP10
   ↓
ERG-P5  entry rejected               ← keep ADX28+TP10
   ↓
ERG-P6  canonical G1 · ADX28           ← fail_g1 (PF 1.21 · DD 24.6%)
   ↓
ERG-P7  human decision                 ← **Reject** · keep PRODUCTION
```

**ERG closed for promote.** PRODUCTION (BSL25 + ADX30 + TP10) remains the EURUSD lock. Optional later: new Discovery thread vs PRODUCTION (not an ADX28 salvage).

### Canon result (recorded)

```text
ERG_P3_adx_ADX28_01 · 2026.01.01–2026.07.31
PF 1.21 · Net +147.86 · DD 24.62% / 27.27% · 443 trades · WR 69.3%
vs PRODUCTION lock: PF 1.36 · Net +221 · DD 18% / 21%
Decision: REJECT (ERG-P7) · profile prof_ERG_P3_adx_ADX28_01
```

See [`ERG_P6_g1_pack.md`](ERG_P6_g1_pack.md) · [`../AI/kb/decisions/20260716_190850_ERG_P3_adx_ADX28_01_Reject.md`](../AI/kb/decisions/20260716_190850_ERG_P3_adx_ADX28_01_Reject.md).

---

## 8. Idea backlog (defer until phase allows)


| Idea                              | Phase          | Caution                                    |
| --------------------------------- | -------------- | ------------------------------------------ |
| December no-trade / reduced depth | P2 / calendar  | Easy to overfit one month                  |
| Tuesday block                     | Analysis first | Likely few large losses, not weekday alpha |
| Soft BSL + trailing giveback      | P4             | Prior Trail50 fail                         |
| Depth cap 4 (`grid`)              | after P1–P3    | Changes structure — one axis               |
| ATR% gate                         | P3-04          | Prior reject                               |
| Per-trade SL                      | code-heavy     | Prefer basket SL first (already exists)    |
| TP raise to catch MFE             | P4-03          | May ↑ hold time / DD; plateau carefully    |


---

## 9. Scorecard template (per preset)

Copy into decision notes / Run KB:

```text
Preset: ERG_…
Parent: …
Axis: …
Window: …
Trades: …   WR: …   PF: …   Net: …
DD bal / eq: … / …
Avg win / avg loss: … / …   ratio: …
Max hold: …
vs P1 raw 2021-25: DD Δ …  PF Δ …
vs PRODUCTION canon (if run): G1 PF? G1 DD?
Decision: pass_is | fail_val | fail_hold | g1_pass | g1_fail | reject | alternate
Next ID: …
```

---

## 10. How this relates to PRODUCTION today

```text
P1-BASELINE (this report)
   │  many good trades, unbounded tails
   ▼
BSL $25                         ← containment (ERG-P1)
   │
ADX < 30                        ← regime (ERG-P3)  →  PRODUCTION lock
   │
Session / MaxBars / Trail / …   ← ERG-P2 / P4 quality add-ons (this cycle)
   │
Canonical G1 + human            ← only promote path
```

PRODUCTION already bought the two largest structural fixes. This guide’s job is **rediscover residual edge quality** (23:00, bag-hold duration, Dec tails, exit shape) **without** undoing BSL/ADX or overfitting 2021–2025.

---

## Related paths


| Path                                                                               | Role                          |
| ---------------------------------------------------------------------------------- | ----------------------------- |
| `[EA_failure_assessment.md](EA_failure_assessment.md)`                             | Weaknesses · failure profile · loss assessment |
| `[backtesting_guide.md](backtesting_guide.md)`                                     | Anti-overfit law              |
| `[edge_rediscovery_system.md](edge_rediscovery_system.md)`                         | Lane A/B Discover plane       |
| `[../AI/kb/search_map.md](../AI/kb/search_map.md)`                                 | Legal one-axis keys           |
| `[../AI/kb/el0_baseline_inventory.md](../AI/kb/el0_baseline_inventory.md)`         | P1 → BSL → PRODUCTION lineage |
| `[../Presets/P1-BASELINE.set](../Presets/P1-BASELINE.set)`                         | Raw parent                    |
| `[../Presets/PRODUCTION.set](../Presets/PRODUCTION.set)`                           | Lock compare                  |
| `[../AI/templates/promotion_checklist.md](../AI/templates/promotion_checklist.md)` | Promote bar                   |
| `[../AI/kb/gate_rules.json](../AI/kb/gate_rules.json)`                             | G1 / G3 / STALE_SLICE         |


