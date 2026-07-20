# ASI-P8 — promote full stack as AI preset

**Candidate id:** `aistack`  
**profile_id:** `prof_aistack`  
**Lane / parent / role:** `A` / `ASI_P5_TEP_MID_BSL_01` / **`ai_preset`**  
**subsystem:** `regime_extra` · **asi_track:** `regime_tep_mid_bsl`  
**EA:** v1.29+ · TEP + mid warn + Mode B early close + regime gate  
**Generated:** 2026-07-20T09:00:00Z  
**Signer:** operator (chat)

## Promote bar

**Guardrails + profitable survival** across G1 and long windows.  
**Not required:** beat PRODUCTION lock PF on demo.  
**Not in scope:** replace `PRODUCTION.set` on Terminal A.

## Stack (AI preset)

| Layer | Phase | Behaviour |
| ----- | ----- | --------- |
| TEP | P4 | Skip steamroller-like opens |
| Mid-warn | P5 | Basket stress detection |
| Mode B | P5 | Early close on `MID_WARN` |
| Regime | P8 | Skip caution∪skip at open |

Gate files: `tep_gate_v1.txt` · `mid_gate_v1.txt` · `regime_gate_v1.txt` → `Common\Files\FEMA_AI\`

## Evidence

| Window | PF | Net | Eq DD | Bal DD | Trades | WR |
| ------ | --: | ---: | ----: | -----: | -----: | --: |
| **2026 G1** (2026.01–07) | **1.27** | +$175 | **14.2%** | — | 437 | 68% |
| **2018–25** | **1.55** | +$134 | **14.1%** | 10.4% | 361 | ~30% |

Compare P8-only (`ASI_P8_REGIME_01`): G1 PF **1.40** / DD 17.5%; long run PF **1.01** / DD **66.3%** / n7021 — regime filter alone is not a guardrail.

## Decision

- [ ] **Promote** → replace PRODUCTION lock
- [ ] **Reject** → retire preset
- [x] **AI preset** → designated opt-in guardrail stack · **PRODUCTION unchanged**

**Notes:** This is the **official AI preset** for Terminal A opt-in / demo wire (external alias `aistack` for the full stack). Discovery lock stays `FEMA_EURUSD_M5_PRODUCTION`. Do not merge P8-only (`ASI_P8_REGIME_01`) into this stack's role — P8-only remains research.

## Consequences

1. `Presets/manifest.json` → `ai_preset: aistack`
2. Load on chart when running guardrailed AI stack (not the birth lock)
3. P4/P5/P6 layer presets remain separate research artifacts — do not fold into PRODUCTION
4. Next optional tracks: `ASI-P7` compatibility · `ASI-P9` edge health

## Forbidden

- [x] Do **not** replace `PRODUCTION.set` on Terminal A
- [x] Do **not** treat P8-only G1 PF as deploy signal
- [x] Do **not** auto-promote to Discovery lock without new human decision
