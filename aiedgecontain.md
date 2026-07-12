# FEMA — AI Edge Contain

> **ARCHIVE / SUPPORTING CHAPTER** — not the active build spine.  
> **Active:** [`edgelifecycle.md`](edgelifecycle.md) (process) · [`infrascaleup.md`](infrascaleup.md) (Ops Plane §16) · [`AI/STATUS.md`](AI/STATUS.md).  
> This file records offline contain experiments (EC0–EC2). Do not treat it as a competing roadmap.

**Status:** **EC2 complete (shadow empty)** — no transferable P(fail) · approve-by-default · ready for EC3  
**Job:** Build **guardrails** around the locked PRODUCTION edge — not beat it, not replace it.  
**Live / demo:** Run `FEMA_EURUSD_M5_PRODUCTION` unchanged.  
**Config:** [`AI/windows.json`](AI/windows.json) · tooling [`AI/README.md`](AI/README.md) · ingest [`AI/ec0_ingest.py`](AI/ec0_ingest.py)

> **Separate from** [`ai_enhance.md`](ai_enhance.md) (older AI0–AI4 exploration that used 2026 PRODUCTION as a beat-this gate). Do not mix scoreboards.

---

## One-line charter

> **PRODUCTION trades the edge on demo; AI Edge Contain learns on 2020–2025 how to soft-skip / pause only clear anti-edge — approve by default, never redesign the engine.**

---

## Guardrails vs gates

| | Guardrail (this doc) | Gate (old habit — avoid) |
| - | -------------------- | ------------------------ |
| Job | Catch steamrollers / edge death | Beat 2026 PRODUCTION PF/DD |
| Default | **Approve** — engine trades | Hold back until AI “wins” |
| Build data | **2020–2025** train/holdout | Force lift on 2026 lock |
| Demo | PRODUCTION as-is | Block progress until AI > demo |
| Success | Bad-path precision · DD damage avoided · ≤15% skip/pause | PF ≥ 2026 baseline |

---

## Architecture

```
PRODUCTION Engine (demo / live)
        │
        ▼
  candidate basket / add / hold
        │
        ▼
AI Edge Contain (shadow → later opt-in)
        │
   Approve | Soft-skip | Pause new | Log
        │
        ▼
   Execution (engine logic frozen)
```

AI does **not** invent entries, retune EMA/TP/SL, or run elite-only filters.

---

## Data windows

| Role | Window | Purpose |
| ---- | ------ | ------- |
| **Demo / live edge** | Ongoing (incl. 2026) | PRODUCTION unchanged — **not** AI homework |
| **AI collect** | **2020.01.01 → 2025.12.31** | One AI0 tester run |
| **AI train** | **2020.01.01 → 2023.12.31** | Fit regime / fail / health / prob |
| **AI holdout** | **2024.01.01 → 2025.12.31** | Guardrail quality bar |
| **Optional sanity** | 2026 Jan–Jul | Later demo shadow — must not starve PRODUCTION |

**Stack:** EURUSD M5 · BSL $25 + ADX(14)&lt;30 + basket TP $10 · `InpUseAiEventLog=true`

### Collect checklist

1. Strategy Tester: PRODUCTION `.set` · Every tick · deposit **≥ enough to finish** (see note)  
2. Dates: **From `2020.01.01` · To `2025.12.31`**  
3. After run: open Agent `MQL5/Files/FEMA_AI/*_baskets.csv`  
4. Confirm **last `open_time` is in 2025** (reject truncated runs)  
5. Copy → `AI/data/EURUSD_baskets_2020_2025.csv`  
6. Ingest:

```bash
python AI/ec0_ingest.py --from-agent "PATH\\To\\Agent\\MQL5\\Files\\FEMA_AI\\EURUSD_*_baskets.csv" --deposit <tester_deposit>
```

**Deposit note:** Use a larger tester deposit only so the account does not wipe before 2025. It is **not** a strategy / lot-size change. Grade guardrails on basket PF / WR / BSL / skip precision — not on absolute DD% vs the $400 demo.

---

## Guardrail pass (build bar)

| Check | Pass |
| ----- | ---- |
| Approve by default | Uncertain → **trade** |
| Budget | Skip/pause ≤ **15%** of holdout baskets |
| Bad-path quality | Skipped/paused mostly losers / BSL · **net avoided ≤ 0** |
| Stress | Helps before known DD troughs |
| Trade count | ≥ **85%** of unfiltered holdout |
| **Not required** | PF ≥ 2026 PRODUCTION demo baseline |

Wire to EA only after holdout pass **and** optional demo shadow does not starve PRODUCTION.

---

## Soft policy

```
clear failure / death stress  → soft-skip or pause new baskets
uncertain                     → approve   # default = engine trades
```

Not:

```
P(TP) ≥ 0.85 → trade          # elite gate
AI must beat 2026 demo PF     # wrong scoreboard
```

---

## Phase map (this framework)

| ID | Name | Wire? | Goal |
| -- | ---- | ----- | ---- |
| **EC0** | Pipeline + 2020–2025 collect / split | No | Labeled baskets + features |
| **EC1** | Regime atlas (coarse) | No | Which states pay / hurt on holdout |
| **EC2** | Failure / steamroller guardrail | Shadow | High precision on bad paths |
| **EC3** | Edge health / death pause | Shadow | Pause new when rolling edge is sick |
| **EC4** | P(TP) confidence | Log only | Tie-break — never solo elite filter |
| **EC5** | Soft fusion | Shadow | Approve-by-default combine |
| **EC6** | Demo shadow → opt-in wire | Yes (opt-in) | Guardrail in front of entry |
| **EC7** | Retrain loop | Yes | Keep guardrails current |

Reuse existing scripts where possible (`AI/regime_atlas.py`, `failure_predictor.py`, `edge_health.py`, `edge_prob.py`, `replay.py`, `split_2020_2025.py`) but **point them at 2020–23 / 2024–25** and score with the **guardrail pass** bar — not legacy beat-2026 AI-G1.

---

### EC0 — Pipeline + collect / split

**ID:** `EC0-DATA`  
**Status:** **Complete** — full span ingested · plan split **2020–23 / 2024–25** frozen  
**Objective:** One clean 2020–2025 AI0 corpus and offline train/holdout files. No model decisions.

| ID | Task | Status |
| -- | ---- | ------ |
| `EC0-001` | Tester run: PRODUCTION + `InpUseAiEventLog` · `2020.01.01 → 2025.12.31` | ✅ larger deposit so run finished |
| `EC0-002` | Verify CSV span (first ~2020, **last open_time in 2025**) | ✅ `2020.01.02 → 2025.12.11` (1315 baskets) |
| `EC0-003` | Copy Agent `*_baskets.csv` → `AI/data/EURUSD_baskets_2020_2025.csv` | ✅ |
| `EC0-004` | Repair sequential `basket_id` | ✅ 1315 unique |
| `EC0-005` | Build labeled dataset (`y_fail`, features at open) | ✅ `dataset_2020_2025.csv` |
| `EC0-006` | Split train `2020–2023` / holdout `2024–2025` | ✅ plan split |
| `EC0-007` | Zero-skip replay sanity on full collect | ✅ matches |
| `EC0-008` | Publish split report + holdout baseline | ✅ `ec0_holdout_baseline.json` |

**Exit:** Train + holdout CSVs exist, IDs unique, holdout baseline frozen for guardrail compares.

#### Frozen corpus (EC0)

| | Window | n | PF | net | note |
| - | ------ | - | -- | --- | ---- |
| Full collect | 2020.01–2025.12 | 1315 | 0.96 | −$431 | Tester deposit elevated to finish only |
| Train | 2020–2023 | 936 | 0.94 | −$412 | Fit models here |
| Holdout | 2024–2025 | 379 | 0.99 | −$19 | Guardrail bar |

Artifacts: `AI/data/ec0_status.json` · `dataset_train_2020_2023.csv` · `dataset_holdout_2024_2025.csv` · `ec0_holdout_baseline.json`

**Deposit:** Tester used ~$1000 so equity survived to 2025. Ignore for strategy/lot sizing — use PF / WR / BSL / basket nets for EC1+. Absolute DD% is deposit-relative only.

#### Tester settings (EC0-001)

| Setting | Value |
| ------- | ----- |
| EA / preset | `FEMA` · Inputs → load **`Presets/PRODUCTION.set`** |
| Symbol / TF | EURUSD · M5 |
| Model | Every tick based on real ticks |
| Deposit | Elevated only to finish collect (ignore vs $400 demo) |
| Dates | **From `2020.01.01` · To `2025.12.31`** |
| AI log | `InpUseAiEventLog=true` (in PRODUCTION.set) |
| Compile | **v1.24+** |

#### Collect history

| Attempt | Actual CSV span | Baskets | Note |
| ------- | --------------- | ------- | ---- |
| 2015→2026 (earlier) | 2015.01–2015.05 | 155 | Truncated |
| **2020→2025 (pre-v1.24)** | 2020.01–2020.02 | 22 | SUSPEND forever — fixed v1.24 |
| **2020→2025 (v1.24, $400)** | 2020.01–2023.12 | 935 | Equity wipe — no 2024–25 |
| **2020→2025 (v1.24, larger deposit)** | **2020.01–2025.12** | **1315** | **EC0 corpus** |

---

### EC1 — Regime atlas (coarse)

**ID:** `EC1-REGIME`  
**Status:** **Complete** — soft-skip list **empty** (valid exit) · scorecard at [`AI/data/regime_scorecard.md`](AI/data/regime_scorecard.md)  
**Objective:** Few rule regimes → pay/hurt map on **holdout**. Soft-skip only if train toxic **and** holdout confirms — empty list OK.

| ID | Task | Status |
| -- | ---- | ------ |
| `EC1-001` | Assign coarse regimes on contain splits | ✅ |
| `EC1-002` | Scorecard train vs holdout | ✅ |
| `EC1-003` | Publish `regime_scorecard` | ✅ `AI/data/regime_scorecard.{json,md}` |
| `EC1-004` | Candidate toxic list (holdout-confirmed, ≤10%) | ✅ **none** — no train-toxic regime |
| `EC1-005` | Soft-skip mask replay on holdout | ✅ empty mask · approve-by-default · gates pass |

**Exit:** Met — empty skip list under approve-by-default.

#### Key map (holdout 2024–2025)

| Pays | Hurts (do **not** soft-skip — not train-toxic) |
| ---- | ---------------------------------------------- |
| `shallow_pullback` PF 1.47 · `expansion` 2.35 · `grinding` 1.74 | `high_adx` PF 0.58 (93 baskets) · `compression` 0.76 |

`high_adx` is the main holdout steamroller but train PF was 0.90 / BSL 31% — below toxic bar. Leave for **EC2** (failure predictor), not a regime hard-skip.

#### Nested calibrate (`regime_nested.py`)

Fit 2020–21 → pick X on 2022–23 → one eval 2024–25. Rule: `PF < fit_all×0.9` OR `BSL ≥ median+X`, share ≤10%.

| Result | Detail |
| ------ | ------ |
| Frozen gate | **empty** (approve-by-default) |
| Rejected candidate | `grinding`+`transition` — cal net −$110 but precision ~35%; holdout skipped set **+$44** (winners) |
| Why not `high_adx` | Fit PF 0.78 (toxic) but **~26% share** — cannot pack under 10% budget |

Artifacts: [`AI/data/regime_nested_scorecard.md`](AI/data/regime_nested_scorecard.md) · script [`AI/regime_nested.py`](AI/regime_nested.py)

**Implication:** Coarse regime soft-skip cannot catch the steamroller under the ≤10% budget → **EC2** (basket-level) is the working gate.

---

### EC2 — Failure / steamroller guardrail

**ID:** `EC2-FAIL`  
**Status:** **Complete — `shadow_empty_cal_no_eligible_policy`** (do not wire)  
**Objective:** P(fail / BSL path) at basket open — skip only clear losers. **Precision on skips > recall.**

| ID | Task | Status |
| -- | ---- | ------ |
| `EC2-001` | Label `y_fail` on 2020–25 | ✅ in dataset |
| `EC2-002` | Train on 2020–2023 (gbdt / logistic) | ✅ |
| `EC2-003` | Lock skip quantile on late-train cal | ✅ empty — no cal policy hit prec≥50% + net≤0 |
| `EC2-004` | Single eval 2024–2025 | ✅ |
| `EC2-005` | Shadow CSV | ✅ `AI/data/ec2/ec2_shadow.csv` |
| `EC2-006` | Guardrail score | ✅ empty skip passes by approve-default |

**Exit:** Explicit **logging / empty soft-skip** — not a fake promote.

#### Holdout result (canonical gbdt + regime)

| | |
| - | - |
| AUC train / holdout | 0.64 / **0.49** (no rank signal) |
| Locked skip_q | **0%** (cal ineligible) |
| Logistic alt | skip 12% but holdout prec ~26%, net skipped **+$114** → `reject_shadow` |

Artifacts: [`AI/data/ec2/ec2_report.md`](AI/data/ec2/ec2_report.md) · [`AI/data/ec2/ec2_comparison.md`](AI/data/ec2/ec2_comparison.md)

**Implication:** Basket-open features do not predict fail better than chance on 2024–25. Steamroller containment needs **EC3** (rolling edge health / pause), not a static P(fail) skip.

---

### EC3 — Edge health / death pause

**ID:** `EC3-HEALTH`  
**Objective:** Rolling PF / expectancy / BSL / window-DD → health 0–100 → pause **new** baskets when edge is sick.

| ID | Task |
| -- | ---- |
| `EC3-001` | Define rolling window (N baskets) on contain data |
| `EC3-002` | Health score 0–100 + ladder (high / medium / low / critical) |
| `EC3-003` | Stress-confirm pause rule (neg edge + roll DD / BSL heat) |
| `EC3-004` | Calibrate on train; eval pause quality on holdout |
| `EC3-005` | Trough-catch check: pause before known DD episodes |
| `EC3-006` | Shadow log health / action / pause_new per basket |

**Exit:** Holdout pauses mostly damaging paths (or documented reject); train trough-catch reported; no TP/SL retune.

---

### EC4 — P(TP) confidence (permissive)

**ID:** `EC4-PROB`  
**Objective:** P(hit TP) for logging / tie-break only. **Never** solo elite filter.

| ID | Task |
| -- | ---- |
| `EC4-001` | Train P(TP) on 2020–2023 |
| `EC4-002` | Score holdout; report AUC (transfer check) |
| `EC4-003` | Ablation: EC4-only skip (must **fail** policy if used alone) |
| `EC4-004` | Ablation: EC2 ∩ low-P(TP) assist — keep only if precision rises |
| `EC4-005` | Shadow confidence log for fusion / explainability |

**Exit:** Logging artifact always; `soft_assist` only if holdout assist beats EC2-alone on bad-path precision under budget.

---

### EC5 — Soft fusion

**ID:** `EC5-FUSION`  
**Objective:** Combine regime + fail + health (+ optional P(TP)) with **approve-by-default**.

| ID | Task |
| -- | ---- |
| `EC5-001` | Fusion rule v1 in replay (pseudocode below) |
| `EC5-002` | Ablations: EC2-only · EC2+EC1 · EC2+EC3 · full |
| `EC5-003` | Lock soft thresholds that pass **holdout guardrail bar** |
| `EC5-004` | Explainability dump per decision (regime, fail_p, health, p_tp, action) |
| `EC5-005` | Budget + precision report on holdout |

**Fusion rule (v1):**

```
IF health == critical (+ stress confirm)     → pause new baskets
ELSE IF regime in toxic_set
     AND fail_p clearly elevated             → soft-skip
ELSE IF fail_p clearly elevated              → soft-skip
ELSE IF EC4 assist only when EC2 also flags  → soft-skip
ELSE                                         → approve   # default
```

**Exit:** Best ablation passes holdout guardrail bar; skip/pause ≤15%; majority skipped set is bad paths.

---

### EC6 — Demo shadow → opt-in wire

**ID:** `EC6-WIRE`  
**Objective:** Shadow on demo / optional 2026 sanity, then opt-in soft guardrail in EA — engine untouched.

| ID | Task |
| -- | ---- |
| `EC6-001` | Shadow fusion on demo-era / live-like log (no orders changed) |
| `EC6-002` | Confirm does **not** starve PRODUCTION (budget + approve-default) |
| `EC6-003` | Opt-in EA input: `InpUseAiContain` (or equivalent) — off by default |
| `EC6-004` | Wire soft-skip / pause-new only; no TP/SL/EMA changes |
| `EC6-005` | Journal / CSV: decision reason per blocked candidate |
| `EC6-006` | Rollback switch (one input → full PRODUCTION behaviour) |

**Exit:** Demo shadow OK; opt-in wire behind flag; instant disable path documented.

---

### EC7 — Retrain loop

**ID:** `EC7-RETRAIN`  
**Objective:** Rolling retrain so guardrails track regime drift — without replacing PRODUCTION.

| ID | Task |
| -- | ---- |
| `EC7-001` | Retrain calendar (e.g. monthly / every N baskets) |
| `EC7-002` | Registry: model version · train span · holdout metrics · promote/reject |
| `EC7-003` | Promote only if new model passes holdout guardrail bar vs previous |
| `EC7-004` | Keep last-known-good model on fail |
| `EC7-005` | Optional: append recent demo shadow baskets into retrain corpus (careful leakage rules) |

**Exit:** Documented retrain + promote/reject path; no silent overwrite of a working contain model.

---

### Deferred (not in EC0–EC7)

| ID | Item | Why deferred |
| -- | ---- | ------------ |
| `EC-X-001` | Mid-basket early-close recovery | Easy to recreate RTE/trail failures |
| `EC-X-002` | Adaptive EMA / TP / SL | Changes engine character |
| `EC-X-003` | 30–50 fine regimes / elite ranking | Overfilter + sparse labels |
| `EC-X-004` | RL policy / heavy memory search | After contain fusion is stable |

---

## Anti-goals

| Do not | Why |
| ------ | --- |
| Ask AI where to buy/sell | Engine already does that |
| Elite-only / high-confidence-only | Phase 2 overfilter failure mode |
| Beat 2026 PRODUCTION to “pass” AI | Demo edge ≠ AI schoolyard |
| Blend all years into one PF trophy | Hides fade vs containment quality |
| Wild EMA / TP / SL retunes | Changes engine character |
| Wire before holdout guardrail pass | Premature live risk |

---

## Relation to other docs

| Doc | Role |
| --- | ---- |
| **`aiedgecontain.md` (this file)** | Offline AI guardrail build (EC0–EC7) |
| [`edgelifecycle.md`](edgelifecycle.md) | **Operator loop** find → run → watch fade → rediscover (EL0–EL8) |
| [`ai_enhance.md`](ai_enhance.md) | Legacy AI0–AI4 notes / beat-2026 experiments — archive reference |
| [`AI/windows.json`](AI/windows.json) | Machine-readable windows + pass criteria |
| [`AI/baseline.json`](AI/baseline.json) | PRODUCTION demo edge freeze (reference, not AI grade) |
| [`System Profile EURUSD.md`](System%20Profile%20EURUSD.md) | Locked engine stack |
| [`Edge Discovery.md`](Edge%20Discovery.md) | How PRODUCTION was found — not AI training |

---

## Immediate next step

**EC3** — edge health / death pause (rolling PF · BSL heat · pause new baskets when edge is sick).

Confirm journal has baskets / activity after **2020.03**, then: `python AI/ec0_ingest.py --from-agent "<Agent FEMA_AI baskets.csv>"`.
