# ATTEMPT-004 Result

## Metrics

| Dataset | Seed | U | S | H | ZS | Best epoch |
|---|---:|---:|---:|---:|---:|---:|
| CUB | 5 | 72.70 | 74.48 | 73.58 | 80.98 | 44 |

## Baseline Comparison

| Baseline | H | Attempt H | Delta H |
|---|---:|---:|---:|
| GTPJ-v1 authoritative baseline | 73.93 | 73.58 | -0.35 |
| CONFIRM-001 same-day confirmation | 73.77 | 73.58 | -0.19 |

## Evidence

```text
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-004
best_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-004:best
full_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-004:full
runner_console_artifact_id: receipt:v1:module_trial:TRIAL-001:attempt-004:runner_console
```

## Decision

`reject`

Valid evidence, but this setting underperformed the current best ATTEMPT-003. H=73.58 vs baseline 73.93 (-0.35).
