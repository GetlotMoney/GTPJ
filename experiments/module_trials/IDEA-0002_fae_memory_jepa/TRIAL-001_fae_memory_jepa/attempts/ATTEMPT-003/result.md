# ATTEMPT-003 Result

## Metrics

| Attempt ID | Dataset | Seed | U | S | H | ZS | Best epoch |
|---|---|---:|---:|---:|---:|---:|---:|
| ATTEMPT-003 | CUB | 5 | 71.32 | 77.40 | 74.24 | 81.62 | 33 |

## Evidence

```text
trial_id: TRIAL-001
train_log_artifact_id: log:v2:module_trial:TRIAL-001:attempt-003
best_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-001:attempt-003:best
full_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-001:attempt-003:full
runner_console_artifact_id: receipt:v2:module_trial:TRIAL-001:attempt-003:runner_console
```

## Decision

`keep`

This is a clean confirmation rerun of ATTEMPT-002. The 74-level result is reproduced, but promotion remains blocked because H=74.24 is below active v2 H=74.29.
