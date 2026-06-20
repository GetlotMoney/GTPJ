# GTPJ-v1

```text
version: v1
baseline_name: GTPJ-v1
status: initialized, pending clean rerun
code_tag: v1
base_version: none
promoted_from: none
config: experiments/v1/config.yaml
```

## Active Modules

- Frozen CLIP ViT-L/14@336px backbone
- GPT text description prototypes
- Text Adapter
- Patch bottleneck / patch selection
- Geometry-aware local visual encoding
- Bidirectional visual-text interaction
- Topology-preserving text constraint
- Conditional text adaptation
- Mutual visual-text branch distillation
- AG-JEPA auxiliary training
- AG-JEPA negative text margin

## Training Policy

- Use strict continuous training.
- Use SGDR-style 20+20+10 staged cosine learning rate with nonzero `eta_min`.
- Do not use test metrics to restart, roll back, stop, or alter training.
- Keep `config.yaml` limited to active v1 fields only.
- Inactive module candidates belong to `idea_tree/`, not to the v1 baseline config.
- Official GTPJ results must be rerun and recorded in this repo.

## Allowed Experiments

- `tune/`
- `ablation/`
- `confirmation/`
