# ASI-P8 — Regime intelligence pack

**Status:** **AI PRESET** · EA **v1.29** · G1 + survival Tester logged · PRODUCTION unchanged  
**AI preset:** [`aistack`](../Presets/aistack.set) (alias of `ASI_P8_TEP_MID_BSL_01`)  
**Decision:** [`../AI/kb/decisions/20260720_ASI_P8_TEP_MID_BSL_01_AI_Preset.md`](../AI/kb/decisions/20260720_ASI_P8_TEP_MID_BSL_01_AI_Preset.md)  
**Track:** **G** Regime Intelligence  
**Charter:** [`adaptive_selection_phases.md`](adaptive_selection_phases.md)  
**Policy ADR:** [`../AI/kb/asi/regime_policy_adr.md`](../AI/kb/asi/regime_policy_adr.md)

## Live filter

Skips new baskets when open regime ∈ **caution ∪ skip**:

| Filter | Regimes |
| ------ | ------- |
| **Live skip** | `false_breakout`, `grind`, `rotation` |
| Allow | `pullback_trend`, `impulse`, `expansion`, `compression`, `liquidity_vacuum`, `exhaustion` |

Gate: `Common\Files\FEMA_AI\regime_gate_v1.txt`

## G1 Tester (2026.01–07 · $400 · every tick)

| Preset | Stack | PF | Net | Equity DD | Trades | WR |
| ------ | ----- | --: | ---: | --------: | -----: | --: |
| [`ASI_P8_REGIME_01`](../Presets/ASI_P8_REGIME_01.set) | PRODUCTION + P8 only | **1.40** | +$246 | **17.5%** | 445 | 72% |
| [`aistack`](../Presets/aistack.set) | Mode B + P8 | **1.27** | +$175 | **14.2%** | 437 | 68% |
| PRODUCTION lock (ref) | BSL25 + ADX30 | 1.36 | +$221 | ~18% | ~424 | ~71% |

**G1 read:** Stack is **profitable** (PF 1.27, +$175) with **best DD** (14.2%). P8-only has higher PF on this window only — **not** the promote bar.

## Survival Tester (2018.01–2025 · $400 · every tick)

| Preset | PF | Net | Eq DD | Bal DD | Trades | WR | Sharpe |
| ------ | --: | ---: | ----: | -----: | -----: | --: | -----: |
| **`aistack`** (TEP + mid + Mode B + P8) | **1.55** | +$134 | **14.1%** | 10.4% | 361 | ~30% | 2.84 |
| `ASI_P8_REGIME_01` (P8 only) | **1.01** | +$91 | **66.3%** | 65.1% | 7021 | ~66% | 0.08 |

**Survival read:** Stack **survives** long window (PF 1.55, contained DD). P8-only **barely breaks even** with **steamroller DD** (~66%) — regime filter alone is not a guardrail.

## Verdict — AI preset promoted (2026-07-20)

| Preset | Role |
| ------ | ---- |
| **`aistack`** | **AI preset** — official opt-in guardrail stack (TEP + mid + Mode B + regime). Profitable G1 **and** 2018–25. |
| `ASI_P8_REGIME_01` | Research only — do not deploy without full stack |
| `PRODUCTION` | Unchanged — birth-window Discovery lock |

**Load for AI ops:** `Presets/aistack.set` + gate files in `Common\Files\FEMA_AI\`.  
**Do not** rank by G1 PF alone. Beat-the-lock on one window ≠ guardrailed long-term edge.

## Offline shadow (2018–25)

skip ~**26%** · net skipped **−$258** · steam prec ~0.30

## Pipeline

```powershell
cd AI
python -m fema_ops asi-regime-build --split-profile long
python -m fema_ops asi-export-regime-gate
# copy regime_gate_v1.txt → Common\Files\FEMA_AI\
```

## Non-goals

- Do not replace PRODUCTION lock — AI preset is opt-in only
- Keep P8-only (`ASI_P8_REGIME_01`) separate from the AI preset stack
