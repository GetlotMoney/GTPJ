# TRIAL-002 Quality Check

```text
quality_check_mode: STRICT
attempt_id: ATTEMPT-004
decision: PASS_OWNER_ACCEPTED_STOCHASTIC_TAG
promotion_decision: owner_accepted_stochastic_tag
baseline_grade_promotion_decision: blocked
evidence_level: valid_single_run
```

## Findings

- Metrics are anchored to best observed `ATTEMPT-004`: U=71.22, S=77.60, H=74.27, ZS=81.38, best_epoch=33.
- Clean seed-42 variance evidence is retained from ATTEMPT-009/010: H=74.14 and H=74.01.
- Trial-level decision recorded as `owner_accepted_to_v3`.
- Attempt confirmation status remains: confirmed_H=pending, confirmation_status=needs_confirmation.
- Owner accepted stochastic variance for formal `GTPJ-v3` tag on 2026-06-28.
- Baseline-grade claims remain blocked until future confirmation/multi-seed evidence upgrades the record.
- Raw artifacts remain in Warehouse; GitHub stores lightweight identities only.

## Artifact Check

- [x] `log:v2:module_trial:TRIAL-002:attempt-004` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-004:best` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-004:full` exists in Warehouse.
- [x] `receipt:v2:module_trial:TRIAL-002:attempt-004:runner_console` exists in Warehouse.
- [x] `manifest.yaml`, `result.yaml`, and `result.md` point back to the attempt-local evidence.
- [x] No raw training log or checkpoint is copied into GitHub.

## Decision

PASS_OWNER_ACCEPTED_STOCHASTIC_TAG.
