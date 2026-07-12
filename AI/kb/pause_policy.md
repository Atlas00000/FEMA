# Pause policy (EL6 / containment §4)

**Wire default:** OFF (`InpReadPauseNewFlag=false`). Shadow fields live in health reports until a human opts in.

## Allowed

- Pause **new basket** entries only
- Continue managing open baskets (TP / SL / trail / adds on existing basket)
- Keep logging + health monitoring
- Human clear of `FEMA_AI\\pause_new.flag` (or ack resume)

## Forbidden

- Live EMA / TP / SL / BSL / lot / grid changes
- Live optimization or auto-promote
- Closing all positions just because health is low (engine exits stay in charge)

## Shadow rule (`would_pause_new`)

Pause is **recommended** when:

1. Ladder is `retire`, **or**
2. Ladder is `re_discovery` **and** persistence `warning_active`, **or**
3. Health &lt; 50 **and** persistence `warning_active`

Resume shadow when ladder recovers to `investigate` or better **and** persistence clears (2 recover windows), **or** human clears the flag.

## Flag file (opt-in wire)

Path (local + Common): `FEMA_AI\\pause_new.flag` (`InpPauseNewFlagFile`)

```
pause_new=1
reason=health_re_discovery
source=human
updated=2026.07.11 21:00:00
```

Clear / set `pause_new=0` to resume new baskets. EA polls on new M5 bar when `InpReadPauseNewFlag=true`.

## Wire decision (IS-EL6-01) — **NOT SIGNED**

| Gate | Status |
| ---- | ------ |
| `pause-check` false-positive review | Available (`fema_ops pause-check`) |
| Wave 0 demo unlock + trusted ingest | **Blocked** (Sunday / open basket) |
| `IS-EL5-01` 2w+ demo persistence trust | **Blocked** |
| Human sign-off to set `InpReadPauseNewFlag=true` | **Pending** |

**Policy:** keep wire **OFF**. Shadow `would_pause_new` only. Do not place live `pause_new.flag` for production risk until the above gates pass.

## Commands

```powershell
cd AI
python -m fema_ops health          # sets would_pause_new on report
python -m fema_ops pause-check     # backfill false-positive rate
python -m fema_ops pause-flag      # write AI/data/live/pause_new.flag from latest health (shadow copy)
```

Copy flag into MT5 `Files\\FEMA_AI\\` only after accepting wire risk (`ESR-DEF-PAUSE-WIRE`).
