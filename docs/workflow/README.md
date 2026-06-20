# Workflow Overview

GTPJ uses a version-first experiment workflow.

```text
idea_tree
  -> module_trials
  -> promoted baseline vX
  -> tune / ablation / final under experiments/vX
```

Core rule:

```text
one vX = one baseline = one Git tag = one version experiment directory
```

Runtime rule:

- OpenClaw is preferred for running experiments.
- Codex follows the same files and can perform the same workflow.
- The repository files are the source of truth for both runtimes.
- Structural actions must go through `workflow/gtpj_workflow.py`.

Read in this order:

1. `git_policy.md`
2. `versioning.md`
3. `idea_tree_protocol.md`
4. `module_trial_protocol.md`
5. `experiment_protocol.md`
6. `review_gate.md`
7. `runbook.md`
8. `workflow/README.md`
