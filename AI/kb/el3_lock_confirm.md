# EL3 — Production lock & certificate confirm

**Status:** **CONFIRMED**  
**Generated:** 2026-07-11T21:28:11Z  
**Lock run_id:** `20260101_PRODUCTION_13c52cd9`  
**Preset:** `FEMA_EURUSD_M5_PRODUCTION` (alias `P2C-001_REG_ADX30`)

## Fingerprint

```
{
  "adx_gate": true,
  "adx_max": 30,
  "bsl": 25.0,
  "basket_tp": 10.0,
  "magic_default": 20260707,
  "load": "FEMA_EURUSD_M5_PRODUCTION.ini",
  "preset_set": "Presets/PRODUCTION.set"
}
```

## Birth (MT5 deals / System Profile)

| Metric | Value |
| ------ | ----- |
| PF | 1.36 |
| Max DD bal | 18.0% |
| WR | 0.71 |
| Trades | 424 |
| Unit | mt5_deals |

## Checks

| ID | OK | Detail |
| -- | -- | ------ |
| `EL3-003_cert_files` | PASS | json=certificate_PRODUCTION_EURUSD.json md=certificate_PRODUCTION_EURUSD.md |
| `EL3-005_weights_sum` | PASS | sum=1.0 |
| `EL3-005_windows` | PASS | windows=[50, 100, 250] primary=100 |
| `EL3-005_birth_vs_gates` | PASS | pf=1.36 dd=18.0 window=2026.01.01-2026.07.31 run_id=20260101_PRODUCTION_13c52cd9 |
| `EL3-001_lock_run` | PASS | role=lock baskets_pf=1.3968 |
| `EL3-001_kb_lock_row` | PASS | found 20260101_PRODUCTION_13c52cd9 |
| `EL3-001_el2_decision` | PASS | exists=True |
| `EL3-004_preset_fingerprint` | PASS | {"adx_gate":true,"adx_max":true,"bsl":true,"basket_tp":true,"magic":true,"file":true} |
| `EL3-002_frozen_stack` | PASS | EMA20/100 + BSL on + HTF/ATRp/session off |
| `EL3-001_system_profile` | PASS | exists=True |
| `EL3-001_ini_load_name` | PASS | cert.load=FEMA_EURUSD_M5_PRODUCTION.ini in_repo=False (Settings .ini may live outside Experts/FEMA) |
| `EL3-005_birth_unit_note` | PASS | cert birth unit=mt5_deals PF=1.36; lock baskets PF=1.3968 (not required equal) |

**Summary:** 12/12 passed · failed=0

## Exit

Certificate data + docs + preset fingerprint confirmed. Demo/live load must still show `adx_gate=on` · `bsl=25` in the journal (operator check).

