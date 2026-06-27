# TRIAL-001 Result

## Current Formal Best

| Attempt ID | Dataset | Seed | U | S | H | ZS | Best epoch |
|---|---|---:|---:|---:|---:|---:|---:|
| ATTEMPT-019 | CUB | 5 | 71.32 | 77.52 | 74.29 | 81.59 | 33 |

## Baseline Comparison

| Baseline | H | Trial H | Delta H |
|---|---:|---:|---:|
| GTPJ-v1 authoritative baseline | 73.93 | 74.29 | +0.36 |
| CONFIRM-001 same-day confirmation | 73.77 | 74.29 | +0.52 |

## Sweep Context

The completed 009-020 sweep found a local peak around `outer=0.15`.
`ATTEMPT-019` (`inner=0.35`, `outer=0.15`, `dropout=0.5`, `heads=4`) is the current best.

The result is seen-heavy:

```text
U = 71.32
S = 77.52
S - U = 6.20
```

## Evidence

```text
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-019
best_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-019:best
full_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-019:full
runner_console_artifact_id: receipt:v1:module_trial:TRIAL-001:attempt-019:runner_console
best_attempt_tag: trial/v1/idea-0001/trial-001-attempt-019-best-h7429
```

## Decision

`revise`

`ATTEMPT-019` is now the formal best recorded experiment for TRIAL-001, but it is not a promotion
result yet. The next promotion-grade step would be a clean confirmation rerun of this exact config.
