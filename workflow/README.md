# GTPJ Executable Workflow

This directory contains the executable workflow layer for GTPJ.

The repository-level rules live in `docs/workflow/`. This directory turns those
rules into repeatable commands and runtime entrypoints for OpenClaw and Codex.
Use `NEXT_ACTIONS.md` as the current execution window.

## Quick Commands

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py new-experiment --version v1 --kind confirmation --exp-id CONFIRM-001 --slug clean_seed5
python workflow/gtpj_workflow.py new-experiment --version v1 --kind tune --exp-id TUNE-001 --slug topo008
python workflow/gtpj_workflow.py new-idea --idea-id IDEA-0001 --slug attribute_router --title "attribute router" --source-type user --source-status unknown --base-version v1 --global-score 50 --version-score 50 --applicability direct
python workflow/gtpj_workflow.py set-current-version --version v1
python workflow/gtpj_workflow.py new-trial --idea-id IDEA-0001 --trial-id TRIAL-001 --slug basic_router --base-version v1
```

## Runtime Entrypoints

- `openclaw/README.md`: OpenClaw-first execution rules.
- `codex/README.md`: Codex-compatible execution rules.

Both runtimes must use the same repository files, templates, and CLI checks.
