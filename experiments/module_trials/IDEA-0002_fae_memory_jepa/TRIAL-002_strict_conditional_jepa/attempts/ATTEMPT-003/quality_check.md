# ATTEMPT-003 Quality Check

```text
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: blocked
```

## Findings

- Metrics parsed from the registered training log: U=71.19, S=76.62, H=73.81, ZS=81.08, best_epoch=42.
- Attempt decision recorded as `not_confirmed`.
- Raw artifacts are registered in Warehouse; GitHub keeps only lightweight identities.

## Artifact Check

- [x] `log:v2:module_trial:TRIAL-002:attempt-003` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-003:best` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-003:full` exists in Warehouse.
- [x] `receipt:v2:module_trial:TRIAL-002:attempt-003:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] Raw logs and checkpoints are not tracked in Git.

## Decision

PASS_REVISE.
