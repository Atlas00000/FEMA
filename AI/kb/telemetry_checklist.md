# Telemetry checklist (RG-DATA-01)

Prefer **derive offline** from existing `fema_baskets_v2` / events. Add EA columns only if derive is impossible.

| Need | Have (column / artifact) | Derive | Missing / next |
| ---- | ------------------------ | ------ | -------------- |
| Regime label | `adx`, gate fingerprint | `adx_lt_30_share`, bins | Named regime enum (optional) |
| Feature distributions | atr, ema_*, depth, hour, dow | Market Fingerprint v0 | — |
| Exec quality | `spread_points`; events `retcode` / `reject_class` | reject_rate (health) | Richer fill latency (park) |
| Basket lifecycle | open/close, exit_reason, depth, bars | health windows | — |
| Failure reason | KB `failure_reason` on candidates | — | Join FP to every experiment (Wave 4 `RG-KB-02`) |
| Env metadata | `run.meta` · `run_config.json` · sync heartbeat | source=demo\|tester | Broker/server clock skew |
| Market Fingerprint | — | `fema_ops fingerprint` | Postgres blob optional (Wave 5) |
| Edge Genome | — | `kb/genome_PRODUCTION.json` | Multi-preset genomes later |
| Pause trust (EL5) | health persistence | — | **Blocked until Wave 0 demo unlock + ≥2 weeks** |

**Rule:** no new EA fields for Wave 3.
