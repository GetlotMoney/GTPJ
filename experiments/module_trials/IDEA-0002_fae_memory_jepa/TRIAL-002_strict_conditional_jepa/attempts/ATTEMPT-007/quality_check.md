# ATTEMPT-007 Quality Check

```text
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: blocked
```

## Findings

- Metrics parsed from the registered training log: U=71.32, S=76.76, H=73.94, ZS=81.25, best_epoch=42.
- Attempt decision recorded as `not_confirmed`.
- Raw artifacts are registered in Warehouse; GitHub keeps only lightweight identities.

## Artifact Check

- [x] `log:v2:module_trial:TRIAL-002:attempt-007` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-007:best` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-007:full` exists in Warehouse.
- [x] `receipt:v2:module_trial:TRIAL-002:attempt-007:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] Raw logs and checkpoints are not tracked in Git.

## Decision

PASS_REVISE.
