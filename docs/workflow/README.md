# GTPJ 实验创新工作流

本目录默认只服务跑实验、做创新、复现、消融、调参、debug 和实验结果记账。

当前阶段已经强制执行核心 workflow。任务路由、启动卡、pre-run freeze、artifact 边界、结果账本、质量门、
agent 凭证和 promotion gate 都是正式规则，不是未来参考。

长期目标见：

```text
docs/workflow/autonomous_research_campaign.md
```

该文档定义最终形态：owner 只给论文来源、评估标准、安全边界和实验标准，workflow 从 0 到最终结果接管
paper intake、idea discovery、tune、ablation、confirmation、innovation/module trial、promotion、
服务器长周期运行、证据入账和最终代码/结果交付。

owner 日常不需要直接阅读完整协议森林。默认先看：

```text
docs/workflow/QUICK_START.md
docs/workflow/TASK_START_MINI.md
```

`QUICK_START.md` 是人话入口，支持 `查状态`、`复现`、`调参`、`消融`、`开新模块`、
`试这个：...`、`继续上一个`、`升版本`、`切版本` 等短口令。`TASK_START_MINI.md` 是 owner
可见的 8 字段启动卡。完整 `WORKFLOW_ROUTER.md` 和 `TASK_START_CARD.md` 保留为 Coordinator
后台展开和审查依据。

状态、复现、结果比较、promotion 或 tag 前，Coordinator 必须先检查 `baseline_repro_status`
或运行 `python workflow/gtpj_workflow.py repro-status --version <vX>`，不要靠聊天记忆判断
某个 `best_observed_H` 是否已经变成 `confirmed_H`。

当前主规范是：

```text
docs/workflow/QUICK_START.md
docs/workflow/TASK_START_MINI.md
docs/workflow/GTPJ_WORKFLOW_SPEC.md
docs/workflow/WORKFLOW_ROUTER.md
docs/workflow/TASK_START_CARD.md
docs/workflow/IMPLEMENTATION_STATUS.md
docs/GITHUB_GOVERNANCE.md
docs/PROJECT_STRUCTURE.md
docs/PROJECT_STATUS.md
```

当前强制 workflow 文档：

```text
docs/workflow/QUICK_START.md
docs/workflow/TASK_START_MINI.md
docs/workflow/WORKFLOW_ROUTER.md
docs/workflow/TASK_START_CARD.md
docs/workflow/FIRST_CLOSED_LOOP.md
docs/workflow/autonomous_research_campaign.md
docs/workflow/CURRENT_WORKFLOW_REPORT.md
docs/workflow/GTPJ_WORKFLOW_SPEC.md
docs/workflow/IMPLEMENTATION_STATUS.md
docs/workflow/workflow_diagrams.md
docs/workflow/paper_intake.md
docs/workflow/artifact_policy.md
docs/workflow/ARTIFACT_REGISTRATION.md
docs/workflow/result_index_protocol.md
docs/workflow/experiment_protocol.md
docs/workflow/innovation_code_review_protocol.md
docs/workflow/quality_gate.md
docs/workflow/promotion.md
docs/workflow/agent_contracts.md
docs/workflow/agent_orchestration.md
docs/workflow/agents/long_term_memory.md
docs/workflow/agent_report_policy.md
```

已落地 runtime / helper 入口：

```text
workflow/README.md
workflow/codex/README.md
workflow/openclaw/README.md
```

按需创建或仍在完善的自动 runtime / 看板文档：

```text
docs/workflow/progress_dashboard.md
docs/workflow/runbook.md
docs/workflow/issues/README.md
```

实验执行中的具体问题、解决方案和预防规则放在 `docs/workflow/issues/`。新对话只需要先读
`issues/README.md` 和最近日期的问题文档，不需要每次全量读取所有历史问题。

GTPJ workflow 使用“版本优先”的实验结构。

```text
idea_tree
  -> module_trials
  -> promoted baseline vX
  -> version-level tune / ablation / confirmation 放在 experiments/vX 下
  -> trial-internal param_tune / narrow ablation / confirmation 放在 module_trials/.../attempts/ 下
```

可以保留的核心规则：

```text
一个 vX = 一个 baseline = 一个 Git tag = 一个版本实验目录
```

runtime 规则：

- OpenClaw 优先用于运行实验。
- Codex 遵循相同仓库事实来源和 workflow 规范。
- GitHub 仓库是治理事实源、复现控制层和轻量结果索引层。
- `GTPJ_Research` 保存 idea/source 长推理，`GTPJ_Warehouse` 保存大型实验资产。
- 结构性动作优先使用 `workflow/gtpj_workflow.py` 做 validate、audit-boundary、目录创建和结果记录；该工具不替代研究判断或实验解释。
- GitHub 文档是 workflow 规范的权威来源；本地 `gtpj-workflow` skill 是执行副本，修改后必须同步。

日常阅读顺序：

1. `QUICK_START.md`
2. `TASK_START_MINI.md`
3. `../../workflow/README.md`

Coordinator / agent 完整展开顺序：

1. `WORKFLOW_ROUTER.md`
2. `TASK_START_CARD.md`
3. `FIRST_CLOSED_LOOP.md`
4. `autonomous_research_campaign.md`
5. `CURRENT_WORKFLOW_REPORT.md`
6. `GTPJ_WORKFLOW_SPEC.md`
7. `IMPLEMENTATION_STATUS.md`
8. `workflow_diagrams.md`
9. `../GITHUB_GOVERNANCE.md`
10. `../PROJECT_STRUCTURE.md`
11. `../PROJECT_STATUS.md`
12. `git_policy.md`
13. `versioning.md`
14. `idea_tree_protocol.md`
15. `paper_intake.md`
16. `module_trial_protocol.md`
17. `code_interface_contract.md`
18. `innovation_code_review_protocol.md`
19. `artifact_policy.md`
20. `ARTIFACT_REGISTRATION.md`
21. `result_index_protocol.md`
22. `experiment_protocol.md`
23. `quality_gate.md`
24. `promotion.md`
25. `agent_contracts.md`
26. `agent_report_policy.md`
27. `agent_orchestration.md`
28. `agents/README.md`
29. `agents/long_term_memory.md`
30. `progress_dashboard.md`
31. `runbook.md`
32. `../../workflow/README.md`
