# TRIAL-001 Quality Check

```text
quality_check_mode: STRICT
attempt_id: ATTEMPT-017
latest_repeat_attempt: ATTEMPT-018
decision: PASS_REVISE
decision_scope: current trial after ATTEMPT-018 exact repeat closeout
latest_trial_decision: revise
promotion_decision: blocked
evidence_level: valid_single_run
```

## Findings

- 最高单次来自 `ATTEMPT-017`：U=73.00、S=77.36、H=75.11、ZS=82.12、best_epoch=48。
- `ATTEMPT-018` 已完成 5 次 exact repeat：best H=74.71、mean H=74.58，未达到 restore_target_H=75.11。
- Trial-level decision 记录为 `revise`，confirmation_status 为 `not_restored`。
- Promotion/tag 保持 blocked；H=75.11 只能作为未还原的研究单次。
- Raw artifacts remain in Warehouse; GitHub stores lightweight identities only.

## Artifact Check

- [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:summary-csv` exists in Warehouse.
- [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:summary-jsonl` exists in Warehouse.
- [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:batch-status-json` exists in Warehouse.
- [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:events-jsonl` exists in Warehouse.
- [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:server-status-json` exists in Warehouse.
- [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:plan-json` exists in Warehouse.
- [x] `manifest.yaml`, `result.yaml`, and `result.md` point back to the attempt-local evidence.
- [x] `attempts/ATTEMPT-018/manifest.yaml`、`result.yaml`、`quality_check.md` 记录了最新 exact repeat 非还原结论。
- [x] No raw training log or checkpoint is copied into GitHub.

## Decision

PASS_REVISE；ATTEMPT-017 保留为最高单次来源，ATTEMPT-018 的复现结论为 `not_restored`，当前 trial decision 为 `revise`。
