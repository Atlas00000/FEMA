# Clone playbook (INF-PRESET / ESR-W10 / Wave 4 factory)

**Goal:** Fork a **parent** preset → one candidate (Lane A: PRODUCTION + one subsystem). Bookkeeping only — not genetic search.  
**Hybrid (adopted):** [`../../doc/dual_lane_rediscovery_pipeline.md`](../../doc/dual_lane_rediscovery_pipeline.md) — Lane A = this playbook; Lane B = multi-base challengers (`DLR-P3` MVP · [`challenger_roster.md`](challenger_roster.md) · [`dlr_policy.json`](dlr_policy.json)).

## Factory path (preferred when genome mismatches)

```powershell
cd AI
python -m fema_ops recommend          # <=3 subsystems from compatibility
python -m fema_ops factory            # dry-run propose index 0
python -m fema_ops factory --apply --index 0
# or: python -m fema_ops factory --apply --subsystem adx --hypothesis "ADX drift"
```

## Manual clone

```powershell
cd AI
python -m fema_ops clone --id Candidate_X1 --subsystem session --set InpUseSessionBlockNo23=true --notes "Watch queue example"
```

3. Load `Presets/Candidate_X1.set` in Strategy Tester (same window as lock unless noted).
4. After the run: `python -m fema_ops register ... --role candidate --preset Candidate_X1`
5. Update `candidates.csv` status (`tested` / `pass` / `fail`) and cite `run_id`.
6. Apply **G1** from [`gate_rules.json`](gate_rules.json): PF **and** DD vs PRODUCTION. Human promote only.

## Limits

- ≤ **3** active queued candidates from a Watch ladder (not 30) — **Lane A** wave.
- ≤ **2** queued **Lane B** challengers (separate cap) — see [`challenger_roster.md`](challenger_roster.md).
- Lane B presets: `Challenger_{ParentToken}_{ThesisToken}_{NN}` (never overnight-default).
- Do not touch frozen axes (lot philosophy, execution architecture).
- Never auto-promote to PRODUCTION.
- Re-Discovery: [`el7_rediscovery_runbook.md`](el7_rediscovery_runbook.md) · snapshot [`../../doc/edge_rediscovery_system.md`](../../doc/edge_rediscovery_system.md)
