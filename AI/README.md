# FEMA AI — Offline tooling

**Active framework:** [`../edgelifecycle.md`](../edgelifecycle.md) (spine) · glance [`STATUS.md`](STATUS.md) · contain notes [`../aiedgecontain.md`](../aiedgecontain.md)
**Schemas:** [`schemas/README.md`](schemas/README.md) · `fema_baskets_v2` / `fema_events_v2` (EA **v1.25+**)

Offline tooling for Edge Ops. **No model decisions in the EA.**

## Deliverables

| ID | Status | Location |
| -- | ------ | -------- |
| INF-LOG | Done (v1.25) | Schema meta + fingerprint + ORDER_FAIL/LIFECYCLE |
| INF-EXPORT | Done | `AI/data/live/latest_*` via `sync_from_agent.py` |
| INF-CERT | Done | `certificate_PRODUCTION_EURUSD.json` + `cert_loader.py` |
| INF-OPS | Done | `fema_ops` · `health_v0` · `python -m fema_ops health` |
| INF-RUN | Done | `AI/kb/runs/` · `python -m fema_ops register` / `list-runs` |
| INF-PRESET | Done | `Presets/manifest.json` · `fema_ops clone` · search map · gates |
| INF-EA | Done (v1.26) | `*_run_config.json` · `InpReadPauseNewFlag` (default off) |
| INF-STATUS | Done | `AI/STATUS.md` · `python -m fema_ops status` |
| INF-DOCKER | Done | `AI/Dockerfile` · [`DOCKER.md`](DOCKER.md) · no MT5 |
| EL0–EL3 | Done | Baseline · run_ids · gates · `cert-confirm` lock |
| EL6 | Shadow | `would_pause_new` · `pause-check` · `pause-flag` |
| AI0-001 | Done | EA CSV event stream (`*_events.csv`) |
| AI0-002 | Done | Feature snapshot columns on candidate/fill/open |
| AI0-003 | Done | Basket outcome labels (`*_baskets.csv`) |
| AI0-004 | Done | `build_dataset.py` (+ `csv_util.py`) |
| AI0-005 | Done | `replay.py` |
| AI0-006 | Done | `baseline.json` (PRODUCTION freeze) |

## EA side (v1.25+)

1. Compile `FEMA.mq5` **v1.26** (journal: `Init v1.26` · `pause_flag=off|armed|ON` · `AI log ... run_id=...`).
2. Run Strategy Tester / demo with PRODUCTION (`InpUseAiEventLog=true`).
3. **Primary CSV location after a tester run:**

```
%APPDATA%\MetaQuotes\Tester\<terminal_id>\Agent-*\MQL5\Files\FEMA_AI\
  EURUSD_<magic>_events.csv
  EURUSD_<magic>_baskets.csv
  EURUSD_<magic>_run.meta.txt
  EURUSD_<magic>_run_config.json   # INF-EA edge Inp* snapshot
```

4. **Sync to stable repo paths (INF-EXPORT):**

```powershell
.\AI\sync_from_agent.ps1
# or: python AI/sync_from_agent.py
```

Writes `AI/data/live/latest_baskets.csv`, `latest_events.csv`, `latest_run.meta.txt`.  
Scripts should use `from paths import LATEST_BASKETS` — never hardcode Agent paths.  
Readers: `from csv_util import read_csv_rows`.

**AI0 status (2026-07-11):** complete — 108 baskets · PF 1.40 · dataset + zero-skip replay OK.

**AI1 status (2026-07-11):** complete — `python AI/regime_atlas.py` · soft-skip **empty** (holdout-safe) · see `AI/data/regime_scorecard.md`.

**AI2 status (2026-07-11):** complete (shadow) — `python AI/failure_predictor.py --model gbdt` · status `fragile_shadow_g1_thin_sample` · validate AUC ~0.48 · **do not wire**. See `AI/data/ai2_report.md`.

**AI3 status (2026-07-11):** complete (shadow) — `python AI/edge_health.py` · status `reject_shadow` · train trough catch 3/3 but validate pauses winners · **do not wire**. See `AI/data/ai3_report.md`.

**AI4 status (2026-07-11):** complete (logging-only) — `python AI/edge_prob.py` · AUC val ~0.40 · no AI2 assist lift · **do not skip on P(TP) alone**. See `AI/data/ai4_report.md`.

## Data windows

| Role | Period |
| ---- | ------ |
| **Demo / live edge** | PRODUCTION as-is (incl. 2026) — not an AI beat-this gate |
| **AI collect** | **2020.01.01 → 2025.12.31** |
| **AI train** | **2020.01.01 → 2023.12.31** |
| **AI holdout (guardrails)** | **2024.01.01 → 2025.12.31** |

See [`windows.json`](windows.json) and [`../ai_enhance.md`](../ai_enhance.md) § Guardrails vs gates.

Collect AI0 CSV with tester `FromDate=2020.01.01` `ToDate=2025.12.31`, copy Agent `FEMA_AI/*_baskets.csv` → `AI/data/EURUSD_baskets_2020_2025.csv`, then:

```bash
python AI/split_2020_2025.py --baskets AI/data/EURUSD_baskets_2020_2025.csv
```

Confirm last `open_time` is in **2025** before training (prior “long” runs truncated early).

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

# AI Edge Contain — EC0 ingest (after 2020-2025 tester collect)
python AI/ec0_ingest.py --from-agent "PATH/TO/Agent/MQL5/Files/FEMA_AI/EURUSD_*_baskets.csv"

# Sync live CSVs
python AI/sync_from_agent.py
# EL4 demo (Wave 0 default):
python -m fema_ops ingest --source demo
python -m fema_ops observatory
# Tester Discovery collect only:
python -m fema_ops ingest --source tester

# Certificate health_v0 (INF-OPS / EL5 shadow)
cd AI
python -m fema_ops health
# or from repo root:
python AI/edge_health_cert.py
python AI/edge_health_cert.py --baskets AI/data/EURUSD_20260707_baskets.csv --no-state

# Unit tests
python -m unittest AI.tests.test_health_v0
python -m unittest AI.tests.test_runs
python -m unittest AI.tests.test_gates
python -m unittest AI.tests.test_lock_confirm

# Register a tester/demo slice (INF-RUN)
cd AI
python -m fema_ops register --baskets data/EURUSD_20260707_baskets.csv --preset PRODUCTION --role lock --from 2026.01.01 --to 2026.07.31
python -m fema_ops list-runs

# EL1 Discovery table -> documented run_ids
python -m fema_ops backfill-discovery

# EL2 G1 gate / KB polish
python -m fema_ops gate-polish
python -m fema_ops gate-check --pf 1.40 --dd 19
# Decision: AI/kb/el2_promote_decision.md · checklist: AI/templates/promotion_checklist.md

# EL3 lock / certificate confirm
python -m fema_ops cert-confirm
# Report: AI/kb/el3_lock_confirm.md

# Clone PRODUCTION -> one-subsystem candidate (INF-PRESET)
python -m fema_ops clone --list-subsystems
python -m fema_ops clone --id Candidate_X1 --subsystem session --set InpUseSessionBlockNo23=true --notes "Watch queue"
python -m fema_ops list-presets

# EL6 pause shadow
python -m fema_ops health
python -m fema_ops pause-check
python -m fema_ops pause-flag
# Wire only after review: copy AI/data/live/pause_new.flag -> MT5 Files\FEMA_AI\
# and set InpReadPauseNewFlag=true (default remains false)

# Docker (INF-DOCKER — Python only, no MT5)
# From repo root:
#   docker build -f AI/Dockerfile -t fema-ops .
#   docker compose -f AI/docker-compose.yml run --rm fema_ops health
# See AI/DOCKER.md

# AI3 edge health (legacy AI-G1 pause calibrator — not certificate health)
python AI/edge_health.py

# AI4 P(TP) confidence (logging / AI2 assist ablations)
python AI/edge_prob.py --model gbdt
```

Stdlib only. Optional Parquet if `pandas` + `pyarrow` are installed.

## AI-G1 note

`baseline.json` locks tester PRODUCTION metrics. Basket-CSV PF/WR should be close after a full Jan–Jul run; equity DD in `replay.py` is a **basket-equity approximation**, not MT5 equity DD.

## Next

1. Tester: PRODUCTION + `InpUseAiEventLog=true` · **2020.01.01 → 2025.12.31** · Every tick · $400  
2. Copy Agent baskets → `AI/data/EURUSD_baskets_2020_2025.csv`  
3. `python AI/split_2020_2025.py`  
4. Rebuild AI1–AI4 on train/holdout as **guardrails** (bad-path catch), not beat-2026 gates.
