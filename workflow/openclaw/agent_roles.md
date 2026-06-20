# OpenClaw Agent Roles

## Coordinator

- Reads repository state and queues.
- Chooses the next valid action.
- Runs `workflow/gtpj_workflow.py validate` before and after structural changes.
- Ensures Git branch, code tag, config, review, logs, and result records align.

## Reader

- Reads long context files: idea tree, workflow docs, experiment records, source notes.
- Summarizes only evidence relevant to the current experiment.

## Implementer

- Implements the minimal code or config change.
- Keeps new modules off by default unless the trial config enables them.
- Records changed files in the trial or experiment README.

## Reviewer

- Performs review according to `docs/workflow/review_gate.md`.
- Returns exactly `ACCEPTED` or `REJECTED`.
- Writes findings into `review.md`.

## Result Analyst

- Parses logs and records U/S/H/ZS, best epoch, seed, command, config, and artifact paths.
- Updates the experiment README and registry.
- Feeds evidence back into `idea_tree/` when a module trial is involved.
