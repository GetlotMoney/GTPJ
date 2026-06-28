# TRIAL-002 Trial Result

## Metrics

| Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ATTEMPT-005 | v2 | CUB | 5 | 71.69 | 76.01 | 73.79 | 81.32 | 43 | -0.50 |

## Evidence

```text
trial_id: TRIAL-002
attempt_id: ATTEMPT-005
evidence_level: valid_single_run
result_status: not_confirmed
promotion_decision: blocked
confirmed_H: pending
confirmation_status: needs_confirmation
train_log_artifact_id: log:v2:module_trial:TRIAL-002:attempt-005
best_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-002:attempt-005:best
full_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-002:attempt-005:full
runner_console_artifact_id: receipt:v2:module_trial:TRIAL-002:attempt-005:runner_console
```

## Decision

`not_confirmed`

ATTEMPT-005 is recorded as `valid_single_run` with confirmed_H=pending and confirmation_status=needs_confirmation. Promotion/tag remains blocked because active v2 comparison reference is unconfirmed: v2 best_observed_H=74.29 (unconfirmed), confirmed_H=pending.
