# ATTEMPT-006 Result

## Metrics

| Dataset | Seed | U | S | H | ZS | Best epoch |
|---|---:|---:|---:|---:|---:|---:|
| CUB | 5 | 70.85 | 77.36 | 73.96 | 81.46 | 33 |

## Baseline Comparison

| Baseline | H | Attempt H | Delta H |
|---|---:|---:|---:|
| GTPJ-v1 authoritative baseline | 73.93 | 73.96 | +0.03 |
| CONFIRM-001 same-day confirmation | 73.77 | 73.96 | +0.19 |

## Evidence

```text
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-006
best_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-006:best
full_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-006:full
runner_console_artifact_id: receipt:v1:module_trial:TRIAL-001:attempt-006:runner_console
```

## Decision

`keep`

Valid evidence. H=73.96 is above or near the authoritative v1 baseline by +0.03, but this attempt is not the current best setting.
