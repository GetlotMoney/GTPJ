# Codex Workflow Entrypoint

Codex follows the same repository workflow as OpenClaw.

## Startup Contract

Before modifying files, read:

```text
AGENTS.md
docs/workflow/README.md
workflow/README.md
```

Then run:

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
```

## Codex Duties

- Use `workflow/gtpj_workflow.py` for structural workflow actions.
- Keep edits minimal and scoped.
- Do not migrate old branch names, old experiment IDs, old video files, or old external-tool workflow files.
- Do not push unless the owner explicitly asks.
- Prefer OpenClaw for experiment execution when both runtimes are available.
