# ASI-P4 — TEP guardrail gate pack

**Status:** **Alternate** (2026-07-19) · keep as guardrail candidate · PRODUCTION unchanged  
**Candidate preset:** `ASI_P4_TEP_GUARD_01`  
**Parent:** `PRODUCTION` · **subsystem:** `regime_extra` · **thesis:** `asi_tep`  
**Decision:** [`../AI/kb/decisions/20260719_ASI_P4_TEP_GUARD_01_Alternate.md`](../AI/kb/decisions/20260719_ASI_P4_TEP_GUARD_01_Alternate.md)

## What it does

When `InpUseAiTepGate=true`, FEMA **skips opening a new basket** (level 0 only) if offline TEP scores `P(steamroller | basket-open) >= threshold`. Grid add-ons are untouched. Mid-basket behaviour is unchanged.

This is a **guardrail**, not a production-parity bet. Promotion does **not** require beating live PRODUCTION PF on 2026 demo.

## Guardrail promote bar

Pass **all** of:

| Gate | Source |
| ---- | ------ |
| Holdout kill = `ok` | `python -m fema_ops asi-review --guardrail` |
| Skip budget ≤ 8% on holdout | threshold tune (`--max-skip 0.08`) |
| Steamroller precision ≥ 30% | kill criteria |
| net_skipped ≤ 0 | avoid cutting winners |
| Human sign-off | `asi_guardrail_review_pack.md` |

**Not required:** PF/WR beat PRODUCTION on 2026 canon.

## Offline pipeline (long_train)

```powershell
cd AI
python -m fema_ops asi-build --split-profile long --no-promote
python -m fema_ops asi-train --strict --max-skip 0.08 --guardrail
python -m fema_ops asi-review --guardrail
python -m fema_ops asi-export-gate
```

Artifacts:

- `AI/kb/asi/tep_gate_v1.txt` — MT5 runtime weights
- `AI/kb/asi/tep_gate.json` — Python metadata
- `AI/kb/asi/asi_guardrail_review_pack.md` — sign-off pack

## MT5 deploy steps

1. **Compile** FEMA EA (includes `Include/AI/AiTepGate.mqh`).
2. Copy `AI/kb/asi/tep_gate_v1.txt` →  
   `%APPDATA%\MetaQuotes\Terminal\Common\Files\FEMA_AI\tep_gate_v1.txt`
3. Load preset `Presets/ASI_P4_TEP_GUARD_01.set` on **Terminal B** tester.
4. Run backtest; register run via existing `postrun.ps1` (ASI shadow columns still apply).
5. Compare **guardrail metrics** on new run vs review pack — not PRODUCTION lock G1.

## EA inputs (one axis)

| Input | Default | Candidate |
| ----- | ------- | --------- |
| `InpUseAiTepGate` | `false` | `true` |
| `InpAiTepGateFile` | `FEMA_AI\tep_gate_v1.txt` | unchanged |

Skip reason in AI events: `tep_gate;p=0.xxxx`

## Extend train to 2018+

Current research CSV spans **2020–2025**. To lengthen train before P4 tester sign-off:

1. Strategy Tester: PRODUCTION + `InpUseAiEventLog=true`
2. Window: `2018.01.01` → `2025.12.31` (larger deposit if needed so run completes)
3. Copy Agent `*_baskets.csv` → `AI/data/EURUSD_baskets_2018_2025.csv`
4. Rebuild:

```powershell
python -m fema_ops asi-build --baskets data/EURUSD_baskets_2018_2025.csv --split-profile long --no-promote
python -m fema_ops asi-train --strict --max-skip 0.08 --guardrail
python -m fema_ops asi-review --guardrail
python -m fema_ops asi-export-gate
```

5. Re-copy `tep_gate_v1.txt` to Common Files and re-test.

Holdout stays **2025**; train grows to 2018–2024.

## Human promote (still required)

No auto-promote. After Terminal B run looks acceptable on guardrail story:

- File decision under `AI/kb/decisions/`
- Upsert profile `prof_ASI_P4_TEP_GUARD_01.json`
- Do **not** replace PRODUCTION lock unless separate AER-P6 promote

## Window review (post `roll_pf` fix)

| Window | PF | Net | DD | Trades | Note |
| ------ | --: | --- | --: | -----: | ---- |
| 2018–2025 | ~1.00 | ~−$30 | ~55% | ~6.9k | Structural BE; gate healthy |
| 2026.01–07 | **1.38** | +$243 | ~11% | 454 | Competitive vs birth lock |
| 2025.01–2026.07 | **1.20** | +$407 | ~18% | 1,306 | Extended recent |

Still **Alternate** — do not lock. Next track: [`ASI_P5_midbasket_pack.md`](ASI_P5_midbasket_pack.md).
