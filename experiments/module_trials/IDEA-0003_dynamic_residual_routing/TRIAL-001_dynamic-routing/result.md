# TRIAL-001 Trial Result

## Metrics

| Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ATTEMPT-017 | v5 | CUB | 5 | 73.00 | 77.36 | 75.11 | 82.12 | 48 | +0.57 |

## Evidence

```text
trial_id: TRIAL-001
attempt_id: ATTEMPT-017
attempt_role: selected_best_single
current_trial_state_source: ATTEMPT-018
evidence_level: valid_single_run
result_status: revise
promotion_decision: blocked
confirmed_H: pending
confirmation_status: not_restored
latest_exact_repeat_attempt: ATTEMPT-018
latest_confirmation_status: not_restored
latest_trial_decision: revise
server_summary_csv_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:summary-csv
server_summary_jsonl_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:summary-jsonl
server_batch_status_json_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:batch-status-json
server_events_jsonl_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:events-jsonl
server_status_json_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:server-status-json
server_plan_json_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:plan-json
```

## Decision

`revise`

ATTEMPT-017 保留为 `valid_single_run` 最高单次来源；ATTEMPT-018 已完成 hard cap 内的 5 次 exact repeat，因此 trial 当前状态为 `revise/not_restored`，promotion/tag 继续 blocked。ATTEMPT-017 当时的 `rerun/needs_confirmation` 历史 decision 保留在 attempt-local 文件中。

## 最新 exact repeat 结论

ATTEMPT-018 对 ATTEMPT-017 `DR-095 / H=75.11` 完成 5 次同配置、同 seed exact repeat：`74.71/74.62/74.51/74.60/74.45`，最好 `74.71`、均值 `74.58`。没有一次达到 `restore_target_H=75.11`，且最好结果低于 near-miss 阈值 `74.91`。

因此 `H=75.11` 继续作为当前 `best_observed_H` 单次记录保留，但状态是 `not_restored`；它不能更新 `confirmed_H`，也不能触发 promotion。
