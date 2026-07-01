# GTPJ Workflow Start Here

This is the compact entry for every GTPJ task. It replaces the habit of reading the entire workflow directory.

## 1. Decide The Mode

Use the smallest mode that is still valid:

| Request | Mode |
|---|---|
| Explain, inspect, report status, or list options | `role_only` |
| Start/monitor a real runner, record formal evidence, compare best results, affect next expensive runs, change code/config semantics, or prepare promotion | `real_multi_agent` |
| Debug/smoke that will not count as evidence | `role_only` allowed, but result cannot be kept as formal evidence |

Formal experiment workflows default to:

```yaml
activation_mode: real_multi_agent
agent_instance_mode: temporary_subagent
lifecycle: workflow_scoped
```

Persistent threads are optional visible long-running context. They are not evidence.

## 2. Minimal Read Order

Read only this chain unless the task requires more:

```text
1. START_HERE.md
2. WORKFLOW_KERNEL.md
3. selected playbook under docs/workflow/playbooks/
4. WORKFLOW_ROUTER.md only if routing is ambiguous or mixed
5. TASK_START_MINI.md before reporting the start summary
6. TASK_START_CARD.md before formal writes/runs
```

Do not deep-read every old protocol by default.

## 3. Owner Phrase Routing

| Owner says | Default route | Playbook |
|---|---|---|
| `汇报`, `查状态`, `现在怎么样` | read-only status | none, use `WORKFLOW_KERNEL.md` |
| `读论文`, `找创新点` | paper intake / idea discovery | `playbooks/paper_intake.md` |
| `调参` | tune | `playbooks/tune.md` |
| `消融` | ablation | `playbooks/ablation.md` |
| `复现`, `确认这个结果` | confirmation | `playbooks/confirmation.md` |
| `开新模块`, `试这个想法` | innovation / module trial | `playbooks/innovation.md` |
| `升版本` | promotion | `playbooks/promotion.md` |
| `跑10创新+100调参` or any mixed count | mixed experiment campaign | `playbooks/mixed_campaign.md` |
| `全自动研究campaign`, `从论文到最终结果都接管` | autonomous research campaign | `playbooks/autonomous_campaign.md` |

## 4. Start Summary

Before editing files, running experiments, recording results, or selecting best, report:

```text
能不能开工：
任务类型：
基于版本/分支：
是否进入 idea_tree：
GitHub 写入：
Research/Warehouse 写入：
agents 模式：
必须读的 playbook：
硬门：
当前阻塞：
下一步最小动作：
```

For a pure status/report request, keep this summary short.

## 5. Evidence First

Never let chat memory become official evidence.

Official evidence lives in:

```text
manifest.yaml
result.yaml
result.md
quality_check.md
agent_summary.md
ATTEMPTS.md
batch_status.json
Warehouse logs/checkpoints/receipts
Research source notes when needed
```

If a conclusion affects keep/drop/best/repeat/promotion/versioning or the next high-cost run, it must be traceable to files or artifacts.
