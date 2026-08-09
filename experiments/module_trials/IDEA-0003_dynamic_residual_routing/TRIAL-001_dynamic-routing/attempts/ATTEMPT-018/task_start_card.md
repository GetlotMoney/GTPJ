# ATTEMPT-018 Task Start Card

subject_id: `ATTEMPT-018`
workflow_mode: `live_multi_agent_monitor`
activation_mode: `real_multi_agent`
agent_instance_mode: `named_owner_thread`
run_id: `RUN-20260709-0002-a017dr095-restore5-live-multiagent-2gpu`
profile: `h76-a017dr095-restore5-exact-repeat`

## 目标

本轮只做 `ATTEMPT-017` best single `DR-095` 的严格 exact repeat 复现。

## 复现边界

- source_candidate_id: `A017DR095`
- source_run_id: `RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu`
- source_job_id: `DR-095`
- source_name: `a015dr035_weight_plus_0.01`
- repeat_type: `exact_repeat`
- original_seed: `5`
- restore_target_H: `75.11`
- max_attempts: `5`
- max_attempts_hard_cap: `true`
- early_stop_on_best_hit: `true`
- near_miss_tolerance_H: `0.2`
- near_miss_not_restored: `true`
- seed_change_allowed: `false`

## 固定配置

- `use_dynamic_routing: true`
- `dynamic_local_mode: fixed`
- `dynamic_icsa_mode: fixed`
- `dynamic_direction_mode: sample`
- `dynamic_pse_mode: fixed`
- `dynamic_gate_hidden: 48`
- `dynamic_gate_anchor_lambda: 0.0035`
- `weight_s2v: 0.535`
- `random_seed: 5`

## 多 Agent 硬门

本轮使用左侧命名 Codex 线程，不走 `server_frozen_runner`。正式 Runner 启动前必须满足：

- `agent_runtime.yaml`
- `validate-agent-runtime`
- `multi-agent-preflight`
- Runner / Interface / Evidence Quality 角色 pre-run `allow`
- helper profile 变更的独立 Reviewer 审核
- 服务器 GPU / screen / run 目录预检
- workflow 验证与 `git diff --check`

## 禁止事项

- 不换 seed
- 不改配置
- 不把 near miss 写成 restored
- 不把本轮 best single 直接写成 promotion evidence
- 不 push、不删远端、不改 tag
