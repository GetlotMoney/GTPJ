# GTPJ

GeoTopoPatch-JEPA for generalized zero-shot learning.

GTPJ is a clean experiment repository for the first official baseline, `GTPJ-v1`.
It starts from the current accepted framework only: frozen CLIP, GPT text
descriptions, patch bottleneck, geometry-aware local encoding, topology-preserving
text constraint, conditional text adaptation, mutual visual-text branch
distillation, and AG-JEPA auxiliary training.

## Current Version

| Version | Code tag | Status | Main dataset | Notes |
|---|---|---|---|---|
| `GTPJ-v1` | `v1` | initialized | CUB GZSL | Needs a clean rerun in this repo before becoming an official reported result. |

## Project Layout

```text
GTPJ/
├── model/                 # model code
├── tools/                 # data, feature, evaluation utilities
├── config/
│   └── versions/v1.yaml   # fixed GTPJ-v1 config
├── docs/workflow/         # GitHub and experiment workflow rules
├── idea_tree/             # strict idea source and queues
└── experiments/
    ├── module_trials/     # code-backed module trials
    └── v1/                # GTPJ-v1 tune / ablation / final records
```

## Workflow Rule

One version is one baseline:

```text
v1 = GTPJ-v1 = one code snapshot = one Git tag = one version experiment directory
```

Module ideas do not immediately become `v2`, `v3`, or `v4`. They first go through
`idea_tree/` and `experiments/module_trials/`. Only a successful, reviewed trial is
promoted into a new baseline version.

## Runtime Preference

OpenClaw is the preferred runtime for experiments. Codex must follow the same
repo files and produce the same records, so both runtimes can work on the same
baseline without inventing separate rules.

Start here:

- `docs/PROJECT_STATUS.md`
- `docs/workflow/README.md`
- `experiments/v1/VERSION.md`
- `idea_tree/README.md`
