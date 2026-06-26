# ATTEMPT-007 Result

## Metrics

| Dataset | Seed | U | S | H | ZS | Best epoch |
|---|---:|---:|---:|---:|---:|---:|
| CUB | 5 | 70.82 | 76.80 | 73.69 | 80.91 | 33 |

## Confirmation Target

| Target | Target H | Confirmation H | Delta H |
|---|---:|---:|---:|
| ATTEMPT-003 | 74.27 | 73.69 | -0.58 |

## Baseline Comparison

| Baseline | H | Attempt H | Delta H |
|---|---:|---:|---:|
| GTPJ-v1 authoritative baseline | 73.93 | 73.69 | -0.24 |
| CONFIRM-001 same-day confirmation | 73.77 | 73.69 | -0.08 |

## Evidence

```text
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-007
best_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-007:best
full_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-007:full
runner_console_artifact_id: receipt:v1:module_trial:TRIAL-001:attempt-007:runner_console
pre_run_freeze_commit: 2820b17c222bd2084292d5249d429dce95d1e060
```

## Decision

`not_confirmed`

This was a clean confirmation run of the ATTEMPT-003 config. It did not reproduce the ATTEMPT-003 high point: H=73.69 is 0.58 below ATTEMPT-003 and 0.24 below the authoritative v1 baseline. TRIAL-001 remains `revise`, and promotion remains blocked.
