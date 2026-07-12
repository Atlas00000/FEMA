# EL0 — Baseline & inventory (EURUSD)

**ID:** `EL0-BASE` · **Status:** Done  
**Machine:** [`el0_baseline_inventory.json`](el0_baseline_inventory.json)

> **Exit line:** We started from **P1-BASELINE** (steamroller); Discovery moved us through **P2A-002_BSL_25** to **PRODUCTION** (BSL_25 + ADX30).

## Tester contract (EL0-002)

| Field | Value |
| ----- | ----- |
| Symbol / TF | EURUSD M5 |
| Deposit | $400 |
| Leverage | 1:500 |
| Model | Every tick |
| ProfitInPips | 0 |
| Canonical window | `2026.01.01` – `2026.07.31` |

## Started from X (EL0-001 / EL0-003)

| | **P1-BASELINE** |
| - | --------------- |
| Preset | [`Presets/P1-BASELINE.set`](../../Presets/P1-BASELINE.set) |
| Stack | Grid + basket TP $10 · **no BSL** · **no ADX** |
| 2026 MT5 | PF **0.17** · −$245 · DD **66%** · WR 83% · 30 trades |
| Source | Edge Discovery **row 1** |
| Verdict | Rejected characterisation — not deployable |
| `run_id` | `20260101_P1-BASELINE_4a41623a` (EL1 documented) |

Diff vs PRODUCTION: `InpUseBasketSl=false` · `InpUseAdxGate=false`.

## Intermediate control

| | **P2A-002_BSL_25** |
| - | ------------------ |
| Preset | [`Presets/P2A-002_BSL_25.set`](../../Presets/P2A-002_BSL_25.set) |
| Stack | BSL $25 + TP $10 · ADX **off** |
| 2026 MT5 | PF **1.27** · +$176 · DD ~17%/21% · WR 70% · 424 trades |
| Role | Control vs PRODUCTION (same window) |
| `run_id` | `20260101_P2A-002_BSL_25_5ea7b09b` (EL1 documented; table PF 1.15) |

Diff vs PRODUCTION: `InpUseAdxGate=false` only.

## Moved to Y (lock)

| | **PRODUCTION** (`P2C-001_REG_ADX30`) |
| - | ------------------------------------- |
| Preset | [`Presets/PRODUCTION.set`](../../Presets/PRODUCTION.set) |
| Load | `FEMA_EURUSD_M5_PRODUCTION.ini` |
| Stack | BSL $25 + **ADX max 30** + TP $10 |
| 2026 MT5 | PF **1.36** · +$221 · DD 18%/21% · WR 71% · 424 trades · Sharpe 1.90 |
| Certificate | [`../certificate_PRODUCTION_EURUSD.json`](../certificate_PRODUCTION_EURUSD.json) |
| `run_id` (AI0 baskets) | `20260101_PRODUCTION_13c52cd9` |

## Links (EL0-004)

- Discovery lab: [`../../Edge Discovery.md`](../../Edge%20Discovery.md)
- System profile: [`../../System Profile EURUSD.md`](../../System%20Profile%20EURUSD.md)
- Freeze snapshot: [`../baseline.json`](../baseline.json)
- KB candidates: [`candidates.csv`](candidates.csv)
- Preset manifest: [`../../Presets/manifest.json`](../../Presets/manifest.json)
