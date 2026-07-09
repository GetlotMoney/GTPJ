# ATTEMPT-013 启动卡

## 结论

可以开始本地 `live_multi_agent_monitor` 规划阶段。当前只规划 50 轮实验，不启动服务器 Runner，不上传 batch，不写 completed 结果。

## 路由

- workflow_mode: `live_multi_agent_monitor`
- activation_mode: `real_multi_agent`
- agent_instance_mode: `named_owner_thread`
- lifecycle: `workflow_scoped`
- task_type: trial-internal confirmation / tune follow-up planning
- base_version: `v5`
- base_code_tag: `v5`
- subject_id: `ATTEMPT-013`
- run_id: `RUN-20260707-0001-h76-followup50-live-multiagent-2gpu`

## 背景

`ATTEMPT-011` 完成 200 jobs，显示 `direction_sample h48` 和小 anchor 区间仍是主要热点。
`ATTEMPT-012` 被 owner 停止，只有 6 completed / 44 skipped，因此不能作为完整确认或 promotion 证据。

## 本轮目标

计划 50 jobs：5 个候选各 seeds 6-15，共 10 次多 seed repeat。目标是给后续正式 runner 提供冻结清单和多 agent gate 证据。

## 当前边界

- 服务器 Runner: not started
- 远端上传: not started
- promotion: blocked
- ATTEMPT-012 partial: weak prior only
