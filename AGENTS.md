# GTPJ Agent Rules

## Communication

- Default to Chinese when working with the owner.
- Start with the conclusion, then give the key reasons.
- For complex work, give a short plan before editing.
- State uncertainty and risks directly.

## Repository Rules

- `main` is the only long-lived branch.
- `v1`, `v2`, `v3` are permanent baseline tags.
- Trial code snapshots use tags such as `trial/idea-0001/trial-001`.
- Use `workflow/gtpj_workflow.py` for status checks and new workflow records.
- Do not create controller branches.
- Do not migrate old experiment IDs, old branches, old PRs, or old workflow files.
- Do not push unless the owner explicitly asks for push.

## Experiment Rules

- OpenClaw is the preferred runtime; Codex is compatible and must follow the same files.
- Every new module trial must start from an `idea_tree` node.
- No `idea_id`, no `dev/idea-*` branch.
- Every trial must record implementation, config, review, result, and code tag.
- Tune, ablation, and final runs belong under a concrete version directory, such as `experiments/v1/`.

## Safety

- Do not commit datasets, checkpoints, raw caches, secrets, or large logs.
- Do not use training/test feedback to change training behavior mid-run.
- Do not hide failed experiments; record them as evidence.
