# TRIAL-002 Trial Result

## Metrics

| Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ATTEMPT-002 | v2 | CUB | 5 | 71.32 | 77.40 | 74.24 | 81.62 | 33 | -0.05 |

## Evidence

```text
trial_id: TRIAL-002
attempt_id: ATTEMPT-002
evidence_level: confirmation_grade
result_status: confirmed
promotion_decision: blocked
confirmed_H: 74.24
confirmation_status: confirmed
train_log_artifact_id: log:v2:module_trial:TRIAL-002:attempt-002
best_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-002:attempt-002:best
full_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-002:attempt-002:full
runner_console_artifact_id: receipt:v2:module_trial:TRIAL-002:attempt-002:runner_console
```

## Decision

`keep`

ATTEMPT-002 is recorded as `confirmation_grade` with confirmed_H=74.24 and confirmation_status=confirmed. Promotion/tag remains blocked because active v2 comparison reference is unconfirmed: v2 best_observed_H=74.29 (unconfirmed), confirmed_H=pending.
