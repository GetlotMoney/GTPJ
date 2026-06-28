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

This is a clean confirmation rerun of ATTEMPT-002. The 74-level result is reproduced. Promotion/tag remains blocked because the active v2 comparison reference is unconfirmed: v2 has `best_observed_H=74.29` and `confirmed_H=pending`; ATTEMPT-003 is 0.05 below that unconfirmed reference.
