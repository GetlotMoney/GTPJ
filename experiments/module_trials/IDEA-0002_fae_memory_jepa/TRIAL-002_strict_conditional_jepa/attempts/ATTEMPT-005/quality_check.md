# ATTEMPT-005 Quality Check

```text
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: blocked
```

## Findings

- Metrics parsed from the registered training log: U=71.69, S=76.01, H=73.79, ZS=81.32, best_epoch=43.
- Attempt decision recorded as `not_confirmed`.
- Raw artifacts are registered in Warehouse; GitHub keeps only lightweight identities.

## Artifact Check

- [x] `log:v2:module_trial:TRIAL-002:attempt-005` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-005:best` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-005:full` exists in Warehouse.
- [x] `receipt:v2:module_trial:TRIAL-002:attempt-005:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] Raw logs and checkpoints are not tracked in Git.

## Decision

PASS_REVISE.
