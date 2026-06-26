# GTPJ 实验创新工作流

本目录默认只服务跑实验、做创新、复现、消融、调参、debug 和实验结果记账。

当前阶段已经强制执行核心 workflow。任务路由、启动卡、pre-run freeze、artifact 边界、结果账本、质量门、
agent 凭证和 promotion gate 都是正式规则，不是未来参考。

当前主规范是：

```text
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
docs/workflow/WORKFLOW_ROUTER.md
docs/workflow/TASK_START_CARD.md
docs/workflow/FIRST_CLOSED_LOOP.md
docs/workflow/CURRENT_WORKFLOW_REPORT.md
docs/workflow/GTPJ_WORKFLOW_SPEC.md
docs/workflow/IMPLEMENTATION_STATUS.md
docs/workflow/artifact_policy.md
docs/workflow/ARTIFACT_REGISTRATION.md
docs/workflow/result_index_protocol.md
docs/workflow/experiment_protocol.md
docs/workflow/quality_gate.md
docs/workflow/promotion.md
docs/workflow/agent_contracts.md
docs/workflow/agent_orchestration.md
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
```

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

阅读顺序：

1. `WORKFLOW_ROUTER.md`
2. `TASK_START_CARD.md`
3. `FIRST_CLOSED_LOOP.md`
4. `CURRENT_WORKFLOW_REPORT.md`
5. `GTPJ_WORKFLOW_SPEC.md`
6. `IMPLEMENTATION_STATUS.md`
7. `../GITHUB_GOVERNANCE.md`
8. `../PROJECT_STRUCTURE.md`
9. `../PROJECT_STATUS.md`
10. `git_policy.md`
11. `versioning.md`
12. `idea_tree_protocol.md`
13. `module_trial_protocol.md`
14. `code_interface_contract.md`
15. `artifact_policy.md`
16. `ARTIFACT_REGISTRATION.md`
17. `result_index_protocol.md`
18. `experiment_protocol.md`
19. `quality_gate.md`
20. `promotion.md`
21. `agent_contracts.md`
22. `agent_report_policy.md`
23. `agent_orchestration.md`
24. `agents/README.md`
25. `progress_dashboard.md`
26. `runbook.md`
27. `../../workflow/README.md`
