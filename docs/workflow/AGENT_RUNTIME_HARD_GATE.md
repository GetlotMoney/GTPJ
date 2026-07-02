# Agent Runtime Hard Gate

本文件是 GTPJ workflow-v2 的启动闸机。它解决一个具体问题：正式实验不能由
Coordinator 单窗口代办所有角色后直接启动 Runner。

## 1. 核心规则

只要一次任务会启动真实 Runner、登记正式 attempt/result、选择 best、安排 repeat、
影响下一轮高成本实验或进入 promotion 判断，就必须先通过 agent runtime hard gate。

```text
没有真实右侧临时 agents -> 不准启动正式 Runner。
没有独立 agent 输出 -> 不准 apply advance transition。
没有 pre-run allow/check -> 不准冻结并启动服务器 batch。
```

状态机只记录证据迁移，不能替代 agents。Runner 只执行训练，也不能替代 workflow。

## 2. 必需启动顺序

正式实验必须按这个顺序执行：

```text
1. Coordinator 生成 task start card。
2. Coordinator 检查真实 multi-agent 工具是否可用。
3. Coordinator 启动右侧临时 agents，并记录 agent_instance_id。
4. Planner / Interface / Quality / Runner Monitor 等角色独立输出 allow/block/propose。
5. Coordinator 写 agent_runtime.yaml。
6. 运行 validate-agent-runtime，通过后才允许 pre-run freeze。
7. Coordinator apply evidence transition。
8. Runner 生成 frozen batch 并启动服务器。
9. Log / Quality / Result agents 分别审查运行证据。
10. Coordinator 写 result、quality、agent_summary 和下一条 transition。
```

如果第 3 步没有发生，本轮只能降级为 debug/smoke 或候选线索，不能作为正式 evidence。

## 3. Runtime Gate 文件

每个正式 runner start 前必须有一个轻量文件：

```text
agent_runtime.yaml
```

推荐位置：

```text
attempts/ATTEMPT-xxx/agent_runtime.yaml
experiments/campaigns/CAMP-xxx/agent_runtime.yaml
```

最小字段：

```yaml
schema_version: gtpj.agent_runtime_gate.v0
subject_id: ATTEMPT-xxx
subject_type: attempt
formal_evidence: true
activation_mode: real_multi_agent
agent_instance_mode: temporary_subagent
lifecycle: workflow_scoped
ui_visibility: right_sidebar_temporary_agents
tool_support_real_multi_agent_available: true
spawn_tool: multi_agent_v1.spawn_agent
single_agent_execution: false
runner_start_allowed: true

temporary_subagent_ids:
  runner_monitor: 019...
  interface_checker: 019...
  evidence_quality_checker: 019...
  result_analyst: 019...

pre_run_required_checks:
  runner_monitor: allow
  interface_checker: allow
  evidence_quality_checker: allow

authority_refs:
  task_start_card: task_start_card.md
  agent_summary: agent_summary.md
  quality_check: quality_check.md
  transitions: TRANSITIONS.jsonl
```

`temporary_subagent_ids` 不能写成 `temporary_subagent`、`not_recorded`、`role_only`、
`current Codex session` 这类占位文本。必须记录真实实例 id、可见 thread id 或明确的
subagent id。

## 4. allow / block 语义

`pre_run_required_checks` 只允许：

```text
allow
pass
block
warn
not_checked
```

Runner start 之前，所有 pre-run 必需角色必须是 `allow` 或 `pass`。任一 `block`、
`not_checked` 或缺失，都必须阻断正式 run。

最低必需角色族：

```text
Runner Monitor
Evidence Quality Checker / Quality Checker
Interface Checker（涉及代码、配置、GZSL、评估语义或新模块时必需）
```

Log Analyst 和 Result Analyst 可以在 run 后进入，但如果它们的结论影响 best、repeat、
promotion 或下一轮实验，也必须是独立 agent 输出。

## 5. 降级规则

如果真实右侧临时 agents 不可用，或者 owner 明确只要 debug/smoke，必须写：

```yaml
formal_evidence: false
evidence_level: debug_smoke
activation_mode: role_only
agent_instance_mode: role_only
runner_start_allowed: true
eligible_for_keep_best_promotion_confirmation: false
```

这种运行只能定位环境、脚本、shape 或速度问题，不能进入 keep / best / confirmation /
promotion 证据。

## 6. Helper

正式 runner start 前必须运行：

```bash
python workflow/gtpj_workflow.py validate-agent-runtime --path <agent_runtime.yaml>
```

动态路由 batch 生成命令必须传入通过校验的 gate：

```bash
python workflow/gtpj_workflow.py plan-dynamic-routing-batch \
  --agent-runtime-gate <agent_runtime.yaml> \
  ...
```

只有显式 `--debug-smoke` 时可以不传 gate；该 run 自动标为非正式证据。

## 7. 证据等级

| 情况 | 证据等级 |
|---|---|
| 右侧临时 agents 已启动，gate 通过，Runner 按 frozen config 执行 | formal evidence |
| Coordinator 单窗口代办所有角色后启动 Runner | candidate/debug evidence only |
| 服务器离线训练但没有 pre-run agent gate | runner evidence only，不是 workflow evidence |
| 事后补写 agent_summary，但没有原始 agent id 和 allow/check | audit note only |

一句话：状态机是账本，Runner 是执行器，agents 是工作流主体。三者缺一，不能声称完整
workflow-v2 闭环。
