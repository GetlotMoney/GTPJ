# GTPJ Workflow Quick Start

The compact entry is now:

```text
docs/workflow/START_HERE.md
docs/workflow/WORKFLOW_KERNEL.md
```

Use this file only as a short owner phrase cheat sheet.

| Owner phrase | Route |
|---|---|
| `汇报`, `查状态` | Read-only status. Do not write evidence unless asked. |
| `读论文`, `找创新点` | Paper intake / idea discovery. |
| `调参` | Tune. Use `playbooks/tune.md`. |
| `消融` | Ablation. Use `playbooks/ablation.md`. |
| `复现`, `确认结果` | Confirmation. Use `playbooks/confirmation.md`. |
| `开新模块`, `试这个想法` | Innovation / module trial. Use `playbooks/innovation.md`. |
| `升版本` | Promotion gate. Use `playbooks/promotion.md`. |
| `跑10创新+100调参` | Mixed campaign. Use `playbooks/mixed_campaign.md`. |
| `全自动研究campaign` | Autonomous campaign. Use `playbooks/autonomous_campaign.md`. |

Default formal agent mode:

```yaml
activation_mode: real_multi_agent
agent_instance_mode: temporary_subagent
lifecycle: workflow_scoped
```

Long-term agents are file-backed role identities and accumulated evidence, not mandatory permanent chat windows.

Persistent threads are optional live context for visible long-running monitoring. They do not replace files, logs, results, quality checks, or Warehouse artifacts.

Before formal writes or runs, produce the `START_HERE.md` start summary and then fill the full task card when needed.

Baseline reproducibility remains a hard gate. Before status comparison, best selection, confirmation, promotion, or tag/version claims, run or record:

```bash
python workflow/gtpj_workflow.py repro-status --version <vX>
```

The start summary must include `baseline_repro_status`. Do not treat `best_observed_H` as a confirmed baseline unless `confirmed_H` and `confirmation_status` support it.
