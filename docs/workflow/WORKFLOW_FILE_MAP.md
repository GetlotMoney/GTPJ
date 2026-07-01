# GTPJ Workflow File Map

This map keeps the workflow readable. It says which files are daily entry points and which are reference material.

## Daily Canonical Files

| File | Status |
|---|---|
| `START_HERE.md` | Start here for every GTPJ workflow task. |
| `WORKFLOW_KERNEL.md` | Hard rules. Keep short and authoritative. |
| `WORKFLOW_ROUTER.md` | Full routing table. Read when task type is ambiguous or mixed. |
| `TASK_START_MINI.md` | Owner-facing compact start summary. |
| `TASK_START_CARD.md` | Full start record for formal writes/runs. |

## Active Playbooks

| File | Status |
|---|---|
| `playbooks/paper_intake.md` | Paper/source/idea discovery operating card. |
| `playbooks/tune.md` | Parameter tuning operating card. |
| `playbooks/ablation.md` | Ablation operating card. |
| `playbooks/confirmation.md` | Reproduce/confirm operating card. |
| `playbooks/innovation.md` | Idea/module-trial operating card. |
| `playbooks/promotion.md` | Promotion operating card. |
| `playbooks/mixed_campaign.md` | Arbitrary mixed experiment campaign card. |
| `playbooks/autonomous_campaign.md` | Long autonomous research campaign card. |

## Reference Protocols

Read these only when the active playbook asks for details:

```text
paper_intake.md
idea_tree_protocol.md
experiment_protocol.md
module_trial_protocol.md
code_interface_contract.md
innovation_code_review_protocol.md
quality_gate.md
promotion.md
ARTIFACT_REGISTRATION.md
agent_orchestration.md
agent_report_policy.md
agents/
mixed_experiment_campaign_protocol.md
autonomous_research_campaign.md
```

## Historical Or Status Files

These preserve decisions, history, diagrams, or implementation state. Do not treat them as the first thing to read.

```text
GTPJ_WORKFLOW_SPEC.md
CURRENT_WORKFLOW_REPORT.md
FIRST_CLOSED_LOOP.md
IMPLEMENTATION_STATUS.md
workflow_diagrams.md
runbook.md
progress_dashboard.md
issues/
```

## Templates And Schemas

Use when writing actual evidence:

```text
experiments/templates/
schemas/
workflow/gtpj_workflow.py
```

## Simplification Rule

If a new workflow rule is important every day, put it in `WORKFLOW_KERNEL.md`.

If it is task-specific, put it in one playbook.

If it is long explanation, evidence, or history, keep it as reference and point to it from a playbook.
