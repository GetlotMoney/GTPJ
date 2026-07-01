# Autonomous Research Campaign Workflow

本文定义 GTPJ 的长期目标：owner 只给论文来源、评估标准、安全边界和实验标准，workflow 从 0 到最终结果接管完整研究 campaign，并在 10 到 20 天这类长周期内持续调度实验、代码、证据和最终交付。

这不是普通“多 agents 聊天”。它是一个可审计的实验状态机：

```text
owner brief
  -> source intake
  -> idea discovery
  -> experiment planning
  -> implementation / tune / ablation / confirmation / promotion
  -> long-running runner
  -> evidence ledger
  -> final result and code package
```

## 1. Owner 最小输入

进入全自动 research campaign 时，owner 只需要提供：

```yaml
campaign_goal:
paper_sources:
evaluation_standard:
safety_boundaries:
experiment_standard:
compute_budget:
time_budget:
final_deliverables:
```

字段含义：

| 字段 | 含义 |
|---|---|
| `campaign_goal` | 本轮研究目标，例如“围绕 GTPJ 动态路由找可复现提升”。 |
| `paper_sources` | 论文 PDF、论文列表、代码仓库、项目页或 owner 给出的来源入口。 |
| `evaluation_standard` | 主要指标、数据集、split、repeat 要求、promotion 门槛和可接受波动。 |
| `safety_boundaries` | 不允许做的事，例如不 push、不删数据、不改远端、不污染评估语义。 |
| `experiment_standard` | 每类实验的最小证据要求，例如 min3 repeat、ablation、quality gate。 |
| `compute_budget` | GPU、batch 数、最大并发、checkpoint retention 和失败隔离策略。 |
| `time_budget` | 运行 10 天、20 天或直到触发 stop condition。 |
| `final_deliverables` | 最终代码、结果表、复现说明、best config、失败总结和下一步建议。 |

owner 不需要指定具体实验类型、agent 列表、分支名、batch 名、artifact id 或每一轮参数。Coordinator 根据本文件和现有 workflow 自动展开。

## 2. Workflow 接管范围

全自动 campaign 可以调度所有 GTPJ 实验类型：

```text
paper intake / source review
idea discovery / idea tree update
version-level tune
version-level ablation
version-level confirmation
trial-internal attempt / tune / narrow ablation / confirmation
innovation / module trial
debug / smoke
promotion / version ledger
final report / final code handoff
```

任意组合数量命令，例如 `跑10创新+100调参`，必须遵守：

```text
docs/workflow/mixed_experiment_campaign_protocol.md
```

Coordinator 必须为每个子任务选择正确协议，不允许把所有事情塞进一个模糊 experiment。

规则：

- 从论文或代码来源产生新机制时，先走 `paper_intake.md` 和 `idea_tree_protocol.md`。
- 只调正式 baseline 参数时，写入 `experiments/vX/tune/`。
- 只确认正式 baseline 或候选结果时，写入 `experiments/vX/confirmation/`。
- 调某个 module trial 内部参数时，写入该 trial 的 `ATTEMPTS.md` 和 `attempts/ATTEMPT-xxx/`。
- 改模型、forward、loss、eval 或数据流时，进入 `innovation / module trial` 并执行 Review 0-3。
- 只有证据达到 promotion 标准时，才进入 `promotion.md`。

## 3. Campaign 层级

长周期 campaign 使用分层状态，不为每一次小尝试单独开一套永久上下文：

```text
research_campaign
  -> workstream
  -> workflow task
  -> batch
  -> run
  -> attempt
```

建议 GitHub 轻量账本：

```text
experiments/campaigns/CAMP-YYYYMMDD-xxxx/
  campaign_manifest.yaml
  campaign_plan.md
  TASK_START_CARD.md
  RESULT_INDEX.md
  DECISION_LOG.md
  agent_summary.md
  quality_check.md
  final_report.md
```

其中具体实验证据仍写入原本所属位置：

```text
experiments/vX/tune/
experiments/vX/ablation/
experiments/vX/confirmation/
experiments/module_trials/.../TRIAL-xxx/attempts/ATTEMPT-xxx/
```

Warehouse 保存 raw logs、checkpoints、figures、完整 runner 报告和长周期运行资产。GitHub 只保存 artifact id、URI、sha256、size、config、result 和 quality 摘要。

## 4. Agent 生命周期

全自动 campaign 默认：

```yaml
agents:
  activation_mode: real_multi_agent
  agent_instance_mode: temporary_subagent
  lifecycle: workflow_scoped
  evidence_source: files_and_artifacts
```

含义：

- `temporary_subagent` 是本轮 workflow / campaign 的活上下文，可以在整个 campaign 阶段内持续存在。
- `persistent_thread` 是跨 workflow 的活上下文，只在确实需要跨多轮持续追踪时启用。
- 长期 agent 不是永久聊天窗口；长期 agent 是 `profile.md`、`memory.md`、调用协议、历史 `agent_summary.md` 和 issues。
- 正式事实永远来自 repo、Research、Warehouse、manifest、result、quality 和 agent summary，不来自任何隐藏聊天上下文。

默认清晰角色名：

```text
Workflow Coordinator
Source Reader
Idea Planner
Code Implementer
Interface Contract Checker
Experiment Runner
Runner Monitor
Log Metric Parser
Result Comparator
Evidence Quality Checker
Independent Reviewer
Warehouse Registrar
Promotion Manager
```

只启用当前阶段需要的角色。不要为 2000 个 attempt 开 2000 个永久 agent。

## 5. 调度循环

Coordinator 在 campaign 中反复执行下面循环：

```text
1. 读取 campaign brief 和当前状态。
2. 选择下一步最有价值的任务类型。
3. 生成或更新 task start card。
4. 执行对应协议和 hard gates。
5. 如果需要训练，Runner 串行持有 GPU lock。
6. Log Metric Parser 解析指标。
7. Evidence Quality Checker 检查证据完整性。
8. Result Comparator 比较 baseline、repeat、U/S 稳定性和失败模式。
9. Coordinator 更新 GitHub 轻量账本、Research 决策历史和 Warehouse artifact 引用。
10. 根据结果决定 keep、rerun、tune、ablate、confirm、promote、reject 或 stop。
```

调度可以不间断运行，但每个子任务都必须留下可恢复状态。任何 agent 可以销毁，workflow 状态不能丢。

## 6. 实验选择规则

workflow 可以自行安排具体实验，但必须遵守：

- 单次最好结果不能直接当正式结论。
- 候选要成为正式数据，默认必须进行 3 次 clean repeat。
- 复现实验通过时，正式行可以使用 3 次 repeat 中最高 H 对应的 U/S/ZS，同时保留 mean/min/max 作为稳定性证据。
- tune-only 不能开新 `vX` 框架版本。
- 代码语义或评估语义变化才可能进入新 trial 或新 framework version。
- ICSA、direction、PSE、local 等方向由结果证据驱动，不靠先验偏好。
- 如果结果影响下一轮高成本实验，必须经过 Result Comparator 和 Evidence Quality Checker。

## 7. 硬门

以下情况必须阻断：

- label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清楚；
- dirty worktree 上启动正式 run；
- run_commit、config、manifest 或 artifact 引用不明确；
- raw logs、checkpoint、generated figures 被写入 GitHub；
- promotion 只凭一次 H 提升；
- 使用 role_only 冒充 real_multi_agent；
- memory-derived fact 未经当前 repo、log 或 artifact 验证就进入正式结论；
- safety boundary 要求禁止的 push、发布、删除、远端改写或破坏性迁移。

## 8. 长周期运行状态

持续运行依赖三个层面：

```text
服务器 runner / batch_status / logs / Warehouse  # 真正运行
GitHub campaign ledger / result index / quality  # 正式轻量事实
workflow agents / temporary contexts              # 当前阶段执行上下文
```

本地电脑关闭、对话窗口关闭或临时 agent 结束，都不应导致 campaign 状态丢失。恢复时以 GitHub 账本、Warehouse artifact 和服务器 batch 状态为准。

## 9. Checkpoint Retention

每次实验完成后，Runner / Warehouse Registrar 必须按工作流规范清理 checkpoint：

```text
只保留本轮 campaign 或 batch 中最好的 3 个模型 checkpoint。
其它 checkpoint 删除或归档到非默认保留区。
GitHub 只记录保留 checkpoint 的 artifact id、URI、sha256、size 和对应指标。
```

如果某个 checkpoint 因 debug、复核或论文图表需要临时保留，必须在 Warehouse artifact 记录中写明保留理由和过期条件。

## 10. Stop Conditions

campaign 不应该无限跑。满足任一条件时必须停下并汇报：

- 达到 owner 的 time budget 或 compute budget；
- 连续若干轮没有超过 baseline / confirmed reference；
- top candidates 已完成 min3 repeat 且结论稳定；
- 出现 hard gate blocker；
- 服务器、数据、评估或代码状态无法恢复到可审计状态；
- 已达到 promotion 或 final deliverable 标准。

## 11. 最终交付

全自动 campaign 的最终交付至少包含：

```text
final_report.md
RESULT_INDEX.md
best_config.yaml
final_code_manifest.md
quality_check.md
agent_summary.md
promotion_decision 或 reject/continue decision
Warehouse artifact index
```

最终汇报必须回答：

- 哪些论文或来源被读过；
- 形成了哪些 idea；
- 跑了哪些实验类型；
- best single 是什么；
- min3 repeat 结果是什么；
- U/S/ZS 是否稳定；
- 哪些方向失败，为什么；
- 哪个代码 commit 和 config 可复现最终结果；
- 是否满足 promotion / paper result 标准；
- 如果不满足，下一轮最小高价值动作是什么。

## 12. 当前落地边界

本文是目标工作流规范，不等于所有自动化代码已经完成。

当前可立即执行的是：

- 按现有 workflow 手动或半自动调度 paper intake、tune、ablation、confirmation、module trial、promotion；
- 用 `workflow/gtpj_workflow.py` 做结构校验、状态检查、batch planning、result analysis 和 ledger closeout；
- 用 workflow-scoped temporary agents 保持角色上下文隔离；
- 把 campaign 状态写入 GitHub 轻量账本和 Warehouse。

后续要产品化的部分：

- campaign-level planner；
- automatic experiment scheduler；
- server-side long-running controller；
- validate-state-sync / validate-agent-ledger；
- checkpoint retention helper；
- final report generator。
