# OpenClaw 工作流入口

OpenClaw 是 GTPJ 实验的优先 runtime。

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
docs/workflow/review_gate.md
docs/workflow/runbook.md
workflow/openclaw/agent_roles.md
```

然后运行：

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
```

## 执行规则

- 使用 `workflow/gtpj_workflow.py` 创建 experiment、idea 和 trial 目录。
- 不要手工创建临时实验目录。
- 没有 `IDEA-xxxx` 节点时，不要运行模块 trial。
- review 文件的 decision 不是 `ACCEPTED` 时，不要开始训练。
- 更新队列前，先把结果写回实验目录。
- 除非 owner 明确要求，否则不要 push。
