# ATTEMPT-017 Task Start Card

subject_id: `ATTEMPT-017`

run_id: `RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu`

本轮目标是在 ATTEMPT-015 的 `h48 + direction_sample + small anchor` 平台期之后，做 100 个服务器冻结实验，探索已经由代码支持但最新热点中未充分验证的动态路由机制。运行模式为 `server_frozen_runner`，因此不创建左侧命名 Codex 线程，也不启动右侧 temporary subagents。

| 字段 | 值 |
|---|---|
| task_type | trial-internal tune_search + narrow_ablation |
| workflow_mode | server_frozen_runner |
| base_version | v5 |
| source_evidence | ATTEMPT-015 result/quality；ATTEMPT-016 只作为运行占用状态参考 |
| profile | h76-escape100-supported-routing |
| jobs | 100 |
| seed | 5 |
| GPUs | 0,1 |
| runner_scope | formal_runner |
| agent_mode | role_only |
| agent_instance_mode | role_only |
| formal_runtime_backend | server_detached_role_only |
| thread_creation_allowed | false |
| owner_monitor_mode | true |
| promotion | blocked |

本轮不做 confirmation。所有 job 都是搜索、机制探针或窄消融；若出现 H>=75，只能记录为 tune single，后续仍需 exact_repeat 复现。
