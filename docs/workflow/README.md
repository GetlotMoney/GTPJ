# 未来工作流参考

当前阶段不强制执行完整 runtime workflow。边界类规范已经生效，agent/runtime 编排仍作为未来 OpenClaw/Codex 接入参考。
当前主规范是：

```text
docs/GITHUB_GOVERNANCE.md
docs/PROJECT_STRUCTURE.md
docs/PROJECT_STATUS.md
```

当前强制 workflow 文档：

```text
docs/workflow/GTPJ_WORKFLOW_SPEC.md
docs/workflow/IMPLEMENTATION_STATUS.md
docs/workflow/artifact_policy.md
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
- `GTPJ_Research`、`GTPJ_Warehouse`、`GTPJ_Manuscript` 分别是论文材料、大型实验资产和写作资产事实源。
- 结构性动作可以使用 `workflow/gtpj_workflow.py`，但当前阶段不强制。
- GitHub 文档是 workflow 规范的权威来源；本地 `gtpj-workflow` skill 是执行副本，修改后必须同步。

阅读顺序：

1. `GTPJ_WORKFLOW_SPEC.md`
2. `IMPLEMENTATION_STATUS.md`
3. `../GITHUB_GOVERNANCE.md`
4. `../PROJECT_STRUCTURE.md`
5. `../PROJECT_STATUS.md`
6. `git_policy.md`
7. `versioning.md`
8. `idea_tree_protocol.md`
9. `module_trial_protocol.md`
10. `code_interface_contract.md`
11. `artifact_policy.md`
12. `result_index_protocol.md`
13. `experiment_protocol.md`
14. `quality_gate.md`
15. `promotion.md`
16. `agent_contracts.md`
17. `agent_orchestration.md`
18. `agents/README.md`
19. `progress_dashboard.md`
20. `runbook.md`
21. `../../workflow/README.md`
