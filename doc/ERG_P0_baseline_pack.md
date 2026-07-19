# ERG-P0 — Baseline documentation pack

**Phase:** ERG-P0 — Document & baseline (**no code**)  
**Status:** **Complete** · 2026-07-15  
**Operator freeze:** criteria locked for this rediscovery cycle (do not edit mid-phase)  
**run_id:** `20210101_P1-BASELINE_60e646e5`  
**Philosophy:** [`baseline_profile.md`](baseline_profile.md) · Plan: [`Edge_Rediscovery_guide.md`](Edge_Rediscovery_guide.md) · Law: [`backtesting_guide.md`](backtesting_guide.md)

---

## Task checklist

| ID | Task | Status | Evidence |
| --- | --- | --- | --- |
| **ERG-P0-01** | Archive P1 2021–25 report metrics into Run KB | **Done** | `AI/kb/runs/20210101_P1-BASELINE_60e646e5/` |
| **ERG-P0-02** | Export / sync baskets + events | **Done (partial)** | `AI/data/erg/p0_p1_baseline_2021_2025/` — see telemetry gap |
| **ERG-P0-03** | Catalogue worst losses / steamroller paths (≥10) | **Done** | Loser atlas below + `loser_atlas.json` |
| **ERG-P0-04** | Freeze success criteria | **Done** | § Frozen criteria (this file) |

**Next phase:** **ERG-P1-01** — create & load `Presets/ERG_P1_bexit_BSL25_01.set`

---

## ERG-P0-01 — Archived metrics (MT5 deal report)

Primary characterisation numbers (Strategy Tester Backtest report, EURUSD M5, every tick, $400, 100% HQ):

| Metric | Value |
| --- | ---: |
| Window | **2021.01.01 – 2025.12.31** |
| Stack | P1-BASELINE · BSL **off** · ADX **off** |
| Net / PF | **+$936.62 / 2.21** |
| Gross profit / loss | +1708.20 / **−771.58** |
| Max DD bal / eq | **36.14% / 40.55%** |
| Recovery factor | **1.10** |
| Deals / WR | **687 / 95.78%** |
| Wins / losses | 658 / **29** |
| Avg win / avg loss | +2.60 / **−26.61** |
| Largest win / loss | +11.10 / **−152.06** |
| Hold avg / max | ~9d / **~297d** |
| Corr(profit, MFE / MAE) | 0.15 / **0.76** |

Window hash: `60e646e5` · Registry: [`../AI/kb/runs/20210101_P1-BASELINE_60e646e5/metrics.json`](../AI/kb/runs/20210101_P1-BASELINE_60e646e5/metrics.json)

**Report toxins (histogram-level):** loss mass spikes at **hour 23**, **Tuesday**, **December**.

---

## ERG-P0-02 — Telemetry archive & gap

### Archived files

| File | Role |
| --- | --- |
| `AI/data/erg/p0_p1_baseline_2021_2025/P1-BASELINE_2021_2025_baskets.csv` | Agent baskets |
| `…/P1-BASELINE_2021_2025_events.csv` | Agent events |
| `…/run.meta.txt` / `run_config.json` | EA meta |
| `…/loser_atlas.json` | Machine atlas |

### Config truth

Agent `preset_id=PRODUCTION` is a **mislove**. Effective stack from `run_config.json`:

- `InpUseBasketSl=false`
- `InpUseAdxGate=false`  
→ **P1-BASELINE behaviour**

`run_id` (EA): `20210101_000000_EURUSD_20260707` · basket span: first open `2021.01.03` → last close `2025.02.02` (CSV ends before full Dec-2025 calendar close of some paths).

### Telemetry gap (high)

| Observation | Implication |
| --- | --- |
| Baskets CSV: **164** rows, **100% `BASKET_TP`**, **0 loss exits** | AI log did **not** record the 29 MT5 loss deals as basket losses |
| MAE still reaches **−394** on TP survivors | Steamroller **paths** exist; some later recover to +$10 (bag-hold thesis) |
| Deal report ≠ basket CSV totals | Net/PF for promote ranking stays on **MT5 report**; CSV used for **path forensics** |

**Follow-up (not blocking P1):** On next P1/BSL runs, confirm end-of-test / non-TP exits write to baskets CSV (or export MT5 deals). Optional task tag: `ERG-P0-02b`.

---

## ERG-P0-03 — Loser / steamroller atlas

### A. True losses (MT5 deal aggregate — authority for count/size)

| Fact | Value |
| --- | --- |
| Loss deals | **29** (~4.2% of 687) |
| Share of absolute P&amp;L mass | Gross loss −772 vs gross profit 1708 → losers ≈ **31%** of two-way mass |
| Avg / largest loss | **−26.61 / −152.06** |
| Path signature | Corr(profit, MAE) **0.76** — adverse excursion ≈ outcome |
| Calendar toxins | Hour **23** · Weekday **Tue** · Month **Dec** (report histograms) |

### B. Steamroller-path proxy (deepest MAE among TP survivors)

These **eventually took +$10 TP** after severe underwater — proof of “time as healer” and why unbounded BSL-off is path-toxic even when headline PF looks fine.

| # | basket_id | MAE | Profit | Depth | Hold (days) | Open | ADX |
| --: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 1 | 149 | **−394.72** | +10.13 | 5 | **213.0** | Tue 20:00 **2022-12** | 22.3 |
| 2 | 151 | **−359.75** | +10.10 | 5 | **294.4** | Tue 15:00 2023-10 | 19.8 |
| 3 | 27 | −240.85 | +10.00 | 5 | 74.9 | Mon 09:00 2021-04 | 28.6 |
| 4 | 91 | −197.26 | +10.49 | 5 | 23.1 | Fri 15:00 2022-05 | 21.9 |
| 5 | 133 | −171.27 | +10.08 | 5 | 8.7 | Wed 22:00 2022-10 | 23.2 |
| 6 | 69 | −162.68 | +10.17 | 5 | 24.0 | Mon 11:00 2022-03 | 19.7 |
| 7 | 108 | −161.11 | +10.04 | 5 | 26.3 | Thu 18:00 2022-07 | 19.0 |
| 8 | 130 | −156.99 | +10.01 | 5 | 14.9 | Tue 17:00 2022-10 | **40.2** |
| 9 | 58 | −153.98 | +10.02 | 5 | 19.8 | Thu 14:00 2022-01 | 22.5 |
| 10 | 116 | −149.27 | +10.08 | 5 | 10.5 | Wed 03:00 2022-09 | 22.2 |
| 11–15 | (see JSON) | −148 … | +10 | 5 | … | … | … |

Full top-15 + hold ranking: [`../AI/data/erg/p0_p1_baseline_2021_2025/loser_atlas.json`](../AI/data/erg/p0_p1_baseline_2021_2025/loser_atlas.json)

### C. Pain-path opens (MAE ≤ −25, n=58 baskets)

| Slice | Finding |
| --- | --- |
| **By weekday** | **Tue** worst sum MAE (−1331, n=11) — confirms report Tuesday bar; Mon/Thu next |
| **By hour** | Open hour **15** worst sum MAE (−806, n=8); then 20, 9, 18 — NY/afternoon start of deep paths |
| **By depth** | Deep MAE paths are almost all **max_depth = 5** (full grid) |
| **ADX** | Most pain opens at ADX **~19–29**; basket 130 at **40** → ADX gate would skip some but not all |

### D. Tuesday rule (ERG-P2-04 gate)

| Question | Answer |
| --- | --- |
| ≥2 independent deep steamrollers on Tuesday? | **Yes** — baskets **149** (Dec 2022) and **151** (Oct 2023), both depth 5, MAE &lt; −350 |
| Block Tuesday now? | **No** — analysis gate satisfied for *later* consideration; still **not** a first filter. Containment (BSL) first. |

### E. What this means for optimisation

```text
Wins  = frequent shallow TPs (frequency engine)
Paths = often full-depth + multi-week MAE before recovery OR MT5 loss exit
Fix   = cap MAE (BSL / max bars) before session cosmetics
```

---

## ERG-P0-04 — Frozen success criteria

**Frozen at:** 2026-07-15 · **Signer:** operator (ERG-P0 pack)  
**Do not change** until ERG-P7 decision or explicit criteria-revision note.

### Research screen (2021–2025 splits)

| Gate | Threshold |
| --- | --- |
| Balance DD | ≤ **25%** on IS stitch (vs P1 raw 36%) |
| Loss asymmetry | avg loss / avg win ≤ **6×** (raw ~10×) |
| PF | May fall vs raw 2.21 if DD collapses (acceptable) |
| Sample | ≥ **200** deals (or equivalent basket coverage) on research stretch used for screen |
| Discipline | **One** search-map axis per preset |

### Time splits (frozen)

```text
2021.01 – 2022.12   IS
2023.01 – 2024.06   VAL
2024.07 – 2025.12   HOLD   ← one look
2026.01 – 2026.07   CANON  ← G1 vs PRODUCTION
```

### Canonical G1 (unchanged)

| Gate | Rule |
| --- | --- |
| PF | ≥ **1.36** vs PRODUCTION |
| Max DD bal | ≤ **18%** |
| Window | `2026.01.01–2026.07.31` only for promote |
| Human | Required · no auto-promote · no stale-slice |

### Pass intent for ERG-P1

BSL25 on P1 parent: **DD↓ and avg-loss ratio↓** vs this baseline — WR drop expected and OK.

---

## One-liner verdict

P1 2021–25 **proves a high-frequency EURUSD pullback edge** and a **fat-tail survival problem**; AI logs show **bag-holds to TP**, MT5 shows **29 hard losses** — rediscovery starts at **failure containment (ERG-P1)**, not more entries.

---

## Related paths

| Path | Role |
| --- | --- |
| [`baseline_profile.md`](baseline_profile.md) | Philosophy DNA |
| [`Edge_Rediscovery_guide.md`](Edge_Rediscovery_guide.md) | Full phase board |
| [`../AI/kb/runs/20210101_P1-BASELINE_60e646e5/`](../AI/kb/runs/20210101_P1-BASELINE_60e646e5/) | Registry record |
| [`../AI/data/erg/p0_p1_baseline_2021_2025/`](../AI/data/erg/p0_p1_baseline_2021_2025/) | CSV + atlas |
| [`../Presets/P1-BASELINE.set`](../Presets/P1-BASELINE.set) | Parent preset |
