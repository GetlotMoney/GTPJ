# TRIAL ATTEMPTS

This file records multiple parameter tries, narrow follow-up ablations, reruns, or debug-fix reruns inside one `TRIAL-xxx`.
It is not the formal baseline `tune/INDEX.md`, and it does not replace the trial root decision files.

## Attempts

| Attempt ID | Type | Parameter / Change | Old | New | Seed | U | S | H | ZS | Best epoch | Log artifact | Decision | Directory |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| ATTEMPT-001 | param_tune | `clip_a_self_outer_ratio` | 0.20 | 0.10 | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | `log:...` | keep | `attempts/ATTEMPT-001/` |

## Type Rules

```text
param_tune       # only numeric or existing config values changed
ablation         # a local diagnostic ablation within the same trial
rerun            # same config rerun for confirmation or failure recovery
anchor_followup  # a narrow follow-up around drift/anchoring risk
debug_fix        # rerun after fixing environment or runner issues only
```

## Notes

- `ATTEMPT-xxx` must be append-only. Do not overwrite old attempts.
- Each attempt should have its own `config.yaml`, `manifest.yaml`, `result.yaml`, `quality_check.md`, and `result.md`.
- The trial root `README.md` should point to the current decision-driving `best_attempt_id`.
- If the change is no longer a narrow attempt and becomes a new implementation hypothesis, open `TRIAL-002` instead of extending this table.
