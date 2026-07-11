# FEMA — Floating EMA Grid

MetaTrader 5 Expert Advisor. Pullback continuation on EURUSD M5 using a floating ATR grid with basket take-profit and basket stop-loss.

## Production Stack

| | |
|---|---|
| **Preset** | `FEMA_EURUSD_M5_PRODUCTION` |
| **Config** | BSL $25 + ADX(14)>30 gate + basket TP $10 |
| **PF** | **1.36** |
| **Net P/L** | +$221 (on $400 deposit) |
| **Max DD** | 18% balance / 21% equity |
| **Window** | 2026-01-01 → 2026-07-31 |

## Quick Start (Strategy Tester)

1. Compile `FEMA.mq5` in MetaEditor (v1.21+).
2. Copy `Presets/PRODUCTION.set` to `MQL5\Profiles\Tester\`.
3. Load `FEMA_EURUSD_M5_PRODUCTION.ini` via Strategy Tester → **Settings**.
4. Confirm journal: `v1.21` · `adx_gate=on` · `bsl=25` · `ai0=on`.
5. After the run, AI CSVs land in `Terminal\Common\Files\FEMA_AI\` (see [`AI/README.md`](AI/README.md)).

## Repository Layout

```
FEMA/
├── FEMA.mq5              # EA entry point
├── FEMA.mqproj
├── Include/              # Engine + AI0 logger
├── AI/                   # Offline dataset + replay (AI0+)
├── Presets/
│   └── PRODUCTION.set    # Locked production inputs
├── Candidate.md          # Production preset spec
├── Edge Discovery.md     # Phase testing history
├── System Profile EURUSD.md
├── ai_enhance.md         # AI edge-preservation phases
├── roadmap.md            # Build roadmap
└── concept.md            # Strategy concept
```

## Docs

- **[Candidate.md](Candidate.md)** — production inputs, benchmark, load instructions
- **[System Profile EURUSD.md](System Profile EURUSD.md)** — edge / trade / performance profile
- **[ai_enhance.md](ai_enhance.md)** — AI0–AI9 edge preservation plan
- **[AI/README.md](AI/README.md)** — AI0 pipeline usage
- **[Edge Discovery.md](Edge Discovery.md)** — full backtest log and phase verdicts
- **[roadmap.md](roadmap.md)** — implementation phases

## Requirements

- MetaTrader 5
- EURUSD M5
- Hedging or netting account (test your broker mode)

## License

See repository owner for terms.
