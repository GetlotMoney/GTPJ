# Project Status

Date: 2026-06-20

## Current Baseline

```text
name: GTPJ-v1
code_tag: v1
status: initialized, pending clean rerun
dataset: CUB GZSL
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

## Official Result Status

No result is official until rerun and recorded inside this repo.

Historical reference for the imported first baseline:

| Dataset | Seed | U | S | H | ZS | Status |
|---|---:|---:|---:|---:|---:|---|
| CUB GZSL | 5 | 71.46 | 76.40 | 73.85 | 81.61 | reference only, must rerun |

## Next Step

Run `FINAL-001_clean_v1_seed5` under `experiments/v1/final/` to confirm the first baseline in this clean repository.
