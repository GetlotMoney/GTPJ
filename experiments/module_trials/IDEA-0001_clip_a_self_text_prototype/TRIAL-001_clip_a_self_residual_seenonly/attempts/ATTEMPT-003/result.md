# ATTEMPT-003 Result

## Metrics

| Dataset | Seed | U | S | H | ZS | Best epoch |
|---|---:|---:|---:|---:|---:|---:|
| CUB | 5 | 71.76 | 76.97 | 74.27 | 81.72 | 33 |

## Baseline Comparison

| Baseline | H | Attempt H | Delta H |
|---|---:|---:|---:|
| GTPJ-v1 authoritative baseline | 73.93 | 74.27 | +0.34 |
| CONFIRM-001 same-day confirmation | 73.77 | 74.27 | +0.50 |

## Evidence

```text
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-003
best_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-003:best
full_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-003:full
runner_console_artifact_id: receipt:v1:module_trial:TRIAL-001:attempt-003:runner_console
```

## Decision

`best`

Current best attempt. H=74.27 exceeds the authoritative v1 baseline by +0.34, but promotion is still blocked pending a clean confirmation run.
