# Agent Report Policy

本文件规定 GTPJ 实验中 agent 工作历史如何保存。目标是保留审计凭证，而不是保存完整聊天流水。

## 核心原则

必须记录：

- 哪些 agents 参与了本次实验；
- 每个 agent 的职责、输入文件、检查范围和输出；
- 是否发现 blocking / non-blocking issue；
- 结论是 keep、reject、rerun、blocked、promote 还是 not_applicable；
- 关联 commit、run id、artifact id、URI、hash 或日志路径。

不保存：

- 完整对话流水；
- 无关中间讨论；
- 重复日志正文；
- 长篇推理草稿；
- raw logs、checkpoint、generated figures 或完整论文笔记。

## 分级保存规则

| 场景 | GitHub 记录 | Warehouse 记录 |
|---|---|---|
| confirmation / 普通 tune | `agent_summary.md` | 可选完整 runner/log analyst 报告 |
| ablation / 改代码 tune | `agent_summary.md`、`interface_check.md`、`quality_check.md` | 可选完整 runner/log analyst/reviewer 报告 |
| innovation / module trial | `agent_summary.md`、`implementation.md`、`idea_intent_check.md`、`interface_precheck.md`、`review_round_1.md`、`interface_check.md`、`quality_check.md`、`review_round_2.md`、必要时 `review.md` | 可选完整 agent reports |
| promotion / 新 baseline | `agent_summary.md`、`quality_check.md`、必要 reviewer/result analyst report | 可选完整 promotion reports |

## GitHub 文件边界

每个真实实验目录至少保存一个轻量 agent 凭证文件：

```text
agent_summary.md
```

代码或接口语义发生变化时，还必须保存：

```text
interface_check.md
```

创新或 promotion 需要独立最终审查时，可以额外保存：

```text
review.md
```

如果某个 agent 的完整报告很长，不放 GitHub；放入 Warehouse 并在 `agent_summary.md` 中引用 artifact id。

## `agent_summary.md` 最小字段

```text
experiment_id:
run_id:
base_version:
code_branch:
code_commit:
activation_mode:
agent_instance_mode:
lifecycle:
activation_reason:
required_roles:
required_real_agents:
agent_persistent_threads:
agent_set:
serial_agents:
parallel_agents:
disabled_agents:
temporary_subagents:
tool_support:
memory_policy:
memory_used:
memory_sources:
persistent_thread_ids:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
runtime_state:
warehouse_report_artifacts:
final_decision:
review_rounds:
temporary_agents:
```

每个 agent 至少记录：

```text
agent:
role:
agent_instance_mode:
agent_instance_type:
lifecycle:
persistent_thread_id:
temporary_subagent_reason:
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Agent 边界

- Coordinator 是唯一最终 GitHub 账本写入者。
- Runner 只写 Warehouse raw artifacts 和 runtime 状态。
- Log Analyst 只解析日志事实，不补造指标。
- Quality Checker 检查证据完整性和边界，不只看 H 分数。
- Interface Checker 在 label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清时必须阻断。
- 多个 agents 不得同时写同一个 GitHub 账本文件。
- `real_multi_agent` 必须保留各 agent 的独立输入、发现和结论；如果当前工具不可用，只能在 `tool_support.fallback_mode` 记录 `role_only_with_independent_sequential_review`，不能冒充真实多 agent。
- 正式 `real_multi_agent` 默认记录 `agent_instance_mode: temporary_subagent` 和 `lifecycle: workflow_scoped`；长周期 campaign 可写 `campaign_scoped`。
- `persistent_thread` 是跨 workflow 的可选活上下文；如启用，必须保存 thread id 或可见 label，但 thread 本身不是正式证据源。
- `temporary_subagent` 可以覆盖本轮 workflow 或 campaign 阶段；它必须把正式输出写入 `agent_summary.md`、result、quality、issues、memory、Research、Warehouse 或 campaign ledger。
- memory 只能用于定位和背景提醒；没有被当前 repo、日志或 artifact 验证的 memory-derived fact 不能写入正式结果、质量门或 promotion 证据。
- 长期 agent 记忆来自 `docs/workflow/agents/shared_roles/<role>/memory.md`；每次真实实验必须记录读取了哪些角色记忆、是否启用 persistent thread，以及是否需要写回更新。

## 入账时机

真实实验结束时，Coordinator 必须在结果提交前确认：

- `agent_summary.md` 存在；
- 已启用 agents 和禁用 agents 与实验类型匹配；
- `activation_mode`、`agent_instance_mode`、`agent_instance_type`、`lifecycle`、`persistent_thread_id`、`independence_scope`、`output_locations` 和 memory 字段已填写；
- blocking issue 已处理或结果被标记为 blocked/rerun/reject；
- 需要长期保存的完整报告已经进入 Warehouse，GitHub 只记录 artifact id/URI。

Module trial attempt closeout must use the helper path when attempt evidence exists:

```bash
python workflow/gtpj_workflow.py sync-trial-summary --trial-dir ... --attempt-id ... --decision ...
python workflow/gtpj_workflow.py closeout-check --trial-dir ... --attempt-id ...
```

The helper-generated `agent_summary.md` and `review_round_2.md` are the current-attempt GitHub summaries. Longer sub-agent reports may be kept in Warehouse, but they must not be required for the root closeout files to point at the latest attempt.
