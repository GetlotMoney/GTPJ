# OpenClaw Workflow Entrypoint

OpenClaw is the preferred runtime for GTPJ experiments.

## Startup Contract

Before choosing or running an experiment, read:

```text
AGENTS.md
NEXT_ACTIONS.md
docs/workflow/README.md
docs/workflow/git_policy.md
docs/workflow/versioning.md
docs/workflow/idea_tree_protocol.md
docs/workflow/module_trial_protocol.md
docs/workflow/experiment_protocol.md
docs/workflow/review_gate.md
docs/workflow/runbook.md
workflow/openclaw/agent_roles.md
```

Then run:

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
```

## Execution Rules

- Use `workflow/gtpj_workflow.py` to create experiment, idea, and trial folders.
- Do not create ad hoc experiment directories by hand.
- Do not run a module trial unless it has an `IDEA-xxxx` node.
- Do not run training until the review file decision is `ACCEPTED`.
- Write results back to the experiment folder before updating queues.
- Do not push unless the owner explicitly asks.
