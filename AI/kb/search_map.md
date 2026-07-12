# Localized search map (INF-PRESET / containment §6)

**Machine:** [`search_map.json`](search_map.json) · **Playbook:** [`clone_playbook.md`](clone_playbook.md)

**Rule:** One subsystem per candidate. Only adapt the pair that matches observed drift.

## May adapt together

| Subsystem id | Pair | Typical keys |
| ------------ | ---- | ------------ |
| `ema` | EMA20 ↔ EMA Trend | `InpEmaFastPeriod`, `InpEmaTrendPeriod` |
| `atr` | ATR Period ↔ Multiplier | `InpAtrPeriod`, `InpAtrMultiplier` |
| `grid` | Spacing ↔ Levels | `InpGridLevels`, `InpMaxEntryDepth` |
| `basket_exit` | Basket TP ↔ SL | `InpBasketTp`, `InpBasketSl`, trail/RTE |
| `adx` | ADX ↔ EMA slope/sep | `InpUseAdxGate`, `InpAdxMax`, slope gates |
| `cooldown` | Cooldown ↔ Max trades | `InpCooldownBars`, `InpMaxOpenTrades` |
| `session` | Session blocks | `InpUseSessionBlock*` |
| `htf` | HTF filter | `InpUseHtfFilter`, HTF EMA |
| `regime_extra` | ATR% / breakout | percentile + breakout suspend |
| `entry_filter` | Candle / RSI | confirm + RSI exhaustion |

## Frozen (do not “search”)

- Lot sizing philosophy · risk model · basket management philosophy  
- Market-order execution · strategy type (pullback continuation)  
- Position sizing framework · state machine · execution architecture  

Clone may still copy frozen keys unchanged from PRODUCTION — never treat them as the experiment axis.
