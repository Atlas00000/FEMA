# Clone playbook (INF-PRESET / ESR-W10 / Wave 4 factory)

**Goal:** Fork PRODUCTION → one candidate with **one subsystem** changed. Bookkeeping only — not genetic search.

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

- ≤ **3** active queued candidates from a Watch ladder (not 30).
- Do not touch frozen axes (lot philosophy, execution architecture).
- Never auto-promote to PRODUCTION.
- Re-Discovery: [`el7_rediscovery_runbook.md`](el7_rediscovery_runbook.md)
