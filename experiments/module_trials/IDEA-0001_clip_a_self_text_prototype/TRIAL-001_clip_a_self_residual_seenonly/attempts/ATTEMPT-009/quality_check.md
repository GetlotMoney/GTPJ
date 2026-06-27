# ATTEMPT-009 Quality Check

```text
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: blocked
```

## Findings

- Metrics parsed from the registered training log: U=70.83, S=77.03, H=73.80, ZS=81.22, best_epoch=42.
- Attempt decision recorded as `not_confirmed`.
- Raw artifacts are registered in Warehouse; GitHub keeps only lightweight identities.

## Artifact Check

- [x] `log:v1:module_trial:TRIAL-001:attempt-009` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-009:best` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-009:full` exists in Warehouse.
- [x] `receipt:v1:module_trial:TRIAL-001:attempt-009:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] Raw logs and checkpoints are not tracked in Git.

## Decision

PASS_REVISE.
