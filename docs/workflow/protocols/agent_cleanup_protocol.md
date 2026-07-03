# Agent Cleanup Protocol

本协议只解决一个问题：每轮 workflow 或阶段结束后，右侧栏不能堆历史 agent。

## 1. 目标

右侧栏只显示当前阶段仍在工作的 active agents。历史结论必须回到文件和 artifact，不能靠旧窗口保存。

阶段结束时，Coordinator 必须执行：

```text
1. 列出保留名单。
2. 列出关闭名单。
3. 确认关闭名单的输出已经写入 agent_summary / AGENT_ACTIVITY / result / quality / issues / memory。
4. 调用 close_agent 关闭已完成的 temporary agents。
5. 把关闭结果写回 AGENT_ACTIVITY.md 或 closeout summary。
```

## 2. 必须记录的字段

`agent_runtime.yaml` 中每个 temporary agent 至少要能追踪：

```yaml
temporary_subagent_ids:
  runner_monitor: 019...

temporary_subagent_display_names:
  runner_monitor: "ATTEMPT-005 Runner Monitor"

agent_instance_status:
  runner_monitor: completed

agent_output_refs:
  runner_monitor: agent_outputs/runner_monitor.md

agent_cleanup:
  retention_policy: current_stage_active_only
  close_completed_agents_on_stage_end: true
  close_command: multi_agent_v1.close_agent
  close_results_record: AGENT_ACTIVITY.md
```

如果工具返回 `not found`，不能伪造为已关闭，必须记录为：

```text
close_result: not_found
meaning: repo ledger id is no longer reachable by the current agent tool
```

## 3. 关闭判定

```text
running / active / spawned -> 保留
completed / complete / closed -> 关闭
missing / failed / unknown / not_found -> 不盲关，先汇报
```

重复 agent id 不能代表独立角色。一个 agent id 如果同时承担多个正式角色，必须标记为历史限制或降级，不能作为完整 `real_multi_agent` 证据。

## 4. 只读计划命令

阶段结束前先运行：

```bash
python workflow/gtpj_workflow.py agent-cleanup-plan --path <agent_runtime.yaml>
```

它只输出保留/关闭/未知名单，不会关闭 agent。

## 5. Owner 可见汇报格式

```text
role: Coordinator
action: agent cleanup
evidence: agent_runtime.yaml + AGENT_ACTIVITY.md + agent_outputs/
keep: ...
close: ...
unknown: ...
next: close completed agents, then write close_result
```

如果 owner 说右侧栏数量和 cleanup plan 不一致，Coordinator 必须说明：

```text
repo 账本只能识别已记录的 runtime agents；
当前工具若没有 list_agents API，无法权威枚举 UI 中所有历史窗口；
未知 UI agent 需要按显示名人工对照后再关闭。
```
