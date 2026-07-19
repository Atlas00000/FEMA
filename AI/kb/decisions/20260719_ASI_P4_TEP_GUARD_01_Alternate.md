# ASI-P4 decision — keep as guardrail candidate

**Candidate id:** `ASI_P4_TEP_GUARD_01`  
**profile_id:** `prof_ASI_P4_TEP_GUARD_01`  
**Lane / parent / role:** `A` / `PRODUCTION` / `guardrail_candidate`  
**subsystem:** `regime_extra` · **asi_track:** `tep`  
**Window (tester):** `2018.01.01–2025.12.31` EURUSD M5  
**Generated:** 2026-07-19T17:00:00Z  
**Signer:** operator (chat)

## Evidence

- [x] Offline guardrail holdout (2025): kill=`ok` · thr **0.650** · precision **60%** · net skipped **−$55**
- [x] Gate wired: `InpUseAiTepGate` · `tep_gate_v1.txt` · `roll_pf` cap fix (no P≈1 lock)
- [x] Long-window Tester: ~**6.9k** trades · PF **~1.00** · DD **~55%** · baskets **~1700** (selective skip, not broken)
- [x] Recent windows (post-fix): **2026.01–07 PF 1.38** / DD~11%; **2025–2026.07 PF 1.20** / DD~18% — competitive, still not lock
- [x] Promote bar = **guardrail holdout**, not beat PRODUCTION PF on long history / 2026 demo
- [x] One-axis only (`InpUseAiTepGate`) — no lot/TP/SL/grid thaw
- [x] No auto-promote

## Forbidden

- [x] Not promoting because long-window PF looked good (it did not rewrite edge)
- [x] No Terminal A PRODUCTION replacement
- [x] No silent live wire without separate human promote

## Decision

- [ ] **Promote** → new lock / live default on Terminal A
- [ ] **Reject** → retire gate / stop Track A
- [x] **Alternate (keep as guardrail candidate)** → roster profile; opt-in preset only; PRODUCTION unchanged

**Notes:** TEP is a working selective skip (~threshold 0.65). 2018–2025 remains structurally break-even — expected under `guardrails_not_gates`. 2026 windows look competitive but still do not justify lock. Keep for shadow / optional demo wire later.

## Next steps (human only)

1. Keep `PRODUCTION.set` on Terminal A.
2. Leave `ASI_P4_TEP_GUARD_01.set` as opt-in on Terminal B / research.
3. Proceed **ASI-P5** mid-basket warn (offline first) — [`doc/ASI_P5_midbasket_pack.md`](../../../doc/ASI_P5_midbasket_pack.md).
4. Retrain/export gate when new basket collects land — re-copy `tep_gate_v1.txt`.
