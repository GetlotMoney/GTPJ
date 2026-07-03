# GTPJ 工作流快速入口

现在的精简入口是：

```text
docs/workflow/START_HERE.md
docs/workflow/WORKFLOW_KERNEL.md
```

本文件只作为 owner 人话短语速查表。

| 用户短语 | 路由 |
|---|---|
| `汇报`, `查状态` | 只读状态检查。除非明确要求，不写 evidence。 |
| `读论文`, `找创新点` | 论文读取 / idea discovery。 |
| `调参` | 调参 Tune。使用 `playbooks/tune.md`。 |
| `消融` | 消融 Ablation。使用 `playbooks/ablation.md`。 |
| `复现`, `确认结果` | 复现确认 Confirmation。使用 `playbooks/confirmation.md`。 |
| `开新模块`, `试这个想法` | 创新 / module trial。使用 `playbooks/innovation.md`。 |
| `升版本` | 升版门 Promotion gate。使用 `playbooks/promotion.md`。 |
| `跑10创新+100调参` | 混合实验 campaign。使用 `playbooks/mixed_campaign.md`。 |
| `全自动研究campaign` | 全自动研究 campaign。使用 `playbooks/autonomous_campaign.md`。 |

正式任务默认 agent 模式：

```yaml
activation_mode: real_multi_agent
agent_instance_mode: temporary_subagent
lifecycle: workflow_scoped
```

长期 agent 是文件支撑的角色身份和累积证据，不等于必须常驻的聊天窗口。

`persistent_thread` 是可选活上下文，适合可见的长周期监控，但不能替代文件、日志、result、quality check 或 Warehouse artifact。

正式写入或运行前，先按 `START_HERE.md` 输出启动摘要；需要正式证据时再填写完整 task card。

baseline 复现状态仍然是硬门。状态比较、best 选择、复现确认、升版、tag/version 表述前，必须运行或记录：

```bash
python workflow/gtpj_workflow.py repro-status --version <vX>
```

启动摘要必须包含 `baseline_repro_status`。除非 `confirmed_H` 和 `confirmation_status` 支持，否则不能把 `best_observed_H` 当成已确认 baseline。
