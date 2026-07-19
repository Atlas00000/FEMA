# ASI-P5 Mode B decision — keep as own Alternate preset

**Candidate id:** `ASI_P5_TEP_MID_BSL_01`  
**profile_id:** `prof_ASI_P5_TEP_MID_BSL_01`  
**Lane / parent / role:** `A` / `ASI_P5_TEP_MID_01` / `guardrail_candidate`  
**subsystem:** `regime_extra` · **asi_track:** `tep_mid_bsl`  
**EA:** v1.28+ · `InpUseAiTepGate` + `InpUseAiMidWarn` + `InpUseAiMidEarlyBsl`  
**Generated:** 2026-07-19T20:00:00Z  
**Signer:** operator (chat)

## Promote bar (this track)

**Survival across regimes** — PF > 1 and contained DD on multi-year + recent windows.  
**Not required:** beat PRODUCTION lock PF/DD on demo.

## Evidence

- [x] Mode A warn logs verified (53 `mid_warn` on 2025–26 events)
- [x] Mode B wired: early close → `exit_reason=MID_WARN` · lifecycle `mid_early_bsl`
- [x] **2026** (deposit 400): PF **1.44** · net **+$200** · equity DD **~19%** · n **409** · Sharpe ~2.0 — survives
- [x] **2018–25** (deposit 400): PF **1.35** · net **+$162** · equity DD **~23%** · n **517** · Sharpe ~1.9 — survives vs prior TEP-only long run (~PF1.0 / DD~55%)
- [x] Own preset kept separate from Mode A and PRODUCTION
- [x] No auto-promote / no Terminal A lock swap

## Caveats

- Trade count much lower than TEP-only long history (~6.9k → ~517) — selective / early-close heavy
- Seasonal concentration (Jan/Dec-heavy) — monitor; not a free-genetic retune
- 2026 Mode B vs Mode A: PF better, DD/net not clearly better — keep both presets

## Forbidden

- [x] Do **not** fold Mode B into `ASI_P5_TEP_MID_01` or `ASI_P4_TEP_GUARD_01`
- [x] Do **not** replace `PRODUCTION.set` on Terminal A
- [x] Do **not** promote on PF alone without survival story

## Decision

- [ ] **Promote** → new lock / live default on Terminal A
- [ ] **Reject** → retire Mode B preset
- [x] **Alternate (own preset)** → keep `ASI_P5_TEP_MID_BSL_01` opt-in; PRODUCTION unchanged

**Notes:** Mode B earns a roster seat as a **survival Alternate**. Default research stack remains Mode A warn-only + TEP; Mode B is the early-close variant for optional stress / demo wire.

## Next steps (human only)

1. Keep `PRODUCTION.set` on Terminal A.
2. Keep Mode A `ASI_P5_TEP_MID_01` and Mode B `ASI_P5_TEP_MID_BSL_01` as **separate** opt-in presets.
3. Optional: Mode A 2018–25 @ deposit 400 for clean A-vs-B table.
4. Next ASI track when ready: `ASI-P6` recovery probability (or park).
