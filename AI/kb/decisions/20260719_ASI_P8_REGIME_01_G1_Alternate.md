# Decision — ASI-P8 regime live filter (G1)

**Date:** 2026-07-19  
**Candidates:** `ASI_P8_REGIME_01` · `aistack`  
**Window:** 2026.01.01–2026.07.31 · deposit 400 · every tick

## Results

| Preset | PF | Net | Eq DD | Trades | WR |
| ------ | --: | ---: | ----: | -----: | --: |
| `ASI_P8_REGIME_01` (P8 only) | **1.40** | +$246 | 17.5% | 445 | 72% |
| `aistack` (Mode B + P8, alias) | 1.27 | +$175 | 14.2% | 437 | 68% |
| PRODUCTION lock (ref) | 1.36 | +$221 | ~18% | ~424 | ~71% |

## Verdict

**Promote bar:** guardrails + profitable survival across windows — **not** G1 PF alone.

| Candidate | Decision |
| --------- | -------- |
| **`aistack`** | **AI preset** — TEP + mid + Mode B + regime. G1: PF 1.27 / DD 14.2% / +$175. Long: PF 1.55 / DD ~14%. |
| `ASI_P8_REGIME_01` | **Research only** — G1 PF 1.40 is misleading; long run PF 1.01 / DD ~66%. Regime filter alone is not a guardrail. |

## Consequences

- PRODUCTION unchanged (birth lock)
- **`aistack` promoted as AI preset** (2026-07-20) — [`20260720_ASI_P8_TEP_MID_BSL_01_AI_Preset.md`](20260720_ASI_P8_TEP_MID_BSL_01_AI_Preset.md)
- **Do not** treat P8-only G1 PF as a deploy signal

---

## Survival addendum (2018.01–2025)

| Preset | PF | Net | Eq DD | Trades |
| ------ | --: | ---: | ----: | -----: |
| **`aistack`** | **1.55** | +$134 | **14.1%** | 361 |
| `ASI_P8_REGIME_01` | **1.01** | +$91 | **66.3%** | 7021 |

Stack is **AI preset**; P8-only research only. PRODUCTION unchanged.
