# ATTEMPT-002 Result

## Metrics

| Dataset | Seed | U | S | H | ZS | Best epoch |
|---|---:|---:|---:|---:|---:|---:|
| CUB | 5 | 71.22 | 76.98 | 73.99 | 81.25 | 33 |

## Baseline Comparison

| Baseline | H | Attempt H | Delta H |
|---|---:|---:|---:|
| GTPJ-v1 authoritative baseline | 73.93 | 73.99 | +0.06 |
| CONFIRM-001 same-day confirmation | 73.77 | 73.99 | +0.22 |

## Evidence

```text
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-002
best_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-002:best
full_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-002:full
runner_console_artifact_id: receipt:v1:module_trial:TRIAL-001:attempt-002:runner_console
```

## Decision

`keep`

Valid evidence. H=73.99 is above or near the authoritative v1 baseline by +0.06, but this attempt is not the current best setting.
