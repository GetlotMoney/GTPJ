# Codex 工作流入口

Codex 遵循与 OpenClaw 相同的仓库工作流。

## 启动契约

修改文件前，先阅读：

```text
AGENTS.md
NEXT_ACTIONS.md
docs/workflow/README.md
workflow/README.md
```

然后运行：

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
```

## Codex 职责

- 使用 `workflow/gtpj_workflow.py` 执行结构性 workflow 动作。
- 保持改动最小且范围明确。
- 不迁移旧分支名、旧实验 ID、旧视频文件或旧外部工具工作流文件。
- 除非 owner 明确要求，否则不要 push。
- 当 OpenClaw 和 Codex 都可用时，实验执行优先使用 OpenClaw。
