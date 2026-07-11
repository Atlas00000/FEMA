# FEMA AI — Offline tooling

**Active framework:** [`../aiedgecontain.md`](../aiedgecontain.md) (AI Edge Contain — guardrails)  
**Legacy notes:** [`../ai_enhance.md`](../ai_enhance.md) (older beat-2026 experiments)

Offline-first tooling for the Edge Contain layer. **No model decisions in the EA yet.**

## Deliverables

| ID | Status | Location |
| -- | ------ | -------- |
| AI0-001 | Done | EA CSV event stream (`*_events.csv`) |
| AI0-002 | Done | Feature snapshot columns on candidate/fill/open |
| AI0-003 | Done | Basket outcome labels (`*_baskets.csv`: hit_tp/bsl, mae, mfe, bars, depth) |
| AI0-004 | Done | `build_dataset.py` |
| AI0-005 | Done | `replay.py` |
| AI0-006 | Done | `baseline.json` (PRODUCTION freeze) |

## EA side (v1.22+)

1. Compile `FEMA.mq5` (journal: `v1.22` · `ai0=on` · `common_ok=1` · `local_ok=1`).
2. Run Strategy Tester with PRODUCTION (`InpUseAiEventLog=true`).
3. **Primary CSV location after a tester run** (non-zero size):

```
%APPDATA%\MetaQuotes\Tester\<terminal_id>\Agent-*\MQL5\Files\FEMA_AI\
  EURUSD_20260707_events.csv
  EURUSD_20260707_baskets.csv
```

Common\Files\FEMA_AI may stay small/locked until the terminal releases handles — prefer the Agent path.

Copy into `AI/data/` (gitignored) for offline work.

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

# AI3 edge health (rolling score + stress pause)
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
