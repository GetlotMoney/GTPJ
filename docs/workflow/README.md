# GTPJ 工作流

本目录不再要求作为一整片协议森林来阅读。

日常规则：

```text
先读 START_HERE.md
再读 WORKFLOW_KERNEL.md
只有路由不清楚时才读 WORKFLOW_ROUTER.md
每次只读一个相关执行卡 playbook
只有 playbook 明确要求时，才深读旧的长协议文件
```

## 当前有效入口

| 文件 | 用途 |
|---|---|
| `START_HERE.md` | 人话入口。每个 GTPJ 工作流任务先从这里开始。 |
| `WORKFLOW_KERNEL.md` | 不可破坏的核心规则：证据、agents、版本、保留策略和安全边界。 |
| `WORKFLOW_ROUTER.md` | 完整路由表。任务类型模糊或混合时再读。 |
| `TASK_START_MINI.md` | 给 owner 看的精简启动摘要。 |
| `TASK_START_CARD.md` | 正式写入或运行前的完整 Coordinator 启动卡。 |
| `WORKFLOW_FILE_MAP.md` | 说明哪些文件是有效入口、参考资料、历史记录或模板。 |

## 执行卡 Playbooks

每种任务只选一个执行卡：

```text
docs/workflow/playbooks/paper_intake.md
docs/workflow/playbooks/tune.md
docs/workflow/playbooks/ablation.md
docs/workflow/playbooks/confirmation.md
docs/workflow/playbooks/innovation.md
docs/workflow/playbooks/promotion.md
docs/workflow/playbooks/mixed_campaign.md
docs/workflow/playbooks/autonomous_campaign.md
```

这些 playbook 是很薄的操作卡，只在任务真的需要细节时才指向旧的长协议。

## 当前简化规则

旧的详细文件保留作审计和边界场景参考，不再作为日常必读。

如果多个工作流文件冲突，按下面优先级处理：

```text
本轮 owner 明确要求
WORKFLOW_KERNEL.md
START_HERE.md
WORKFLOW_ROUTER.md
TASK_START_CARD.md
被选中的 playbook
长协议参考文件
历史报告
```

GitHub 仍然是工作流规范的权威来源。本地 Codex skill 只是执行镜像，工作流规则改变后必须同步。
