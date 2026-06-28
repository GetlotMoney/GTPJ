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
promotion_decision: owner_accepted_stochastic_tag
baseline_grade_promotion_decision: blocked
promote_to: v3
confirmed_H: pending
confirmation_status: needs_confirmation
train_log_artifact_id: log:v2:module_trial:TRIAL-002:attempt-004
best_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-002:attempt-004:best
full_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-002:attempt-004:full
runner_console_artifact_id: receipt:v2:module_trial:TRIAL-002:attempt-004:runner_console
```

## Decision

`owner_accepted_to_v3`

ATTEMPT-004 is the best observed strict conditional FAE-memory JEPA result (`H=74.27`). The owner accepted mixed reruns as stochastic variance and requested formal `GTPJ-v3` tagging on 2026-06-28. This keeps `confirmed_H=pending`; baseline-grade claims remain blocked until future confirmation/multi-seed evidence upgrades the record.
