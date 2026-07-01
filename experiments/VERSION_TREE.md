# Version Tree

This file records formal baseline/version relationships. It does not record ordinary tune, ablation, or confirmation experiments.

Core rules:

- Every formal version has an explicit `parent_version`.
- `parent_version` describes the code/config parent, not the ledger parent.
- `main` stores the current active code plus the full global ledger.
- Promotion creates a formal version/tag. It does not automatically run `activate-version`.
- Pure tuning/config-only confirmation does not create a formal `vX`; it stays
  under the parent version as a confirmed config/reference.
- Historical note: tag `v4` exists, but it was a config-only tune confirmation
  and is retained as a legacy/misclassified tag, not counted as a formal
  framework version.

## Current Version Tree

```text
v1
`-- v2 = parent v1 + IDEA-0001/TRIAL-001 CLIP-A-self text prototype adapter
    `-- v3 = parent v2 + IDEA-0002/TRIAL-002 strict conditional FAE-memory JEPA
        |-- CONFIRM-001 = local-v3-054 min3-confirmed tuned config (not a v-version)
        `-- v5 = parent v3 + TRIAL-003 conditional BVSA text active mainline
```

## Version Table

| Version | Parent | Code tag | Ledger source | Change type | Source | Note |
|---|---|---|---|---|---|---|
| `v1` | none | `v1` | initial | initial_baseline | none | First formal baseline. |
| `v2` | `v1` | `v2` | `dev/v1-idea-0001-trial-001-clip-a-self-residual-seenonly@f24a277` | add_module | `trial/v1/idea-0001/trial-001` | CLIP-A-self text prototype adapter; best_observed_H=74.29, confirmed_H=pending. |
| `v3` | `v2` | `v3` | `dev/v2-idea-0002-trial-002-strict-conditional-jepa@875cbb6` | add_module | `trial/v2/idea-0002/trial-002` | Strict conditional FAE-memory JEPA; best_observed_H=74.27, confirmed_H=pending. |
| `v4` | `v3` | `v4` | `exp/v3-confirm-001-local-v3-054-min3@39ff2e7` | legacy_config_tag | `experiments/v3/confirmation/CONFIRM-001_local_v3_054_min3` | Historical config-only tag; not a formal framework version. The confirmed reference is `v3/CONFIRM-001 local-v3-054`, confirmed_H=74.47, repeat mean H=74.45. |
| `v5` | `v3` | `v5` | `main owner activation 2026-06-30` | combo | `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-003_conditional_bvsa_text` | Conditional BVSA text active mainline from `trial003-main100-069`; best_observed_H=74.54, confirmed_H=74.44, active_main_update=activated, strongest confirmed reference is `v3/CONFIRM-001 local-v3-054`. |

## Record Template

When adding a formal version, add a row:

```text
| `vX` | `vParent` | `vX` | `main@<commit>` | add_module / replace_module / remove_module / combo | `<source>` | short note |
```

Also update:

- `experiments/vX/VERSION.md`
- `experiments/EXPERIMENT_REGISTRY.md`
- `config/versions/vX.yaml`
- `docs/PROJECT_STATUS.md`
- `README.md`
