# TRIAL-001 Result

## Metrics

| Attempt ID | Dataset | Seed | U | S | H | ZS | Best epoch |
|---|---|---:|---:|---:|---:|---:|---:|
| ATTEMPT-003 | CUB | 5 | 71.76 | 76.97 | 74.27 | 81.72 | 33 |

## Baseline Comparison

| Baseline | H | Trial H | Delta H |
|---|---:|---:|---:|
| GTPJ-v1 authoritative baseline | 73.93 | 74.27 | +0.34 |
| CONFIRM-001 same-day confirmation | 73.77 | 74.27 | +0.50 |

## Evidence

```text
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-003
best_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-003:best
full_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-003:full
runner_console_artifact_id: receipt:v1:module_trial:TRIAL-001:attempt-003:runner_console
```

## Decision

`revise`

ATTEMPT-003 is the current best parameter setting for TRIAL-001. It beats the authoritative `v1` baseline by `+0.34` H, but the sweep should still be treated as trial-local evidence rather than a promotion-ready result. The next action is a clean confirmation run that uses the ATTEMPT-003 config with no additional local edits.
