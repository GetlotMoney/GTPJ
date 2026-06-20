# 未来工作流参考

当前阶段不执行完整 workflow。本目录只保存未来 OpenClaw/Codex 接入时可以参考的规则草案。
当前主规范是：

```text
docs/GITHUB_GOVERNANCE.md
docs/PROJECT_STRUCTURE.md
docs/PROJECT_STATUS.md
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
- 仓库文件是两个 runtime 的唯一事实来源。
- 结构性动作可以使用 `workflow/gtpj_workflow.py`，但当前阶段不强制。

阅读顺序：

1. `../PROJECT_STRUCTURE.md`
2. `git_policy.md`
3. `versioning.md`
4. `idea_tree_protocol.md`
5. `module_trial_protocol.md`
6. `code_interface_contract.md`
7. `experiment_protocol.md`
8. `quality_gate.md`
9. `runbook.md`
10. `workflow/README.md`
