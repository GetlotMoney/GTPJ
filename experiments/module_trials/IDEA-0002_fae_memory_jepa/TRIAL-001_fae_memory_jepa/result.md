# TRIAL-001 Trial Result

## Metrics

| Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ATTEMPT-003 | v2 | CUB | 5 | 71.32 | 77.40 | 74.24 | 81.62 | 33 | -0.05 |

## Evidence

```text
trial_id: TRIAL-001
attempt_id: ATTEMPT-003
evidence_level: confirmation_grade
result_status: confirmed
promotion_decision: blocked
confirmed_H: 74.24
confirmation_status: confirmed
train_log_artifact_id: log:v2:module_trial:TRIAL-001:attempt-003
best_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-001:attempt-003:best
full_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-001:attempt-003:full
runner_console_artifact_id: receipt:v2:module_trial:TRIAL-001:attempt-003:runner_console
```

## Decision

`keep`

ATTEMPT-003 is recorded as `confirmation_grade` with confirmed_H=74.24 and confirmation_status=confirmed. Promotion/tag remains blocked because active v2 comparison reference is unconfirmed: v2 best_observed_H=74.29 (unconfirmed), confirmed_H=pending.
