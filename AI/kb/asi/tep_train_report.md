# ASI-P2 TEP train report

- variant: **tep_full**
- threshold: **0.649755**
- AUC calibrate: **0.5525**

## Calibrate (threshold tuned here)

- skip rate: **0.023**
- steamroller precision: **0.6**
- false-skip winners: **2**
- net skipped: **-55.13**

## Promote frozen (one-shot — not tuned)

- (no promote_frozen split)

## Ablation

- TEP beats static: **False**
- TEP beats ADX-only: **True**
- winner: **tep_full**
