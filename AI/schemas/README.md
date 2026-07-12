# FEMA telemetry schemas

**Active:** `fema_baskets_v2` · `fema_events_v2` (EA v1.25+) · `*_run_config.json` (v1.26+)  
**Legacy:** `fema_baskets_v1` / `fema_events_v1` — no `# FEMA_META` lines; same core columns without `retcode` / `reject_class` / `transient`.

Machine-readable field lists: [`fema_telemetry.json`](fema_telemetry.json)

## Market Fingerprint (Wave 3)

JSON Schema: [`market_fingerprint.schema.json`](market_fingerprint.schema.json)  
Compute: `python -m fema_ops fingerprint` → `AI/data/live/fingerprint_latest.json` + optional `AI/kb/runs/<run_id>/fingerprint.json`  
Genome: `AI/kb/genome_PRODUCTION.json` · compatibility shadow on health / Observatory.

## File layout

```
FEMA_AI/<symbol>_<magic>_events.csv
FEMA_AI/<symbol>_<magic>_baskets.csv
FEMA_AI/<symbol>_<magic>_run.meta.txt      # key=value fingerprint
FEMA_AI/<symbol>_<magic>_run_config.json   # INF-EA edge Inp* snapshot (v1.26+)
FEMA_AI/pause_new.flag                     # EL6 opt-in (InpReadPauseNewFlag)
```

CSV files may start with comment lines:

```
# FEMA_META schema=fema_baskets_v2
# FEMA_META run_id=...
# FEMA_META magic=...
# FEMA_META ea_build=1.25
# FEMA_META fingerprint=adx_gate=on;bsl=25;preset=PRODUCTION
# FEMA_META created=2026.07.11 21:00:00
<header row>
<data rows>
```

Python: use `AI/csv_util.py` → `read_csv_rows()` (skips `#` lines).

## Certificate metric mapping (baskets)

| Certificate need | Column(s) |
| ---------------- | --------- |
| Rolling PF / WR | `profit`, `hit_tp`, `hit_bsl` (+ offline roll) |
| Basket duration | `bars_alive` |
| Basket depth | `max_depth`, `open_level` |
| MAE / MFE | `mae`, `mfe` |
| Spread / execution | events: `spread_points`, `retcode`, `reject_class` |
| Regime context | `adx`, `atr`, `ema_*` at open |

## Events v2 extras

| Column | Meaning |
| ------ | ------- |
| `retcode` | MT5 trade retcode (0 if N/A) |
| `reject_class` | `ok` / `transient` / `no_money` / `reject` / `other` |
| `transient` | `1` if not counted toward SUSPEND |

Event `ORDER_FAIL` = structured order rejection (also still appears as SKIP with reason for back-compat).  
Event `LIFECYCLE` = SUSPEND / RESUME / etc. (`reason` = code).
