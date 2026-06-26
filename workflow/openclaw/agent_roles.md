# OpenClaw Agent 角色

OpenClaw agent 必须遵循 GTPJ 核心 workflow。以下角色分工是 OpenClaw runtime 接入
`docs/workflow/agents/` 长期角色体系时的实现参考；如有冲突，以 GitHub workflow 规范和
`docs/workflow/agent_orchestration.md` 为准。

## Coordinator

- 读取仓库状态和队列。
- 选择下一个合法动作。
- 在结构性改动前后运行 `workflow/gtpj_workflow.py validate`。
- 确保 Git 分支、代码 tag、配置、quality_check、日志和结果记录一致。

## Reader

- 读取长上下文文件：创意树、workflow 文档、实验记录、来源说明。
- 只总结与当前实验相关的证据。

## Implementer

- 实现最小代码改动或配置改动。
- 除非 trial 配置启用，否则新模块默认关闭。
- 在 trial 或实验 README 中记录改动文件。

## 质量检查者

- 按 `docs/workflow/quality_gate.md` 执行质量检查。
- 可以继续使用 `ACCEPTED` 或 `REJECTED` 作为运行时结论标签，但必须映射到 GitHub 账本中的正式决策。
- 把发现写入 `quality_check.md`。

## Result Analyst

- 解析日志并记录 U/S/H/ZS、best epoch、seed、命令、配置和产物路径。
- 更新实验 README 和 registry。
- 如果涉及模块 trial，把证据反馈回 `idea_tree/`。
