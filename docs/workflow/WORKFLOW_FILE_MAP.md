# GTPJ 工作流文件地图

这个文件用来让 workflow 目录可读：哪些是日常入口，哪些只是参考材料。

## 日常权威文件

| 文件 | 状态 |
|---|---|
| `START_HERE.md` | 每个 GTPJ 工作流任务从这里开始。 |
| `WORKFLOW_KERNEL.md` | 硬规则层。必须短而权威。 |
| `WORKFLOW_ROUTER.md` | 完整路由表。任务类型模糊或混合时再读。 |
| `TASK_START_MINI.md` | 给 owner 看的精简启动摘要。 |
| `TASK_START_CARD.md` | 正式写入或运行前的完整启动记录。 |

## 有效执行卡

| 文件 | 状态 |
|---|---|
| `playbooks/paper_intake.md` | 论文/来源/idea discovery 操作卡。 |
| `playbooks/tune.md` | 调参操作卡。 |
| `playbooks/ablation.md` | 消融操作卡。 |
| `playbooks/confirmation.md` | 复现/确认操作卡。 |
| `playbooks/innovation.md` | idea/module-trial 操作卡。 |
| `playbooks/promotion.md` | 升版操作卡。 |
| `playbooks/mixed_campaign.md` | 任意组合实验 campaign 操作卡。 |
| `playbooks/autonomous_campaign.md` | 长周期全自动研究 campaign 操作卡。 |

## 参考协议

只有被当前 playbook 要求时才读：

```text
paper_intake.md
idea_tree_protocol.md
experiment_protocol.md
module_trial_protocol.md
code_interface_contract.md
innovation_code_review_protocol.md
quality_gate.md
promotion.md
ARTIFACT_REGISTRATION.md
agent_orchestration.md
agent_report_policy.md
agents/
mixed_experiment_campaign_protocol.md
autonomous_research_campaign.md
```

## 历史或状态文件

这些文件保存决策、历史、图示或实现状态，不作为第一阅读入口：

```text
GTPJ_WORKFLOW_SPEC.md
CURRENT_WORKFLOW_REPORT.md
FIRST_CLOSED_LOOP.md
IMPLEMENTATION_STATUS.md
workflow_diagrams.md
runbook.md
progress_dashboard.md
issues/
```

## 模板和 Schema

真正写证据时使用：

```text
experiments/templates/
schemas/
workflow/gtpj_workflow.py
```

## 简化规则

如果某条规则每天都要用，写进 `WORKFLOW_KERNEL.md`。

如果规则只和某类任务有关，写进对应 playbook。

如果只是长解释、证据或历史，保留为参考文件，并从 playbook 指过去。
