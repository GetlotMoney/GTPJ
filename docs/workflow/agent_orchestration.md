# Agent 编排和长期管理

GitHub 保存长期规则和 agent IO 契约。本地 `gtpj-workflow` skill 保存执行入口。
两边规则必须同步。

## 核心结构

长期 agent 管理采用两层结构：

```text
docs/workflow/agents/
|-- shared_roles/
`-- by_experiment/
```

`shared_roles/` 只定义 agent 的长期身份、自我介绍、权限、读写边界、输出和失败条件。

`by_experiment/` 只定义某类实验如何调用这些共享角色，不重复定义角色本身。

这样可以同时满足两个目标：

- 每个实验类型都有独立 agents 文件夹，层次清楚；
- Coordinator、Runner、Quality Checker 等共享角色只写一份，避免规则漂移。

## GitHub 权威目录

```text
docs/workflow/agents/
|-- README.md
|-- shared_roles/
|   |-- coordinator/profile.md
|   |-- reader_planner/profile.md
|   |-- runner/profile.md
|   |-- implementer/profile.md
|   |-- interface_checker/profile.md
|   |-- quality_checker/profile.md
|   |-- log_analyst/profile.md
|   |-- result_analyst/profile.md
|   `-- reviewer/profile.md
`-- by_experiment/
    |-- tune/agents/README.md
    |-- ablation/agents/README.md
    |-- innovation/agents/README.md
    |-- confirmation/agents/README.md
    `-- promotion/agents/README.md
```

## 本地 Skill 镜像目录

本地 skill 必须镜像 GitHub 权威目录：

```text
C:\Users\Administrator\.codex\skills\gtpj-workflow\references\agents/
|-- README.md
|-- shared_roles/
`-- by_experiment/
```

如果 GitHub 文档和本地 skill 冲突，以 GitHub 文档为准。

## 角色长期，实例临时

长期保存的是角色说明、读写边界、检查清单和交接格式。每次实验启动的 agent 实例可以是临时的，
但必须按照长期角色文件工作。

新边界下，GitHub 只保存轻量 config / manifest / result / version ledger。Runner 写
Warehouse，Reader / Planner 读 Research，Result Analyst 通过 artifact id 引用结果。
任何 agent 都不能把 raw logs、checkpoint、generated figures、完整论文笔记或完整创意树写入 GitHub。

## Agent 工作凭证

真实实验必须保存 agent 工作凭证，而不是保存完整聊天流水。最小 GitHub 记录是：

```text
agent_summary.md
```

它记录参与 agents、禁用 agents、输入、检查范围、发现、结论和证据引用。长报告、完整
日志分析、runner 细节和大型审查材料放入 Warehouse，并在 `agent_summary.md` 里引用
artifact id。具体规则见：

```text
docs/workflow/agent_report_policy.md
```

## 四类实验编排

调参：

```text
Coordinator -> Reader/Planner -> 用户选择 -> Runner -> Log Analyst + Quality Checker -> Coordinator
```

消融：

```text
Coordinator -> Reader/Planner -> Implementer -> Interface Checker -> Runner -> Log Analyst + Quality Checker + Result Analyst -> Coordinator
```

创新：

```text
Coordinator -> Reader/Planner -> Implementer -> Interface Checker -> Runner -> Quality Checker + Result Analyst + Reviewer -> Coordinator
```

重新复现：

```text
Coordinator -> Runner -> Log Analyst + Quality Checker -> Coordinator
```

Promotion：

```text
Coordinator -> Quality Checker + Interface Checker + Result Analyst -> Coordinator
```

## 禁止事项

- 多个 agents 同时写同一个 `INDEX.md`。
- 多个 agents 同时改同一实验代码路径。
- Runner 并行抢同一块 GPU。
- 非 Coordinator 删除分支、合并分支、创建 tag。
- 非用户明确要求时 push 到 GitHub。

## 进度看板联动

真实实验运行时，Coordinator 负责按 `docs/workflow/progress_dashboard.md` 创建和更新：

```text
.gtpj_runtime/runs/<run_id>/status.json
.gtpj_runtime/runs/<run_id>/events.jsonl
```

各 agent 在关键阶段向 Coordinator 汇报状态；Coordinator 收口写入 runtime 状态。
网页看板只读这些状态和 GitHub 账本，不直接启动训练、删除分支、打 tag、执行 promotion 或 push。

## 同步规则

修改 workflow agent 规范时：

1. 先更新 `docs/workflow/agents/` 和本文件。
2. 如果影响 agent 工作凭证，同步更新 `docs/workflow/agent_report_policy.md` 和模板。
3. 同步更新本地 `gtpj-workflow` skill 的 `references/agents/` 与相关 reference 文件。
4. 运行 skill 校验。
5. 运行仓库验证。
6. 提交 GitHub 文档；只有 owner 明确要求时才 push。
