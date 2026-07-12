# Research-loop SOP (RG-RES-01)

Permanent loop for keeping the edge alive. Same spine as EL5 → EL7 → EL1 → EL2 → EL3 / EL8 — written as an SOP.

```text
drift → explain → hypothesize → candidate → validate → promote|reject → archive
```

| Step | Do | Artifact | EL |
| ---- | -- | -------- | -- |
| **1. Detect drift** | Compare rolling health / components vs birth bands; note sync source | `health_latest.json` · Observatory | EL5 |
| **2. Explain** | Tag causes (regime, session, depth, exec…); rule out Tester-as-demo | Observatory notes · drift_tags | EL5 |
| **3. Hypothesize** | One subsystem from [`search_map.md`](search_map.md); cite why | Ticket / STATUS open ESR | EL7 start |
| **4. Candidate** | `fema_ops clone` from parent lock; ≤3 candidates first | New `.set` · `candidates.csv` | EL7 → factory |
| **5. Validate** | Same window/symbol as lock; apply [`gate_rules.json`](gate_rules.json) | run_id · scorecard | EL1 / EL2 |
| **6. Promote or reject** | Human sign-off only ([`raci.md`](raci.md)) | promote decision · checklist | EL2 / EL3 |
| **7. Archive** | Keep fail rows; update lineage parent/child / `retired_run_id` | [`lineage.json`](lineage.json) · KB runs | EL8 |

## Rules

- Watch may **trigger**; it may not **author** the new preset.
- Prefer demo-path health for live decisions; Tester is Discovery only.
- One active lock; history intact.
- RACI: promote/retire = operator accountable.

## Policy links

- Triggers / cadence: [`retrain_rediscovery_policy.md`](retrain_rediscovery_policy.md)
- Pause: [`pause_policy.md`](pause_policy.md)
- Spine: [`../../edgelifecycle.md`](../../edgelifecycle.md) § EL7
