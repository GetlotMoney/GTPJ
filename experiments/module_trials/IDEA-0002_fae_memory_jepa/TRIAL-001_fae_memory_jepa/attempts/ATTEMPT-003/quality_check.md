# ATTEMPT-003 Quality Check

```text
quality_check_mode: STRICT
decision: PASS_KEEP
promotion_decision: blocked
```

## Findings

- Metrics parsed from the registered training log: U=71.32, S=77.40, H=74.24, ZS=81.62, best_epoch=33.
- Clean confirmation of the 74-level ATTEMPT-002 result passed.
- Promotion remains blocked because H=74.24 is below active v2 H=74.29 by 0.05.
- Attempt decision recorded as `keep`.
- Raw artifacts are registered in Warehouse; GitHub keeps only lightweight identities.

## Artifact Check

- [x] `log:v2:module_trial:TRIAL-001:attempt-003` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-001:attempt-003:best` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-001:attempt-003:full` exists in Warehouse.
- [x] `receipt:v2:module_trial:TRIAL-001:attempt-003:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] Raw logs and checkpoints are not tracked in Git.

## Decision

PASS_KEEP.
