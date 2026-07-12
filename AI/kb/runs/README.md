# FEMA run registry (INF-RUN)

Append-only experiment log. Every material tester/demo slice gets a `run_id` folder under `runs/`.

## `run_id` format

```
{YYYYMMDD}_{preset_slug}_{window_hash8}
```

| Part | Meaning |
| ---- | ------- |
| `YYYYMMDD` | Window **start** date (`20260101`), not wall-clock register time |
| `preset_slug` | Preset or alias, sanitized (`PRODUCTION`, `P2C-001_REG_ADX30`) |
| `window_hash8` | First 8 hex chars of SHA-1 over `symbol\|tf\|start\|end\|baskets_basename` |

**Example:** `20260101_PRODUCTION_a1b2c3d4`

### Related IDs (do not confuse)

| ID | Owner | Role |
| -- | ----- | ---- |
| **Registry `run_id`** | `AI/kb/runs/` | Stable Discovery / KB key |
| **EA telemetry `run_id`** | CSV `# FEMA_META` / `*_run.meta.txt` | Init timestamp + symbol_magic tag |

Store EA `run_id` inside `metrics.json` as `ea_run_id` when known. They are **not** required to match.

### Collision / overwrite

- **Never overwrite** an existing `runs/<run_id>/` folder.
- If the same window+preset is registered again, CLI appends `_02`, `_03`, … (new folder).
- Delete only by explicit human archive (EL8) — not by re-register.

## Folder layout

```
AI/kb/runs/
  README.md                 # this file
  index.json                # append-only list of registered ids
  <run_id>/
    metrics.json            # required
    SOURCE.txt              # path to baskets CSV (repo-relative preferred)
```

Large CSVs stay under `AI/data/` (gitignored). Registry stores **paths + metrics**, not copies.

## Commands

```powershell
cd AI
python -m fema_ops register --baskets data/EURUSD_20260707_baskets.csv --preset PRODUCTION --role lock --from 2026.01.01 --to 2026.07.31
python -m fema_ops list-runs
```

## Edge Discovery

When a table row is materially updated (new PF/DD/verdict), cite `run_id` in the notes/status cell or a footnote. See [`../schema.md`](schema.md).

**EL1 backfill:** seed [`../discovery_rows_seed.json`](../discovery_rows_seed.json) → `python -m fema_ops backfill-discovery` → map [`../discovery_run_ids.json`](../discovery_run_ids.json).  
Documented runs have `status=documented` and `baskets_path=null` (table metrics only). Row 22 reuses the live AI0 lock folder.
