# GTPJ 实验创新工作流

本目录默认只服务跑实验、做创新、复现、消融、调参、debug 和实验结果记账。

当前阶段不强制执行完整 runtime workflow。边界类规范已经生效，agent/runtime 编排仍作为未来 OpenClaw/Codex 接入参考。
当前主规范是：

```text
docs/GITHUB_GOVERNANCE.md
docs/PROJECT_STRUCTURE.md
docs/PROJECT_STATUS.md
```

当前强制 workflow 文档：

```text
docs/workflow/WORKFLOW_ROUTER.md
docs/workflow/TASK_START_CARD.md
docs/workflow/FIRST_CLOSED_LOOP.md
docs/workflow/GTPJ_WORKFLOW_SPEC.md
docs/workflow/IMPLEMENTATION_STATUS.md
docs/workflow/artifact_policy.md
docs/workflow/ARTIFACT_REGISTRATION.md
docs/workflow/result_index_protocol.md
docs/workflow/experiment_protocol.md
docs/workflow/quality_gate.md
docs/workflow/promotion.md
docs/workflow/agent_contracts.md
```

未来参考和 runtime 编排文档：

```text
docs/workflow/agent_orchestration.md
docs/workflow/progress_dashboard.md
docs/workflow/runbook.md
workflow/
```

GTPJ 未来 workflow 仍建议使用“版本优先”的实验结构。

```text
idea_tree
  -> module_trials
  -> promoted baseline vX
  -> tune / ablation / confirmation 放在 experiments/vX 下
```

可以保留的核心规则：

```text
一个 vX = 一个 baseline = 一个 Git tag = 一个版本实验目录
```

未来 runtime 规则：

- OpenClaw 优先用于运行实验。
- Codex 遵循相同仓库事实来源。
- GitHub 仓库是治理事实源、复现控制层和轻量结果索引层。
- `GTPJ_Research` 保存 idea/source 长推理，`GTPJ_Warehouse` 保存大型实验资产。
- 结构性动作可以使用 `workflow/gtpj_workflow.py`，但当前阶段不强制。
- GitHub 文档是 workflow 规范的权威来源；本地 `gtpj-workflow` skill 是执行副本，修改后必须同步。

阅读顺序：

1. `WORKFLOW_ROUTER.md`
2. `TASK_START_CARD.md`
3. `FIRST_CLOSED_LOOP.md`
4. `GTPJ_WORKFLOW_SPEC.md`
5. `IMPLEMENTATION_STATUS.md`
6. `../GITHUB_GOVERNANCE.md`
7. `../PROJECT_STRUCTURE.md`
8. `../PROJECT_STATUS.md`
9. `git_policy.md`
10. `versioning.md`
11. `idea_tree_protocol.md`
12. `module_trial_protocol.md`
13. `code_interface_contract.md`
14. `artifact_policy.md`
15. `ARTIFACT_REGISTRATION.md`
16. `result_index_protocol.md`
17. `experiment_protocol.md`
18. `quality_gate.md`
19. `promotion.md`
20. `agent_contracts.md`
21. `agent_orchestration.md`
22. `agents/README.md`
23. `progress_dashboard.md`
24. `runbook.md`
25. `../../workflow/README.md`
