# TRIAL-002 Trial Result

## Metrics

| Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ATTEMPT-003 | v2 | CUB | 5 | 71.19 | 76.62 | 73.81 | 81.08 | 42 | -0.48 |

## Evidence

```text
trial_id: TRIAL-002
attempt_id: ATTEMPT-003
evidence_level: valid_single_run
result_status: valid_observation
promotion_decision: blocked
confirmed_H: pending
confirmation_status: not_applicable
train_log_artifact_id: log:v2:module_trial:TRIAL-002:attempt-003
best_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-002:attempt-003:best
full_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-002:attempt-003:full
runner_console_artifact_id: receipt:v2:module_trial:TRIAL-002:attempt-003:runner_console
```

## Decision

`not_confirmed`

ATTEMPT-003 is recorded as `valid_single_run` with confirmed_H=pending and confirmation_status=not_applicable. Promotion/tag remains blocked because active v2 comparison reference is unconfirmed: v2 best_observed_H=74.29 (unconfirmed), confirmed_H=pending.
