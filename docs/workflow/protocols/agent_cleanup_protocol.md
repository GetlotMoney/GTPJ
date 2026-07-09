# Agent Cleanup Protocol

本协议只解决一个问题：每轮 workflow 或阶段结束后，左侧命名 Codex 线程不能变成历史堆积。旧 UI 临时 agent 已不再作为正式范式使用。

## 1. 目标

左侧栏只保留当前阶段仍在工作的 active 线程。历史结论必须回到文件和 artifact，不能靠旧对话窗口保存。

创建新的 formal named threads 前，Coordinator 必须先问 owner 是否允许，并确认当前左侧栏不会被旧线程混淆。如果 owner 看到历史线程太多，正式 `real_multi_agent` 必须暂停，先整理账本和归档计划。

阶段结束时，Coordinator 必须执行：

```text
1. 列出保留名单。
2. 列出归档名单。
3. 确认归档名单的输出已经写入 agent_summary / AGENT_ACTIVITY / result / quality / issues / memory。
4. 使用线程归档能力归档已完成的 named_owner_thread。
5. 把归档结果写回 AGENT_ACTIVITY.md 或 closeout summary。
```

## 2. 必须记录的字段

`agent_runtime.yaml` 中每个命名线程至少要能追踪：

```yaml
named_thread_ids:
  runner_monitor: 019...

named_thread_titles:
  runner_monitor: "ATTEMPT-005 | Runner Monitor"

agent_instance_status:
  runner_monitor: completed

agent_output_refs:
  runner_monitor: agent_outputs/runner_monitor.md

agent_cleanup:
  thread_archive_policy: archive_completed_threads_on_stage_end
  archive_completed_threads_on_stage_end: true
  archive_command: codex_app.set_thread_archived
  archive_results_record: AGENT_ACTIVITY.md
```

如果工具返回 `not_found`，不能伪造为已归档，必须记录为：

```text
archive_result: not_found
meaning: repo ledger thread id is no longer reachable by the current thread tool
```

## 3. 归档判定

```text
running / active / spawned -> 保留
completed / complete / closed -> 归档
missing / failed / unknown / not_found -> 不盲目归档，先汇报
```

重复 thread id 不能代表独立角色。一个 thread id 如果同时承担多个正式角色，必须标记为历史限制或降级，不能作为完整 `real_multi_agent` 证据。

## 4. 命名判定

正式 runtime 必须使用：

```text
<subject_id> | <Role Label>
```

其中 `subject_id` 是本次 attempt / confirmation / campaign / review pack 的机器可读任务 id，`Role Label` 是清晰角色名，例如 `Runner Monitor`、`Interface Checker`、`Evidence Quality Checker`、`Result Analyst`。

非法示例：

```text
Herschel
Galileo
Feynman
Runner
Quality
```

非法原因：看不出属于哪个任务、哪个证据对象，也无法和 `agent_runtime.yaml` 稳定对应。

## 5. 只读计划命令

阶段结束前先运行：

```bash
python workflow/gtpj_workflow.py agent-cleanup-plan --path <agent_runtime.yaml>
```

它只输出保留/归档/未知名单，不会归档线程。

## 6. Owner 可见汇报格式

```text
role: Coordinator
action: agent cleanup
evidence: agent_runtime.yaml + AGENT_ACTIVITY.md + agent_outputs/
keep: ...
archive: ...
unknown: ...
next: archive completed threads, then write archive_result
```

如果 owner 说左侧栏数量和 cleanup plan 不一致，Coordinator 必须说明：

```text
repo 账本只能识别已记录的 runtime threads；
当前工具若没有完整 list_threads API，无法权威枚举 UI 中所有历史线程；
未知 UI thread 需要按标题人工对照后再归档。
```

在这种不一致被解决前，禁止创建新的 formal named threads。否则每次新开正式角色时，旧窗口会继续堆积。

## 7. 旧 UI agent 污染退出规则

如果同时满足下面条件：

```text
1. owner 可见 UI 仍有历史临时 agent 或未知命名线程；
2. UI 没有关闭 / 归档按钮；
3. 已记录 id 不能被当前工具关闭；
4. 当前环境没有 list_agents 或按 UI nickname 关闭的工具；
```

则当前线程必须标记为：

```yaml
owner_window_status: polluted_by_unknown_ui_agents
formal_real_multi_agent_allowed: false
runner_start_allowed: false
allowed_actions:
  - read_only_status
  - repo_ledger_cleanup
  - handoff_to_new_clean_owner_thread
blocked_actions:
  - spawn_agent
  - formal_runner
  - confirmation_evidence_start
  - promotion
```

正确处理不是继续尝试在当前线程补 gate，而是开一个干净 owner 线程；新线程仍然必须遵守命名线程 gate，不能重新启用旧 `create_thread` 范式。
