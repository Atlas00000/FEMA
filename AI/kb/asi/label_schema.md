# ASI label schema (`ASI-P1-01`)

**Phase:** `ASI-P1` · offline only · no MT5 behaviour change  
**Charter:** [`../../doc/adaptive_selection_phases.md`](../../doc/adaptive_selection_phases.md)  
**Forensics:** [`../../doc/EA_failure_assessment.md`](../../doc/EA_failure_assessment.md)

## Purpose

Label **closed baskets** for Trend Expansion Predictor (TEP) training. Labels use **outcome** fields (`hit_bsl`, `profit`, `max_depth`, `mae`) — never fed as features at basket-open.

## Primary target: `y_steamroller`

| Value | Meaning |
| ----- | ------- |
| **1** | Steamroller / expansion-fail episode — TEP should learn to skip these at open |
| **0** | Not a steamroller signature — keep trading |

## Class taxonomy (`label_class`)

| Class | Rule | `y_steamroller` |
| ----- | ---- | --------------- |
| `steamroller_bsl` | `hit_bsl=1` or `exit_reason=BASKET_SL` | 1 |
| `expansion_stress` | `max_depth ≥ 4` and `profit < 0` (deep grid, no TP) | 1 |
| `winner` | `hit_tp=1` or `profit > 0` | 0 |
| `other_loss` | Small loss, shallow depth — not primary TEP target | 0 |

**PRODUCTION note:** With BSL $25, most steamrollers appear as `steamroller_bsl`. `expansion_stress` catches deep-grid losers before full BSL on research stacks.

## Legacy compat: `y_fail`

EC0 / AI2 field: `1` if `hit_bsl=1` **or** `mae ≤ −$20`.

## Features at basket-open (no leakage)

Snapshot from basket row at **open** + derived from **prior basket open** only:

| Field | Source |
| ----- | ------ |
| Static open | `ema_slope`, `adx`, `atr`, `dist_ema_trend_atr`, … (see `fema_baskets_v2`) |
| `ema_slope_accel` | Δ slope vs previous basket open |
| `adx_accel` | Δ ADX vs previous basket open |
| `atr_expansion_rate` | (ATR − prev_ATR) / prev_ATR |
| `consecutive_same_dir` | Run length of same `direction` |
| `dist_ema_abs` | \|dist_ema_trend_atr\| |
| `impulse_score` | Weighted composite (v0 heuristic for P1 shadow) |

**Forbidden as features:** `profit`, `mae`, `mfe`, `max_depth`, `hit_bsl`, `exit_reason`, `close_time`.

## Time splits (`splits.json`)

| Split | Window | Use |
| ----- | ------ | --- |
| `train` | 2020.01.01 – 2023.12.31 | Model fit |
| `calibrate` | 2024.01.01 – 2025.12.31 | Threshold tune |
| `promote_frozen` | 2026.01.01 – 2026.07.31 | G1 one-shot — **never tune here** |

## Build

```powershell
cd AI
python -m fema_ops asi-build
# or explicit paths:
python -m fema_ops asi-build --baskets data/EURUSD_baskets_2020_2025_uid.csv --promote-baskets data/live/latest_baskets.csv
```

**Outputs:** `AI/kb/asi/dataset_*.csv` · `splits.json` · `asi_baseline_metrics.json` · `asi_shadow_v0.json`

**Train (P2):** `cd AI && python -m fema_ops asi-train --strict --max-skip 0.08 --guardrail`

**Guardrail review (P3):** `python -m fema_ops asi-review --guardrail`

**Export gate (P4):** `python -m fema_ops asi-export-gate` → copy `tep_gate_v1.txt` to `Common\Files\FEMA_AI\`

**Long train profile:** `asi-build --split-profile long --no-promote`

## Mid-basket target: `y_mid_steamroller` (`ASI-P5-01`)

| Value | Meaning |
| ----- | ------- |
| **1** | Basket eventually steamrollers (`y_steamroller=1`) — warn at this depth milestone |
| **0** | Basket does not steamroller — avoid false mid-warn |

**Expansion:** one row per `(basket, warn_depth)` for `warn_depth ∈ [2 … min(max_depth, 5)]`. Label copies eventual steamroller outcome; features are open snapshot + `warn_depth` + `is_sell` only (no `mae`/`mfe`/`profit`).

**Build / train / review:**

```powershell
python -m fema_ops asi-mid-build --split-profile long
python -m fema_ops asi-mid-train --max-skip 0.15
python -m fema_ops asi-mid-review
```

Policy default: **warn only** — [`mid_policy_adr.md`](mid_policy_adr.md) · pack [`../../doc/ASI_P5_midbasket_pack.md`](../../doc/ASI_P5_midbasket_pack.md).

## Recovery target: `y_recover` (`ASI-P6-01`)

| Value | Meaning |
| ----- | ------- |
| **1** | Basket eventually recovers — `hit_tp=1` or `profit > 0` |
| **0** | Basket fails to recover (BSL / loss) |

**Expansion:** same depth milestones as mid-warn (`warn_depth ∈ [2 … min(max_depth, 5)]`). Features identical anti-leakage set (open + `warn_depth` + `is_sell`). Low `P(recover)` → recommend early exit (shadow); high → KEEP.

**Build / train / review:**

```powershell
python -m fema_ops asi-rec-build --split-profile long
python -m fema_ops asi-rec-train --max-exit-rate 0.15
python -m fema_ops asi-rec-review
```

Policy default: **shadow recommend only** — [`rec_policy_adr.md`](rec_policy_adr.md) · pack [`../../doc/ASI_P6_recovery_pack.md`](../../doc/ASI_P6_recovery_pack.md).

## Regime labels (`ASI-P8-01`)

Open-time rule taxonomy (no outcome leakage): `liquidity_vacuum` · `impulse` · `expansion` · `exhaustion` · `false_breakout` · `compression` · `grind` · `pullback_trend` · `rotation`.

```powershell
python -m fema_ops asi-regime-build --split-profile long
python -m fema_ops asi-regime-review
```

Policy: allow / caution / skip — [`regime_policy_adr.md`](regime_policy_adr.md) · pack [`../../doc/ASI_P8_regime_pack.md`](../../doc/ASI_P8_regime_pack.md).

## Shadow v0 (`ASI-P1-05`)

Provisional skip rule until P2 model: skip if `impulse_score ≥ train p90`. Report counts skipped steamrollers vs false-skip winners.
