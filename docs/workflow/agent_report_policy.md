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
| innovation / module trial | `agent_summary.md`、`implementation.md`、`interface_check.md`、`quality_check.md`、`review.md` | 可选完整 agent reports |
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
agent_set:
serial_agents:
parallel_agents:
disabled_agents:
runtime_state:
warehouse_report_artifacts:
final_decision:
```

每个 agent 至少记录：

```text
agent:
role:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
```

## Agent 边界

- Coordinator 是唯一最终 GitHub 账本写入者。
- Runner 只写 Warehouse raw artifacts 和 runtime 状态。
- Log Analyst 只解析日志事实，不补造指标。
- Quality Checker 检查证据完整性和边界，不只看 H 分数。
- Interface Checker 在 label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清时必须阻断。
- 多个 agents 不得同时写同一个 GitHub 账本文件。

## 入账时机

真实实验结束时，Coordinator 必须在结果提交前确认：

- `agent_summary.md` 存在；
- 已启用 agents 和禁用 agents 与实验类型匹配；
- blocking issue 已处理或结果被标记为 blocked/rerun/reject；
- 需要长期保存的完整报告已经进入 Warehouse，GitHub 只记录 artifact id/URI。

