# Challenger roster (DLR-P2)

**Artifact:** [`challenger_roster.json`](challenger_roster.json)  
**Cards:** [`profiles/`](profiles/)  
**Charter:** [`../../doc/dual_lane_rediscovery_pipeline.md`](../../doc/dual_lane_rediscovery_pipeline.md)

Lane B parents come from this roster — not from the live PRODUCTION lock.

## Naming (DLR-P2-06)

| Lane | Pattern | Example |
| ---- | ------- | ------- |
| A | `Candidate_{Token}` | `Candidate_X3` |
| B | `Challenger_{ParentToken}_{ThesisToken}_{NN}` | `Challenger_P1BASE_adx_01` |
| Profile id | `prof_{preset}` | `prof_Candidate_X2` |

**ParentToken** = short slug of the base/profile (`P1BASE`, `X2`, `P2D001`).  
**ThesisToken** = one search-map axis or short thesis (`adx`, `grid`, `nosession`).  
**NN** = 01, 02, … per parent/thesis family.

## Seeds

| Kind | Id | Eligible B | Status |
| ---- | -- | ---------- | ------ |
| Base | `P1-BASELINE` | yes | base |
| Profile | `Candidate_X2` | yes | alternate |
| Profile | `P2D-001_SES_NO23` | yes | alternate |

## Enqueue

```powershell
# Preferred wrapper
powershell -File ops\tester_queue\enqueue_lane_b.ps1 -Preset Challenger_P1BASE_adx_01 -Parent P1-BASELINE -Subsystem adx -Notes "Lane B hunt"

# Or via enqueue directly
powershell -File ops\tester_queue\enqueue.ps1 -Preset Challenger_P1BASE_adx_01 -Lane B -Parent P1-BASELINE -Role challenger -Subsystem adx
```

**Caps:** Lane A queued ≤3 · Lane B queued ≤2 (separate). Never auto-promote.
