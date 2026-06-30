# GTPJ

## Current Active Version

```text
name: GTPJ-v5
code_tag: v5
status: owner_activated_provisional
best_observed_H: 74.54
confirmed_H: 74.44
source: TRIAL-003 main100 trial003-main100-069
active_main_update: activated
future_tuning_base: config/versions/v5.yaml
```

`GTPJ-v5` is the active mainline selected by the owner on 2026-06-30. It activates the TRIAL-003 conditional BVSA text path, so `all_text_cond [B, C, 768]` enters BVSA, including the cross/local_score branch.

The stronger confirmed reference remains `GTPJ-v4 / tag v4 / confirmed_H=74.45`. v5 is active for the next tuning round, but its frozen-repeat mean is `74.44`, so it is not a stronger confirmed-baseline claim over v4.

## Versions

| Version | Code tag | Status | Dataset | Note |
|---|---|---|---|---|
| `GTPJ-v1` | `v1` | confirmed | CUB GZSL | First formal baseline, seed=5, H=73.93. |
| `GTPJ-v2` | `v2` | owner activated, needs confirmation | CUB GZSL | CLIP-A-self text prototype adapter, best_observed_H=74.29. |
| `GTPJ-v3` | `v3` | owner accepted stochastic, needs confirmation | CUB GZSL | Strict conditional FAE-memory JEPA, best_observed_H=74.27. |
| `GTPJ-v4` | `v4` | confirmed formal reference | CUB GZSL | min3-confirmed `local-v3-054`, confirmed_H=74.45, best_observed_H=74.47. |
| `GTPJ-v5` | `v5` | owner activated provisional active mainline | CUB GZSL | TRIAL-003 conditional BVSA text, best_observed_H=74.54, repeat mean H=74.44. |

Version tree:

```text
v1
`-- v2 = parent v1 + IDEA-0001/TRIAL-001 CLIP-A-self / PSE
    `-- v3 = parent v2 + IDEA-0002/TRIAL-002 strict conditional FAE-memory JEPA
        `-- v4 = parent v3 + local-v3-054 min3-confirmed tuned config
            `-- v5 = parent v4 + TRIAL-003 conditional BVSA text active mainline
```

`main` stores the current active code plus all historical governance ledgers. `v1` to `v5` are Git tags, not long-running branches.

## Current Mainline Config

```text
config/GTPJ_cub_gzsl.yaml -> identical to config/versions/v5.yaml
```

Key v5 parameters:

```text
bvsa_text_mode: conditional
sgmp_text_mode: conditional
jepa_text_mode: conditional
pse_outer_ratio: 0.65
clip_a_self_outer_ratio: 0.65
local_weight: 0.2
```

Default CUB run:

```bash
conda run -n dvsr_gpu python train_GTPJ_CUB.py --config config/versions/v5.yaml
```

## Repository Layout

```text
model/                  model code
tools/                  dataset, feature, and evaluation helpers
config/versions/        frozen version configs
experiments/            lightweight version and trial ledgers
docs/                   governance, workflow, and project status
workflow/               structural helper CLI
idea_tree/              idea source and version applicability records
```

Large datasets, raw logs, receipts, checkpoints, generated figures, and feature caches stay outside GitHub in Warehouse or local runtime storage.

## Governance Commands

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py audit-boundary
python workflow/gtpj_workflow.py validate-remote
```

Priority docs:

- `docs/PROJECT_STATUS.md`
- `experiments/v5/VERSION.md`
- `experiments/VERSION_TREE.md`
- `experiments/EXPERIMENT_REGISTRY.md`
- `docs/workflow/README.md`
- `docs/workflow/runbook.md`
