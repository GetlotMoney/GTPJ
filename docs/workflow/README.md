# Workflow 总览

GTPJ 使用“版本优先”的实验工作流。

```text
idea_tree
  -> module_trials
  -> promoted baseline vX
  -> tune / ablation / confirmation 放在 experiments/vX 下
```

核心规则：

```text
一个 vX = 一个 baseline = 一个 Git tag = 一个版本实验目录
```

Runtime 规则：

- OpenClaw 优先用于运行实验。
- Codex 遵循相同文件，也可以执行同一套 workflow。
- 仓库文件是两个 runtime 的唯一事实来源。
- 结构性动作必须通过 `workflow/gtpj_workflow.py`。

阅读顺序：

1. `../PROJECT_STRUCTURE.md`
2. `git_policy.md`
3. `versioning.md`
4. `idea_tree_protocol.md`
5. `module_trial_protocol.md`
6. `code_interface_contract.md`
7. `experiment_protocol.md`
8. `review_gate.md`
9. `runbook.md`
10. `workflow/README.md`
