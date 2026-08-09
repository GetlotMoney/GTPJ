# ATTEMPT-011 Task Start Card

subject_id: `ATTEMPT-011`
subject_type: `attempt`
workflow_kind: `dynamic-routing`
runner_scope: `server_detached_mixed200`

Formal runner 当前状态：blocked。

解除 block 的条件：

- `agent_runtime.yaml` 使用 `activation_mode: role_only` 和 `formal_runtime_backend: server_detached_role_only`；
- 三份独立 role outputs 已写入：Runner Monitor / Interface Checker / Evidence Quality Checker；
- `validate-agent-runtime`、`multi-agent-preflight`、`agent-cleanup-plan` 全部通过；
- 服务器预检确认 commit、GPU、同 run id 进程和目标目录无冲突。

禁止事项：

- 不启动右侧临时 agents。
- 不为了 gate 创建任何 named thread 或临时 agents。
- 不在 formal gate 前启动服务器 Runner。
