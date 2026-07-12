# Edge Genome v0 — PRODUCTION (RG-GEN-01)

**Preset:** `PRODUCTION` (`P2C-001_REG_ADX30`) · lock `20260101_PRODUCTION_13c52cd9`  
**Machine:** [`genome_PRODUCTION.json`](genome_PRODUCTION.json)

## Thrive (where the edge works)

| Region | Signal | Evidence |
| ------ | ------ | -------- |
| Mild trend / ADX&lt;30 | High `adx_lt_30_share`, median ADX below gate | Lock birth; ADX30 gate |
| Shallow pullbacks | Avg depth ~3–4.5 (birth 3.94) | ATR×1.0 grid |
| Multi-session (incl. Asia) | Asia share not ~0 | P2D-004 London/NY-only failed |
| Contained MAE | Mean \|MAE\| well under BSL $25 | Certificate MAE band |
| Tight spreads | p90 spread ≤ ~30 pts | EA spread filter |

## Fail (where it dies)

| Region | Signal | Evidence |
| ------ | ------ | -------- |
| Strong ADX / steamroller | Low ADX&lt;30 share | P1-BASELINE |
| Deep / wide grid | Avg depth ≫ birth or ATR×1.5+ | P2F grid spacing |
| Session over-filter | London+NY only | P2D-004 |
| MAE near BSL | Mean \|MAE\| → 22+ | Tail risk |
| Other symbols | Same preset GBPUSD | G3 fail PF 0.80 |

## Use

Fingerprint × genome → **compatibility shadow** (`fema_ops fingerprint` / health report).  
Mismatches suggest ≤3 `search_map` subsystems for Wave 4 factory — human still clones.
