# FEMA RACI — edge changes (GOV-RACI-01)

**Scope:** Candidate create · promote to lock · retire.  
**Charter:** Human-in-the-loop. No auto-promote. No live EMA/TP/SL/lot from AI.

| Decision | Responsible (does) | Accountable (signs) | Consulted | Informed |
| -------- | ------------------ | ------------------- | --------- | -------- |
| **Create candidate** (`fema_ops clone`, new `.set`) | Operator / agent (offline) | Operator | Discovery notes / search_map | STATUS / KB `candidates.csv` |
| **Run / score candidate** (EL1 tester → EL2 gates) | Operator (MT5 Tester) | Operator | `gate_rules.json` | KB run registry |
| **Promote → lock** (EL2 + EL3) | Operator | **Operator only** | Checklist · System Profile | Certificate · STATUS · lineage |
| **Retire / archive lock** (EL8) | Operator | **Operator only** | EL7 trigger / health ladder | Edge Discovery · System Profile |
| **Pause-new flag** (EL6 wire) | Operator | Operator | `pause_policy.md` · `pause-check` | Demo account / Observatory |
| **Open Re-Discovery** (EL7) | Operator | Operator | health persistence · research SOP | Factory / clone queue |

## Hard rules

1. **Promote / retire** — Accountable = human operator. Scripts and agents may draft; they may not sign.
2. **Candidate create** — Allowed offline without a promote. Must cite parent lock + one subsystem (`search_map`).
3. **AI / Ops Plane** — May score, recommend, and archive. May **not** author PRODUCTION or retune live risk.
4. **Demo vs Tester** — Demo health decisions use `--source demo` only; Tester collect is not a promote input.

## Sign-off artifacts

| Gate | Written exit |
| ---- | ------------ |
| EL2 promote/reject | `AI/kb/el2_promote_decision.md` + checklist |
| EL3 lock | `AI/kb/el3_lock_confirm.json` + certificate |
| EL8 retire | Lineage `retired_run_id` + dated archive note |

See also: [`research_loop_sop.md`](research_loop_sop.md) · [`retrain_rediscovery_policy.md`](retrain_rediscovery_policy.md) · [`../templates/promotion_checklist.md`](../templates/promotion_checklist.md).
