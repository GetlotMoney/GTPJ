# TRIAL-002 Trial Result

## Metrics

| Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ATTEMPT-004 | v2 | CUB | 5 | 71.22 | 77.60 | 74.27 | 81.38 | 33 | -0.02 |

## Evidence

```text
trial_id: TRIAL-002
attempt_id: ATTEMPT-004
evidence_level: valid_single_run
result_status: needs_confirmation
promotion_decision: blocked
confirmed_H: pending
confirmation_status: needs_confirmation
train_log_artifact_id: log:v2:module_trial:TRIAL-002:attempt-004
best_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-002:attempt-004:best
full_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-002:attempt-004:full
runner_console_artifact_id: receipt:v2:module_trial:TRIAL-002:attempt-004:runner_console
```

## Decision

`keep`

ATTEMPT-004 is recorded as `valid_single_run` with confirmed_H=pending and confirmation_status=needs_confirmation. Promotion/tag remains blocked because active v2 comparison reference is unconfirmed: v2 best_observed_H=74.29 (unconfirmed), confirmed_H=pending.

## Confirmation Gate

ATTEMPT-003 and ATTEMPT-004 were exact same-config reruns of the strict conditional JEPA path. They produced mixed evidence:

| Attempt | H | Decision |
|---|---:|---|
| ATTEMPT-003 | 73.81 | not_confirmed |
| ATTEMPT-004 | 74.27 | keep |

Do not start the planned 10-run tuning sweep from this trial state. The next action must be an owner decision on whether to accept this variance, run a new confirmation strategy, or revise the implementation/training determinism.
