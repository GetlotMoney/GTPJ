# TRIAL-001 Trial Result

## Metrics

| Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ATTEMPT-001 | v2 | CUB | 5 | 70.32 | 77.68 | 73.82 | 81.39 | 34 | -0.47 |

## Evidence

```text
trial_id: TRIAL-001
attempt_id: ATTEMPT-001
evidence_level: valid_single_run
result_status: valid_observation
promotion_decision: not_applicable
confirmed_H: pending
confirmation_status: not_applicable
train_log_artifact_id: log:v2:module_trial:TRIAL-001:attempt-001
best_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-001:attempt-001:best
full_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-001:attempt-001:full
runner_console_artifact_id: receipt:v2:module_trial:TRIAL-001:attempt-001:runner_console
```

## Decision

`revise`

ATTEMPT-001 is recorded as `valid_single_run` with confirmed_H=pending and confirmation_status=not_applicable. Promotion/tag remains blocked because active v2 comparison reference is unconfirmed: v2 best_observed_H=74.29 (unconfirmed), confirmed_H=pending.
