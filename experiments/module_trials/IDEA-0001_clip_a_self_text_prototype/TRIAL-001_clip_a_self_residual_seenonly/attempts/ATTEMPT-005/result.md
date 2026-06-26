# ATTEMPT-005 Result

## Metrics

| Dataset | Seed | U | S | H | ZS | Best epoch |
|---|---:|---:|---:|---:|---:|---:|
| CUB | 5 | 74.62 | 70.85 | 72.69 | 81.18 | 49 |

## Baseline Comparison

| Baseline | H | Attempt H | Delta H |
|---|---:|---:|---:|
| GTPJ-v1 authoritative baseline | 73.93 | 72.69 | -1.24 |
| CONFIRM-001 same-day confirmation | 73.77 | 72.69 | -1.08 |

## Evidence

```text
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-005
best_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-005:best
full_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-005:full
runner_console_artifact_id: receipt:v1:module_trial:TRIAL-001:attempt-005:runner_console
```

## Decision

`reject`

Valid evidence, but this setting underperformed the current best ATTEMPT-003. H=72.69 vs baseline 73.93 (-1.24).
