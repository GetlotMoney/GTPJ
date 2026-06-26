# TRIAL-001 Result

## Metrics

| Attempt ID | Dataset | Seed | U | S | H | ZS | Best epoch |
|---|---|---:|---:|---:|---:|---:|---:|
| ATTEMPT-003 | CUB | 5 | 71.76 | 76.97 | 74.27 | 81.72 | 33 |
| ATTEMPT-007 | CUB | 5 | 70.82 | 76.80 | 73.69 | 80.91 | 33 |

## Baseline Comparison

| Baseline | H | Trial H | Delta H |
|---|---:|---:|---:|
| GTPJ-v1 authoritative baseline | 73.93 | 74.27 | +0.34 |
| CONFIRM-001 same-day confirmation | 73.77 | 74.27 | +0.50 |

## Clean Confirmation

| Target | Target H | Confirmation | Confirmation H | Delta H |
|---|---:|---|---:|---:|
| ATTEMPT-003 | 74.27 | ATTEMPT-007 | 73.69 | -0.58 |

## Evidence

```text
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-003
best_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-003:best
full_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-003:full
runner_console_artifact_id: receipt:v1:module_trial:TRIAL-001:attempt-003:runner_console
confirmation_log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-007
```

## Decision

`revise`

ATTEMPT-003 is still the highest observed parameter setting for TRIAL-001, but ATTEMPT-007 clean confirmation did not reproduce it. ATTEMPT-007 reached H=73.69, which is below both ATTEMPT-003 and the authoritative `v1` baseline. The next action is analysis or a new stabilization hypothesis, not promotion.
