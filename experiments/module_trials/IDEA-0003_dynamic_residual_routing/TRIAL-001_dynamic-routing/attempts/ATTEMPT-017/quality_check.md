# ATTEMPT-017 Quality Check

## Pre-Run

- [x] 运行模式为 `server_frozen_runner`。
- [x] 训练运行期不创建左侧命名线程，不启动右侧 temporary subagents。
- [x] 使用 `role_only + server_detached_role_only` gate。
- [x] profile 只使用现有代码支持的配置开关。
- [x] 禁止 `dynamic_pse_mode=sample`。
- [x] ATTEMPT-016 仍在运行时，ATTEMPT-017 排队等待，不抢占 GPU。

## Post-Run

- [x] 服务器 `batch_status.status=completed`。
- [x] 100/100 completed，0 failed，0 skipped。
- [x] `screen -ls` 无会话，符合 supervisor 完成后退出。
- [x] GPU0/GPU1 空闲。
- [x] 本地同步的 `batch_status.json`、`summary.csv`、`summary.jsonl`、`events.jsonl`、`ATTEMPT017_SERVER_STATUS.json` 与服务器 SHA256 一致。
- [x] `monitor-workflow --report-new-completions` 已写入 `AGENT_ACTIVITY.md`。
- [x] `closeout-workflow` 已执行，状态写为 `closed_out`；helper 明确提示它不替代正式 result/sync。

## 结果边界

ATTEMPT-017 不产生 confirmation evidence。`DR-095` 是 H=75.11 的 best single，只能作为 `valid_single_run` / `tune_promising` 候选。

正式复现必须使用：

- repeat_type: `exact_repeat`
- original_seed: `5`
- restore_target_H: `75.11`
- max_attempts: `5`
- early_stop_on_best_hit: `true`

未达到 `restore_target_H=75.11` 的接近结果只能标记为 `near_miss_not_restored`，不能写成 confirmed 或 restored。

## Decision

- evidence_level: `valid_single_run`
- confirmation_decision: `not_confirmation_evidence`
- promotion_decision: `blocked`
- next_action: 为 `A017DR095 / DR-095` 生成最多 5 次 exact repeat。
