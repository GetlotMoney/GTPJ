# Agent Runtime Hard Gate

本文件是 GTPJ workflow-v2 的正式 Runner 启动闸机。它解决一个具体问题：正式实验不能由 Coordinator 单窗口代办所有角色，也不能再依赖旧 UI 临时 agent 面板。

## 1. 核心规则

只要一次任务会启动真实 Runner、登记正式 attempt/result、选择 best、安排 repeat、影响下一轮高成本实验或进入 promotion 判断，就必须先通过 agent runtime hard gate。

```text
没有左侧命名 Codex 线程 -> 不准启动正式 Runner。
没有独立线程输出 -> 不准 apply advance transition。
没有 pre-run allow/check -> 不准冻结并启动服务器 batch。
没有 owner 可见监控流 -> 不准声称 workflow 全程接管。
```

旧 `temporary_subagent` / `spawn_agent` / UI 临时 agent 只允许作为非正式诊断历史，不允许作为新的 formal evidence gate。状态机只记录证据迁移，不能替代 agents。Runner 只执行训练，也不能替代 workflow。

## 2. 必需启动顺序

正式实验必须按这个顺序执行：

```text
1. Coordinator 生成 task start card。
2. Coordinator 确认 owner 允许创建左侧命名 Codex 线程。
3. Coordinator 为必需角色创建命名线程，标题使用 <subject_id> | <Role Label>。
4. Planner / Interface / Quality / Runner Monitor 等角色在线程内独立输出 allow/block/propose。
5. Coordinator 写 agent_runtime.yaml。
6. 运行 validate-agent-runtime 和 multi-agent-preflight，通过后才允许 pre-run freeze。
7. Coordinator apply evidence transition。
8. Runner 生成 frozen batch 并启动服务器。
9. Coordinator 进入 owner-visible monitor loop，按间隔汇报线程活动、batch 状态、证据位置和下一步。
10. Log / Quality / Result 线程分别审查运行证据。
11. Coordinator 写 result、quality、agent_summary 和下一条 transition。
12. Coordinator 归档已完成且结论已入账的命名线程；左侧栏只保留当前仍 active 的工作线程。
```

如果第 3 步没有发生，本轮必须阻断正式 Runner。只有 owner 明确把目标改成非正式 `debug_smoke` 排障时，才允许另走 debug 路径；该路径不能作为正式 evidence、candidate keep、best、confirmation、promotion 或 version 判断依据。

## 3. Runtime Gate 文件

每个正式 Runner start 前必须有一个轻量文件：

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
agent_instance_mode: named_owner_thread
lifecycle: workflow_scoped
ui_visibility: left_sidebar_named_threads
tool_support_real_multi_agent_available: true
thread_management_tool: codex_app.create_thread
single_agent_execution: false
runner_start_allowed: true
formal_runner_allowed: true
formal_evidence_allowed: true
owner_monitor_mode: true
owner_role: monitor
owner_visible_reporting: true
report_channel: current_conversation
report_interval_minutes: 15
agent_activity_stream: AGENT_ACTIVITY.md
monitor_handoff_on_pause: required
thread_archive_policy: archive_completed_threads_on_stage_end
archive_completed_threads_on_stage_end: true
archived_threads_record: AGENT_ACTIVITY.md

named_thread_ids:
  runner_monitor: 019...
  interface_checker: 019...
  evidence_quality_checker: 019...

named_thread_titles:
  runner_monitor: "ATTEMPT-007 | Runner Monitor"
  interface_checker: "ATTEMPT-007 | Interface Checker"
  evidence_quality_checker: "ATTEMPT-007 | Evidence Quality Checker"

pre_run_required_checks:
  runner_monitor: allow
  interface_checker: allow
  evidence_quality_checker: allow

agent_instance_status:
  runner_monitor: running
  interface_checker: completed
  evidence_quality_checker: completed

agent_status_refs:
  runner_monitor: AGENT_ACTIVITY.md
  interface_checker: AGENT_ACTIVITY.md
  evidence_quality_checker: AGENT_ACTIVITY.md

agent_output_refs:
  runner_monitor: agent_outputs/runner_monitor.md
  interface_checker: agent_outputs/interface_checker.md
  evidence_quality_checker: agent_outputs/evidence_quality_checker.md

multi_agent_preflight:
  required_threads_created: true
  agent_instance_ids_present: true
  agent_status_refs_valid: true
  independent_outputs_present: true
  agent_output_refs_valid: true
  pre_run_allow_checks_passed: true
  agent_runtime_validated: true
  threads_archivable: true

authority_refs:
  task_start_card: task_start_card.md
  agent_summary: agent_summary.md
  quality_check: quality_check.md
  transitions: TRANSITIONS.jsonl
  agent_activity: AGENT_ACTIVITY.md
```

`named_thread_ids` 不能写成 `named_owner_thread`、`temporary_subagent`、`not_recorded`、`role_only`、`current Codex session` 这类占位文本。必须记录真实可见 thread id。

`named_thread_titles` 必须记录左侧栏实际线程标题。标题使用严格格式：

```text
<subject_id> | <Role Label>
```

禁止使用与任务无关的随机英文昵称，例如 `Herschel`、`Galileo`、`Feynman`、`Bohr`。标题必须同时说明“属于哪个任务”和“承担哪个角色”；否则 `validate-agent-runtime` 必须阻断正式 Runner。

## 3.1 分文件复核契约

正式 `real_multi_agent` 不能只记录“有多个 agent”。每个必需角色的输出文件必须包含：

```yaml
role:
agent_instance_id:
files_reviewed:
decision: allow | block | propose
uncovered_scope:
```

`files_reviewed` 必须列出该角色实际阅读的文件或 artifact。入口规则修改至少要分成三组独立复核：owner 入口文档、runtime/orchestration hard gate、helper 测试与本地 skill 镜像。Coordinator 可以整合结论，但不能把一个 agent 的阅读结果复制给其他角色，也不能用单一上下文冒充分文件复核。

## 4. allow / block 语义

Runner start 之前，所有 pre-run 必需角色必须是 `allow` 或 `pass`。任一 `block`、`not_checked` 或缺失，都必须阻断正式 run。

最低必需角色族：

```text
Runner Monitor
Evidence Quality Checker / Quality Checker
Interface Checker（涉及代码、配置、GZSL、评估语义或新模块时必需）
```

Log Analyst 和 Result Analyst 可以在 run 后进入，但如果它们的结论影响 best、repeat、promotion 或下一轮实验，也必须是独立线程输出。

## 5. formal runner 判定

正式 Runner 同时要求：

```text
formal_evidence: true
activation_mode: real_multi_agent
agent_instance_mode: named_owner_thread
workflow_mode_pairing: live_multi_agent_monitor
ui_visibility: left_sidebar_named_threads
tool_support_real_multi_agent_available: true
single_agent_execution: false
runner_start_allowed: true
formal_runner_allowed: true
formal_evidence_allowed: true
multi_agent_preflight 全部为 true
validate-agent-runtime 通过
```

其中 `multi_agent_preflight` 是启动前的机器可读汇总，不替代角色输出。它必须由 `named_thread_ids`、`named_thread_titles`、`agent_instance_status`、`agent_status_refs`、`agent_output_refs`、`pre_run_required_checks`、`agent_summary.md`、`quality_check.md`、`AGENT_ACTIVITY.md` 等文件支撑。

如果 owner 明确禁止创建线程，但仍要把 detached 服务器训练计入正式 evidence，则允许第二条 formal gate：

```text
formal_evidence: true
activation_mode: role_only
agent_instance_mode: role_only
formal_runtime_backend: server_detached_role_only
workflow_mode_pairing: server_frozen_runner
ui_visibility: current_owner_thread_only
thread_creation_allowed: false
formal_runner_allowed: true
formal_evidence_allowed: true
sequential_role_preflight 全部为 true
validate-agent-runtime 通过
```

这条路径不是 debug/smoke。它要求独立 sequential role outputs、detached server status file、stop 机制和恢复 handoff。

## Live Monitor Gate

`workflow_mode: live_multi_agent_monitor` 必须同时满足：

```text
agent_instance_mode: named_owner_thread
ui_visibility: left_sidebar_named_threads
owner_visible_reporting: true
current_stage_status: running | closeout_complete
report_new_completions: true
monitor_command: monitor-workflow --report-new-completions
active_named_threads_visible_until_closeout: true
archive_after_closeout_only: true
```

Runner 运行期每个新增 completed job 必须通过 `monitor-workflow --report-new-completions` 或等价证据写入 `AGENT_ACTIVITY.md`。如果只能启动服务器 detached runner、不能保持左侧命名线程和逐 job 监控，则必须改走 `server_frozen_runner`，不能把它标成 live multi-agent。

## 6. 降级规则

如果 owner 不允许创建命名线程，或者当前任务只是 debug/smoke，必须写：

```yaml
formal_evidence: false
activation_mode: role_only
agent_instance_mode: role_only
runner_scope: debug_smoke
evidence_level: debug_smoke
formal_runner_allowed: false
formal_evidence_allowed: false
```

debug/smoke 可以帮助排障，但不得升级成正式 attempt 证据。要升级，必须重新走 formal gate：`named_owner_thread` 或 `server_detached_role_only`。

## 7. 收尾归档

阶段结束前运行只读计划：

```bash
python workflow/gtpj_workflow.py agent-cleanup-plan --path <agent_runtime.yaml>
```

`agent-cleanup-plan` 只读列出 keep / archive / unknown；真正归档由 Coordinator 使用线程归档能力完成，并把结果写入 `archived_threads_record`。
