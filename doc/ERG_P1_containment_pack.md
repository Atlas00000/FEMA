# ERG-P1 — Failure containment (BSL) · test pack

**Phase:** ERG-P1 · **axis:** `basket_exit`  
**Status:** ERG-P1 **closed** · centre = **BSL25** · MaxBars **rejected** · next = ERG-P3 ADX  
**Parent:** [`P1-BASELINE.set`](../Presets/P1-BASELINE.set)  
**Baseline:** [`ERG_P0_baseline_pack.md`](ERG_P0_baseline_pack.md) · `run_id` `20210101_P1-BASELINE_60e646e5`  
**Plan:** [`Edge_Rediscovery_guide.md`](Edge_Rediscovery_guide.md)

> Cap steamroller MAE. Session/ADX come later. **One preset at a time.**

---

## Presets (load order)

| Order | File | Task | Diff vs parent |
| --- | --- | --- | --- |
| **1st** | [`ERG_P1_bexit_BSL25_01.set`](../Presets/ERG_P1_bexit_BSL25_01.set) | **ERG-P1-01** | `InpUseBasketSl=true` (SL=25) |
| 2nd | [`ERG_P1_bexit_BSL20_01.set`](../Presets/ERG_P1_bexit_BSL20_01.set) | ERG-P1-02 | BSL on · SL=**20** |
| 2nd | [`ERG_P1_bexit_BSL30_01.set`](../Presets/ERG_P1_bexit_BSL30_01.set) | ERG-P1-02 | BSL on · SL=**30** |
| 3rd | [`ERG_P1_bexit_MaxBars480_01.set`](../Presets/ERG_P1_bexit_MaxBars480_01.set) | ERG-P1-03 | MaxBars=**480** only (BSL still off) |
| 3b | [`ERG_P1_bexit_MaxBarsBSL_01.set`](../Presets/ERG_P1_bexit_MaxBarsBSL_01.set) | ERG-P1-03b | BSL25 + MaxBars=480 |

**Alias note:** `ERG_P1_bexit_BSL25_01` ≡ historical `P2A-002_BSL_25` stack (same keys). Use the ERG name for this cycle’s scorecard.

---

## How to run (Terminal B)

**Load path (Tester Profiles):**  
`C:\Users\emili\AppData\Roaming\MetaQuotes\Terminal\158041E5204719DC59E8E86EAAE9D56B\MQL5\Profiles\Tester\`

Presets are copied there for Strategy Tester → Inputs → Load. Repo copies also live under `Presets/` (source of truth).

1. Strategy Tester → Expert **FEMA** → Inputs → **Load** preset above (from Tester Profiles).  
2. Symbol **EURUSD** · Period **M5** · Model **Every tick** · Deposit **$400** · ProfitInPips **0**.  
3. Dates: start with **IS** `2021.01.01`–`2022.12.31`; if pass screen, extend / VAL.  
4. Journal: confirm `bsl=25` (or 20/30) when BSL presets run.  
5. Sync Agent CSVs → register; fill scorecard below.  
6. Do **not** retune and re-peek HOLD (`2024.07`–`2025.12`) this phase.

---

## Pass screen (frozen from P0)

| Gate | Threshold vs P1 raw 2021–25 |
| --- | --- |
| Max DD bal | ≤ **25%** (raw **36.14%**) |
| avg loss / avg win | ≤ **6×** (raw ~**10×**) |
| PF | May fall vs 2.21 — OK if DD collapses |
| Sample | Meaningful trade count on IS |

**ERG-P1-04:** Prefer BSL25 if 20/30 are similar (plateau). Knife-edge → note Alternate, don’t overfit.

---

## Scorecard (paste after each run)

```text
Preset: ERG_P1_bexit_…
Window: …
Trades: …   WR: …   PF: …   Net: …
DD bal / eq: … / …
Avg win / avg loss: … / …   ratio: …
Max hold: …
vs P1 raw: DD Δ …   PF Δ …   ratio Δ …
Decision: pass_is | fail_is | plateau_ok | skip
Next: …
```

| Preset | Window | PF | DD% | AvgW/AvgL | Decision |
| --- | --- | --- | --- | --- | --- |
| BSL25_01 | ~2021–2025 (operator report) | **1.02** | **35.3 / 38.3** | 2.72 / −5.13 (**1.89×**) | **fail_is** (DD) · **plateau centre / P1 control** |
| BSL20_01 | ~2021–2025 (operator report) | **0.95** | **74.7 / 78.0** | 2.76 / −4.20 (**1.52×**) | **fail_is** · reject tighter |
| BSL30_01 | ~2021–2025 (operator report) | **1.00** | **53.7 / 55.9** | 2.68 / −5.96 (**2.22×**) | **fail_is** · reject looser |
| MaxBars480_01 | ~2021–2025 (operator report) | **1.14** | **88.9 / 91.1** | 2.51 / −5.41 (**2.16×**) | **fail_is** · **reject as BSL substitute** |
| MaxBarsBSL_01 | ~2021–2025 (operator report) | **0.99** | **76.1 / 77.0** | 2.57 / −4.41 (**1.72×**) | **fail_is** · **worse than BSL25 alone** |

### Result — `ERG_P1_bexit_MaxBarsBSL_01` (2026-07-15)

```text
Preset: ERG_P1_bexit_MaxBarsBSL_01  (BSL25 + MaxBars=480)
Window: multi-year from 2021 (MT5 report)
Trades: 2413   WR: 62.99%   PF: 0.99   Net: -39.88
DD bal / eq: 76.13% / 76.99%
Avg win / avg loss: +2.57 / -4.41   ratio: 1.72×
Largest L: -13.73   (BSL still capping $)
vs BSL25 alone: PF 1.02→0.99 · Net +67→-40 · DD 35%→76% · trades 1994→2413
Decision: fail_is · MaxBars add-on harms path on this window
Next: ERG-P1 CLOSED · ERG-P3 ADX30 on BSL25 (no MaxBars)
```

**Screen vs frozen P0:**

| Gate | Need | Got | |
| --- | --- | --- | --- |
| DD bal ≤ 25% | ≤25% | **76.1%** | **FAIL** |
| avgL/avgW ≤ 6× | ≤6× | **1.72×** | **PASS** |
| Beat BSL25 parent | DD↓ or PF↑ | DD **worsened**, PF **down** | **FAIL** |

**Read:** Combining time-stop with BSL **increases trade count** (forced exits → re-entries) and **destroys DD** vs BSL25 alone. Largest loss still BSL-capped (−13.73), so the damage is **path / churn**, not uncapped tails. **Do not carry MaxBars into ERG-P3.**

### ERG-P1 final (containment)

| Keep | Reject |
| --- | --- |
| **`ERG_P1_bexit_BSL25_01`** as parent stack | BSL20, BSL30, MaxBars480, MaxBarsBSL |

### Result — `ERG_P1_bexit_MaxBars480_01` (2026-07-15)

```text
Preset: ERG_P1_bexit_MaxBars480_01  (MaxBars=480, BSL OFF)
Window: multi-year from 2021 (MT5 report)
Trades: 1911   WR: 71.17%   PF: 1.14   Net: +426.27
DD bal / eq: 88.92% / 91.09%
Avg win / avg loss: +2.51 / -5.41   ratio: 2.16×
Largest L: -35.77   (vs BSL25 -13.83 · P1 raw -152)
Recovery factor: 1.04
vs BSL25: PF higher (1.14 vs 1.02) but DD disaster (35%→89%)
Decision: fail_is · time-stop ≠ dollar containment
Next: Do NOT prefer MaxBars over BSL25 · ERG-P3 ADX on BSL25
```

**Screen vs frozen P0:**

| Gate | Need | Got | |
| --- | --- | --- | --- |
| DD bal ≤ 25% | ≤25% | **88.9%** | **FAIL** (worst of P1 set) |
| avgL/avgW ≤ 6× | ≤6× | **2.16×** | **PASS** |
| DD must improve vs raw | ≤36% path | **worse than raw** | **FAIL** |

**Read:** MaxBars-only softens the −152 tail (−35.77) and lifts headline PF/Net vs BSL25, but **within 480 bars the grid can still dig deep** — account path nearly wiped (DD ~90%). Confirms park decision: **money stop (BSL25) first**; MaxBars is optional add-on later (`MaxBarsBSL_01`), never a replacement.

### Plateau close — BSL20 / 25 / 30 (2026-07-15)

| | BSL20 | **BSL25** | BSL30 |
| --- | ---: | ---: | ---: |
| PF | 0.95 | **1.02** | 1.00 |
| Net | −188 | **+67** | +7 |
| DD bal / eq | 74.7 / 78 | **35.3 / 38.3** | 53.7 / 55.9 |
| WR | 59% | **66%** | 69% |
| AvgW / AvgL | 2.76 / −4.20 | 2.72 / −5.13 | 2.68 / −5.96 |
| L/W ratio | 1.52× | **1.89×** | 2.22× |
| Largest L | −12.82 | −13.83 | −14.82 |

**ERG-P1-04 verdict:** **BSL25 wins the plateau.** Tighter (20) destroys path; looser (30) re-opens DD without PF gain. All three fail DD ≤25% — expected for BSL-only on multi-year. Containment centre locked: **`ERG_P1_bexit_BSL25_01`**.

### Result — `ERG_P1_bexit_BSL30_01` (2026-07-15)

```text
Preset: ERG_P1_bexit_BSL30_01
Window: multi-year from 2021 (MT5 report)
Trades: 1920   WR: 69.06%   PF: 1.00   Net: +6.73
DD bal / eq: 53.68% / 55.85%
Avg win / avg loss: +2.68 / -5.96   ratio: 2.22×
Largest L: -14.82
vs BSL25: DD worse (35%→54%) · PF flat/worse · Net +67→+7
Decision: fail_is · not preferred over BSL25
Next: Close ERG-P1 containment · open ERG-P3 ADX on BSL25 parent
```

**Screen vs frozen P0:**

| Gate | Need | Got | |
| --- | --- | --- | --- |
| DD bal ≤ 25% | ≤25% | **53.7%** | **FAIL** |
| avgL/avgW ≤ 6× | ≤6× | **2.22×** | **PASS** |
| Prefer plateau centre | best DD+PF among 20/25/30 | **BSL25** | **selected** |

**Read:** Looser BSL buys slightly higher WR and lets avg loss drift up — path DD gets **worse**, not better. No reason to prefer 30. MaxBars-only (scored) **confirmed reject as BSL substitute** (PF 1.14, DD ~90%). **ADX on BSL25** remains the next one-axis move (ERG-P3-01).

### Result — `ERG_P1_bexit_BSL25_01` (2026-07-15)

```text
Preset: ERG_P1_bexit_BSL25_01
Window: multi-year from 2021 (MT5 report)
Trades: 1994   WR: 65.80%   PF: 1.02   Net: +66.84
DD bal / eq: 35.33% / 38.32%   (relative bal DD 42.44%)
Avg win / avg loss: +2.72 / -5.13   ratio: 1.89×
Largest L: -13.83
vs P1 raw: DD ~36%→35% (flat) · PF 2.21→1.02 · ratio 10×→1.89×
vs BSL20:   DD 75%→35% · PF 0.95→1.02 · Net -188→+67 · WR 59%→66%
Decision: fail_is (DD gate) · keep as P1 control / plateau centre
Next: optional BSL30 for plateau; then ERG-P3 ADX on BSL25 — do not chase MaxBars yet
```

### Result — `ERG_P1_bexit_BSL20_01` (2026-07-15)

```text
Preset: ERG_P1_bexit_BSL20_01  (label)
Window: multi-year from 2021 (MT5 report; confirm exact end date)
Trades: 2164   WR: 59.10%   PF: 0.95   Net: -187.99
DD bal / eq: 74.73% / 78.00%
Avg win / avg loss: +2.76 / -4.20   ratio: 1.52×
Largest L: -12.82   (tail CAP works vs P1 -152)
vs P1 raw: DD 36%→75% (worse path) · PF 2.21→0.95 · ratio 10×→1.52× (better R)
Decision: fail_is
```

**Screen — BSL20:** DD FAIL · R PASS · DD worsened vs raw.

**Config note:** Agent CSVs often 0 bytes post-run; trust MT5 report for these scores. Fingerprint may lag the labeled preset — confirm Inputs `InpBasketSl` when in doubt.

---

## Expected qualitative result (BSL25)

WR falls (more realized −$20–30 basket exits); **DD and avg loss collapse**; PF often lands near historical BSL control (~1.1–1.3 on 2026). That is **health**, not regression.

---

## After P1 (BSL plateau closed · MaxBars rejected)

Containment centre: **`ERG_P1_bexit_BSL25_01`**. MaxBars480 and MaxBarsBSL **both fail_is** — do not stack MaxBars into the next phase.

→ **ERG-P3-01** — create/load `ERG_P3_adx_ADX30_01` on **BSL25 parent** (`InpUseAdxGate=true`, `InpAdxMax=30`).  
→ Session (ERG-P2) only after ADX is scored.
