# Codex 未来工作流入口

当前阶段不强制执行 Codex 工作流。Codex 只需要遵循 GitHub 项目治理规范；
未来正式接入时，再遵循与 OpenClaw 相同的仓库工作流。

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

- 可以使用 `workflow/gtpj_workflow.py` 执行结构性辅助动作。
- 保持改动最小且范围明确。
- 不迁移旧分支名、旧实验 ID、旧视频文件或旧外部工具工作流文件。
- 除非 owner 明确要求，否则不要 push。
- 当 OpenClaw 和 Codex 都可用时，实验执行优先使用 OpenClaw。
