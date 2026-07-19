# ASI guardrail review — TEP holdout (not production parity)

Generated: `2026-07-17T16:51:24Z`
Split profile: **long_train**
Threshold: **0.649755** (frozen from calibrate tune)

## Philosophy

Candidate must pass **kill gates** on the guardrail holdout window. We do **not** require beating or matching live PRODUCTION PF/WR.

## Holdout (2025.01.01–2025.12.31)

| Metric | Value |
| ------ | ----: |
| n | 217 |
| skip_n / rate | 5 / 0.023 |
| steamroller precision | 0.6 |
| false-skip winners | 2 |
| skipped steamrollers | 3 |
| net skipped | -55.13 |
| DD all → if skipped | 48.93% → 45.71% (Δ 3.22%) |

## Kill criteria (holdout)

- status: **`ok`** → `continue_shadow`
- reasons: _(none)_

**Verdict:** GUARDRAIL OK — holdout passes kill gates

## All slices

| Slice | window | n | skip | precision | false wins | net skip | DD Δ% | kill |
| ----- | ------ | -: | ---: | --------: | ---------: | -------: | ----: | ---- |
| holdout_calibrate | 2025.01.01–2025.12.31 | 217 | 5 (0.023) | 0.6 | 2 | -55.13 | 3.22 | ok |
| train_in_sample | 2018.01.01–2024.12.31 | 1489 | 17 (0.0114) | 0.8235 | 3 | -320.71 | 22.47 | ok |
| research_full | research_full | 1820 | 29 (0.0159) | 0.6552 | 10 | -375.69 | 26.87 | ok |

NO AUTO-PROMOTE · guardrail candidate ≠ production lock.
