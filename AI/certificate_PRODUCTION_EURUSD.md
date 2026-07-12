# Edge certificate — FEMA EURUSD M5 PRODUCTION

**Machine source of truth:** [`certificate_PRODUCTION_EURUSD.json`](certificate_PRODUCTION_EURUSD.json)  
**Vision / narrative:** [`../edgecontainment.md`](../edgecontainment.md) §1–3  
**Lock profile:** [`../System Profile EURUSD.md`](../System%20Profile%20EURUSD.md)  
**EL3 confirm:** [`kb/el3_lock_confirm.md`](kb/el3_lock_confirm.md) · `python -m fema_ops cert-confirm`  
**Health:** `python -m fema_ops health` (from `AI/`) · formula `health_v0`

Scripts must load bands from the JSON (`AI/cert_loader.py`) — do not hardcode thresholds.

**Lock run_id:** `20260101_PRODUCTION_13c52cd9` · birth unit = MT5 deals (basket CSV PF ~1.40 is related, not identical).

## Birth metrics (lock window 2026.01.01–2026.07.31)

| Metric | Value |
| ------ | ----- |
| Profit factor | **1.36** |
| Net | **+$221** |
| Max DD | **18% / 21%** eq |
| Win rate | **71%** |
| Trades | **424** |
| Sharpe | **1.90** |
| Avg `bars_alive` (M5) | **320.5** |
| Avg `max_depth` | **3.94** |
| Baskets / day | **0.596** |

Fingerprint: `adx_gate=on` · `bsl=25` · `basket_tp=10` · preset `FEMA_EURUSD_M5_PRODUCTION`

## Rolling windows

**50 / 100 / 250** baskets (primary **100**). Persist: **3** deteriorating windows to escalate · **2** recoveries to clear.

## Bands (summary)

| | Green | Amber | Red |
| - | ----- | ----- | --- |
| PF | ≥ 1.25 (target 1.30–1.45) | 1.10–1.25 | &lt; 1.10 |
| WR / TP hit | ≥ 68% | 63–68% | &lt; 63% |
| Depth | ≤ **1.15× birth** (~4.5) | 1.15–1.4× | &gt; 1.4× |
| Duration | **0.7–1.3× birth** M5 bars | 0.5–1.6× | outside |
| MAE vs BSL | ≤ 60% | — | &gt; 80% persistent |
| Trade freq | 70–130% of birth bpd | — | — |

Containment “2–6 bars / ≤L2.5” was conceptual — EA logs M5 `bars_alive` and lock depth ~L4; health uses **birth-relative** duration/depth.

## Action ladder (by health 0–100)

| Health | Label | Action |
| ------ | ----- | ------ |
| ≥ 85 | normal | Run |
| 70–84 | investigate | Human review · no EA change |
| 50–69 | watch | ≤3 offline candidates · keep PRODUCTION |
| 30–49 | re_discovery | Edge Discovery · human promote |
| &lt; 30 | retire | Stop new capital · archive |

**Never auto-promote.** Pause = new baskets only (see JSON `pause_policy`).
