# ASI-P3 review pack — TEP shadow vs PRODUCTION canon

Generated: `2026-07-17T09:01:07Z`
Threshold: **0.600899** (frozen from P2 calibrate)

## Compare (canonical 2026.01–07)

| Slice | n | PF | WR | Net | DD% (equity proxy) |
| ----- | -: | --: | --: | ---: | ---: |
| Baseline (all) | 111 | 1.4479 | 0.7838 | 271.12 | 18.14 |
| After TEP skip | 105 | 1.4215 | 0.781 | 244.6 | 18.93 |

- skip_n / rate: **6** / **0.0541**
- skipped_pnl: **26.52**
- steamrollers skipped: **1** · false-skip winners: **5**
- precision: **0.1667**

## Kill criteria

- status: **`kill`** → `retune_threshold_or_stop`
- reasons: ['precision 16.7% < 30%', 'false_skip_winners 5 > 2.0x steamrollers 1', 'net_skipped +26.52 > 0 (cutting winners)']

**Verdict hint:** KILL — do not proceed to live gate

## Sign-off (human)

- [ ] Shadow looks net-positive (PF/DD/n)
- [ ] False-skip winners acceptable
- [ ] Proceed to ASI-P4 design **or** retune / stop

NO AUTO-PROMOTE · no live skip until P4 + human promote.
