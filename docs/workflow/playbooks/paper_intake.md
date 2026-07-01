# Playbook: Paper Intake / Idea Discovery

Use when the owner asks to read papers, process sources, or extract innovation ideas.

## Read

```text
START_HERE.md
WORKFLOW_KERNEL.md
paper_intake.md
idea_tree_protocol.md
```

## Agents

Default: `Reader/Planner`, `Source Reviewer`, `Coordinator`.

Use `real_multi_agent` if the output affects formal idea selection, a module trial, baseline claims, or paper experiment planning.

## Outputs

Long-form evidence goes to `GTPJ_Research`.

Lightweight GitHub records go to:

```text
idea_tree/sources/
idea_tree/inbox.md
idea_tree/ideas/<IDEA-ID>/
idea_tree/idea_tree.json
idea_tree/versions/<vX>.md
```

## Stop Gates

- No verified source or accepted local heuristic.
- Missing hypothesis, implementation scope, or risk.
- Idea is not tied to the active version view.
- Owner asked only for reading, not experiment execution.
