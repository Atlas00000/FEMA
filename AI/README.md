# FEMA AI0 — Pipeline & infra

Offline-first tooling for the Edge Preservation Layer. **No model decisions in the EA yet.**

## Deliverables

| ID | Status | Location |
| -- | ------ | -------- |
| AI0-001 | Done | EA CSV event stream (`*_events.csv`) |
| AI0-002 | Done | Feature snapshot columns on candidate/fill/open |
| AI0-003 | Done | Basket outcome labels (`*_baskets.csv`: hit_tp/bsl, mae, mfe, bars, depth) |
| AI0-004 | Done | `build_dataset.py` |
| AI0-005 | Done | `replay.py` |
| AI0-006 | Done | `baseline.json` (PRODUCTION freeze) |

## EA side (v1.21+)

1. Compile `FEMA.mq5` (journal must show `v1.21` and `ai0=on`).
2. Run Strategy Tester with PRODUCTION (`InpUseAiEventLog=true`).
3. After the run, CSVs are in:

```
%APPDATA%\MetaQuotes\Terminal\Common\Files\FEMA_AI\
  EURUSD_20260707_events.csv
  EURUSD_20260707_baskets.csv
```

(Symbol + magic in the filename.)

Copy them into `AI/data/` (gitignored) for offline work.

### Events logged

`CANDIDATE` → `SKIP` | `FILL`/`ADD` → `BASKET_OPEN` → `BASKET_CLOSE`

Skips include filter / regime / session / validation / order fail reasons.

## Offline commands

From the FEMA repo root:

```bash
# Build labeled dataset (features + y_fail)
python AI/build_dataset.py --baskets AI/data/EURUSD_20260707_baskets.csv --out AI/data/dataset.csv

# Replay with zero skips (must match full sample — AI0 exit criterion)
python AI/replay.py --baskets AI/data/EURUSD_20260707_baskets.csv --baseline AI/baseline.json

# Hypothetical soft skip list (one basket_id per line or JSON array)
python AI/replay.py --baskets AI/data/EURUSD_20260707_baskets.csv --skip-ids AI/data/skip_ids.txt
```

Stdlib only. Optional Parquet if `pandas` + `pyarrow` are installed.

## AI-G1 note

`baseline.json` locks tester PRODUCTION metrics. Basket-CSV PF/WR should be close after a full Jan–Jul run; equity DD in `replay.py` is a **basket-equity approximation**, not MT5 equity DD.

## Next

AI1 regime atlas / AI2 failure model consume `dataset.csv`. Do not wire gates until AI-G1 passes offline.
