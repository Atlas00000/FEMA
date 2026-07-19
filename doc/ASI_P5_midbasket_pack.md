# ASI-P5 — Mid-basket steamroller early warning pack

**Status:** **COMPLETE (MVP)** (2026-07-19) · Mode A + Mode B as **separate** Alternate presets · PRODUCTION unchanged  
**Depends on:** `ASI-P4` Alternate (TEP open-gate kept)  
**Charter:** [`adaptive_selection_phases.md`](adaptive_selection_phases.md)  
**Decisions:** Mode B [`../AI/kb/decisions/20260719_ASI_P5_TEP_MID_BSL_01_Alternate.md`](../AI/kb/decisions/20260719_ASI_P5_TEP_MID_BSL_01_Alternate.md)

## What it does

Score `P(eventual steamroller | open features, warn_depth)` when the grid first reaches depth `D` (milestones 2…5).

| Mode | Preset | Behaviour |
| ---- | ------ | --------- |
| **A** | `ASI_P5_TEP_MID_01` | TEP skip + **log** `mid_warn` only |
| **B** | `ASI_P5_TEP_MID_BSL_01` | TEP skip + mid_warn + **early close** (`MID_WARN`) |

Keep as **two presets** — do not fold B into A or into `ASI_P4_TEP_GUARD_01`.

## Promote bar

**Survival across regimes** (PF > 1, contained DD). Not required to beat PRODUCTION.

## Leakage rule

| Allowed at warn time | Forbidden as features |
| -------------------- | --------------------- |
| Basket-open snapshot + TEP derived | `profit`, `mae`, `mfe`, `hit_bsl` |
| `warn_depth` (level just filled) | Future path beyond current depth |
| `is_sell` / direction | Outcome labels as inputs |

## Offline pipeline

```powershell
cd AI
python -m fema_ops asi-mid-build --split-profile long
python -m fema_ops asi-mid-train --max-skip 0.15
python -m fema_ops asi-mid-review
python -m fema_ops asi-export-mid-gate
```

Copy `mid_gate_v1.txt` (+ `tep_gate_v1.txt`) → `Common\Files\FEMA_AI\`.

## Offline result (2026-07-19)

| Metric | Value |
| ------ | ----- |
| Threshold | **0.659** |
| AUC calibrate | **0.612** |
| Warn rate / precision | **5.1%** / **57.6%** |
| Verdict | **MID WARN OK** |

## Tester — Mode B survival (`ASI_P5_TEP_MID_BSL_01`, deposit 400)

| Window | PF | Net | Equity DD | Trades | Note |
| ------ | --: | ---: | --------: | -----: | ---- |
| **2026** | **1.44** | +$200 | ~19% | 409 | Survives |
| **2018–25** | **1.35** | +$162 | ~23% | 517 | Survives vs TEP-only ~PF1 / DD~55% |

**Decision:** **Alternate** — own opt-in preset. Caveats: sparse n vs TEP-only; Jan/Dec-heavy seasonality.

Profile: [`../AI/kb/profiles/prof_ASI_P5_TEP_MID_BSL_01.json`](../AI/kb/profiles/prof_ASI_P5_TEP_MID_BSL_01.json)

## EA inputs (v1.28+)

| Input | Mode A | Mode B |
| ----- | ------ | ------ |
| `InpUseAiTepGate` | true | true |
| `InpUseAiMidWarn` | true | true |
| `InpUseAiMidEarlyBsl` | false | **true** |

## Next

- Optional: Mode A 2018–25 @ 400 for clean A-vs-B table  
- Do **not** replace PRODUCTION  
- Next track: `ASI-P6` when ready  
