# TRIAL-002 Trial Result

## Metrics

| Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ATTEMPT-008 | v2 | CUB | 42 | 71.22 | 76.64 | 73.83 | 81.62 | 45 | -0.46 |

## Evidence

```text
trial_id: TRIAL-002
attempt_id: ATTEMPT-008
evidence_level: valid_single_run
result_status: not_confirmed
promotion_decision: blocked
confirmed_H: pending
confirmation_status: needs_confirmation
train_log_artifact_id: log:v2:module_trial:TRIAL-002:attempt-008
best_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-002:attempt-008:best
full_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-002:attempt-008:full
runner_console_artifact_id: receipt:v2:module_trial:TRIAL-002:attempt-008:runner_console
```

## Decision

`not_confirmed`

ATTEMPT-008 is recorded as `valid_single_run` with confirmed_H=pending and confirmation_status=needs_confirmation. Promotion/tag remains blocked because active v2 comparison reference is unconfirmed: v2 best_observed_H=74.29 (unconfirmed), confirmed_H=pending.

Seed-42 diagnosis pair: ATTEMPT-007 produced `H=73.94` at epoch 42 and ATTEMPT-008 produced `H=73.83` at epoch 45 from the same pre-run freeze commit and same seed-42 deterministic config. Both remain below the TRIAL-002 best observed `H=74.27`, so the trial is still not confirmed.
