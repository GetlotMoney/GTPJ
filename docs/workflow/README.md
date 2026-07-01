# GTPJ Workflow

This directory is no longer meant to be read as one large protocol forest.

Daily rule:

```text
Read START_HERE.md
Read WORKFLOW_KERNEL.md
Read WORKFLOW_ROUTER.md only when routing is unclear
Read exactly one relevant playbook
Deep-read reference protocols only when the playbook asks for them
```

## Active Entry Points

| File | Use |
|---|---|
| `START_HERE.md` | Human-facing entry. Start every GTPJ workflow here. |
| `WORKFLOW_KERNEL.md` | Non-negotiable rules: evidence, agents, versioning, retention, safety. |
| `WORKFLOW_ROUTER.md` | Full routing table for ambiguous or mixed requests. |
| `TASK_START_MINI.md` | Short owner-visible start summary. |
| `TASK_START_CARD.md` | Full Coordinator start card for formal runs. |
| `WORKFLOW_FILE_MAP.md` | Explains which files are active, reference, historical, or templates. |

## Playbooks

Use one playbook per requested task type:

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

Playbooks are thin operating cards. They point to older long-form protocols only when the task needs those details.

## Current Simplification Rule

Old detailed files are kept for audit and edge cases. They are not daily required reading.

If two workflow docs conflict, use this order:

```text
current owner instruction
WORKFLOW_KERNEL.md
START_HERE.md
WORKFLOW_ROUTER.md
TASK_START_CARD.md
selected playbook
long-form reference protocol
historical report
```

GitHub remains the canonical workflow source. Local Codex skills are execution mirrors and must be synced after workflow rule changes.
