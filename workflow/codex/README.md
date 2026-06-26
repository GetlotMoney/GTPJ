# Codex 工作流入口

当前阶段 Codex 必须遵循 GTPJ 核心 workflow。OpenClaw 和 Codex 只是不同 runtime 入口；
两者共享同一套 GitHub 事实源、任务路由、启动卡、artifact 边界、结果账本、质量门和 agent 凭证规则。

## 启动契约

修改文件前，先阅读：

```text
AGENTS.md
NEXT_ACTIONS.md
docs/GITHUB_GOVERNANCE.md
docs/workflow/README.md
workflow/README.md
```

然后运行：

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
```

## Codex 职责

- 优先使用 `workflow/gtpj_workflow.py` 执行 validate、audit-boundary、目录创建和结果记录等结构性辅助动作。
- 不把 helper 当成研究判断黑盒；Coordinator 仍要判断任务类型、实验语义、质量门和结论边界。
- 保持改动最小且范围明确。
- 不迁移旧分支名、旧实验 ID、旧视频文件或旧外部工具工作流文件。
- 除非 owner 明确要求，否则不要 push。
- 当 OpenClaw 和 Codex 都可用时，实验执行优先使用 OpenClaw。
