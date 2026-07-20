# ASI-P6 — Basket recovery probability pack

**Status:** **COMPLETE (MVP offline)** (2026-07-19) · shadow recommend only · no MQL wire · PRODUCTION unchanged  
**Depends on:** `ASI-P5` mid-basket (complementary score)  
**Charter:** [`adaptive_selection_phases.md`](adaptive_selection_phases.md)  
**Policy ADR:** [`../AI/kb/asi/rec_policy_adr.md`](../AI/kb/asi/rec_policy_adr.md)  
**Decision:** [`../AI/kb/decisions/20260719_ASI_P6_REC_SHADOW_Alternate.md`](../AI/kb/decisions/20260719_ASI_P6_REC_SHADOW_Alternate.md)

## What it does

Score `P(recover | open features, warn_depth)` at the same depth milestones as mid-warn (2…5).

| Band | Meaning | Default action |
| ---- | ------- | -------------- |
| High P(recover) | Likely finish TP/profit | **KEEP** (advisory) |
| Mid band | Uncertain | CAUTION / stop-adds — not wired |
| Low P(recover) ≤ exit_thr | Likely fail | **Recommend** early BSL (shadow only) |

Does **not** replace mid-warn. Early BSL stays human Mode B (`ASI_P5_TEP_MID_BSL_01`).

## Leakage rule

Same as P5: open snapshot + `warn_depth` + `is_sell`. Forbidden: `profit`, `mae`, `mfe`, outcomes.

## Offline pipeline

```powershell
cd AI
python -m fema_ops asi-rec-build --split-profile long
python -m fema_ops asi-rec-train --max-exit-rate 0.15
python -m fema_ops asi-rec-review
python -m fema_ops asi-rec-shadow --baskets data/EURUSD_baskets_2018_2025.csv
```

## Artifacts

| Path | Role |
| ---- | ---- |
| `AI/kb/asi/rec_dataset_*.csv` | Expanded mid-depth recovery rows |
| `AI/kb/asi/rec_model.pkl` + `rec_model_card.json` | Logistic model + exit band |
| `AI/kb/asi/asi_p6_review_pack.md` | Holdout review |
| `AI/kb/asi/asi_shadow_rec.json` | Calibrate shadow summary |

## Results (long train)

| Metric | Value |
| ------ | ----- |
| Mid-rows | 5531 · recover rate ~0.65 |
| AUC calibrate | **0.612** |
| Exit thr (low P) | **~0.341** |
| Calibrate exit rate | ~5.1% · fail precision **0.58** · net of exit set **−$332** |
| Full 2018–25 shadow | exit ~4.4% · fail prec **0.59** · net exit baskets **−$1341** |

Promote-frozen slice weak (low fail precision) → **do not wire / do not promote**.

## Non-goals

- No `InpUseAiRec*` in P6 MVP
- No merge into Mode B / PRODUCTION
- No threshold tune on 2026 canon

## Next

Optional: combine low-P(recover) **and** mid-warn before Mode B early close — new decision. Or park and proceed to `ASI-P7`.
