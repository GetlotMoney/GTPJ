# TRIAL-002 Trial Result

## Metrics

| Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ATTEMPT-006 | v2 | CUB | 5 | 71.29 | 76.73 | 73.91 | 81.52 | 42 | -0.38 |

## Evidence

```text
trial_id: TRIAL-002
attempt_id: ATTEMPT-006
evidence_level: valid_single_run
result_status: not_confirmed
promotion_decision: blocked
confirmed_H: pending
confirmation_status: needs_confirmation
train_log_artifact_id: log:v2:module_trial:TRIAL-002:attempt-006
best_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-002:attempt-006:best
full_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-002:attempt-006:full
runner_console_artifact_id: receipt:v2:module_trial:TRIAL-002:attempt-006:runner_console
```

## Decision

`not_confirmed`

ATTEMPT-006 is recorded as `valid_single_run` with confirmed_H=pending and confirmation_status=needs_confirmation. Promotion/tag remains blocked because active v2 comparison reference is unconfirmed: v2 best_observed_H=74.29 (unconfirmed), confirmed_H=pending.
