# OpenClaw 工作流入口

当前阶段 OpenClaw 必须遵循 GTPJ 核心 workflow。OpenClaw 和 Codex 只是不同 runtime 入口；
两者共享同一套 GitHub 事实源、任务路由、启动卡、artifact 边界、结果账本、质量门和 agent 凭证规则。

当前主规范：

```text
docs/workflow/GTPJ_WORKFLOW_SPEC.md
docs/workflow/WORKFLOW_ROUTER.md
docs/workflow/TASK_START_CARD.md
docs/GITHUB_GOVERNANCE.md
docs/PROJECT_STRUCTURE.md
```

## 启动契约

选择或运行实验前，先阅读：

```text
AGENTS.md
NEXT_ACTIONS.md
docs/workflow/README.md
docs/workflow/git_policy.md
docs/workflow/versioning.md
docs/workflow/idea_tree_protocol.md
docs/workflow/module_trial_protocol.md
docs/workflow/experiment_protocol.md
docs/workflow/quality_gate.md
docs/workflow/runbook.md
workflow/openclaw/agent_roles.md
```

然后运行：

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
```

## 执行规则

- 优先使用 `workflow/gtpj_workflow.py` 执行 validate、audit-boundary、目录创建和结果记录等结构性辅助动作。
- 不把 helper 当成研究判断黑盒；Coordinator 仍要判断任务类型、实验语义、质量门和结论边界。
- 不要手工创建临时实验目录。
- 没有 `IDEA-xxxx` 节点时，不要运行模块 trial。
- 质量检查未通过时不要开始正式训练。
- 更新队列前，先把结果写回实验目录。
- 除非 owner 明确要求，否则不要 push。
