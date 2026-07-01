# Project Status

Date: 2026-06-30

## Current Active Mainline

```text
name: GTPJ-v5
code_tag: v5
status: owner_activated_provisional
dataset: CUB GZSL
baseline_evidence: experiments/v5/baseline/
best_observed_H: 74.54
confirmed_H: 74.44
confirmation_status: owner_activated_provisional
active_main_update: activated
future_tuning_base: config/versions/v5.yaml
```

`GTPJ-v5` is the owner-selected active mainline. It activates TRIAL-003 so that `all_text_cond` enters BVSA, including the cross/local_score branch, and freezes the best source configuration from the 100-run batch:

```text
source_run: RUN-20260630-0002-trial003-main100-2gpu
source_candidate: trial003-main100-069
pse_outer_ratio: 0.65
clip_a_self_outer_ratio: 0.65
local_weight: 0.2
```

## Confirmed Reference

```text
name: v3 CONFIRM-001 local-v3-054
code_tag: v3
status: confirmed_config
confirmed_H: 74.47
best_observed_H: 74.47
H_mean: 74.45
historical_tag: v4 (legacy config-only tag; not a formal framework version)
```

`v3/CONFIRM-001 local-v3-054` remains the stronger confirmed reference because its min3 cluster passed and the formal confirmed H is `74.47`; its repeat mean is `74.45`, while the v5 frozen-repeat mean is `74.44`. `GTPJ-v5` is active because the owner explicitly selected it as the next mainline for tuning, not because it supersedes the confirmed v3 config.

## Enabled Modules

- Frozen CLIP ViT-L/14@336px backbone
- GPT text description prototypes
- PSE / CLIP-A-self sentence-level text prototype adapter
- FGVD geometry-aware visual memory
- BVSA bidirectional visual-semantic alignment
- ICSA conditional text adaptation
- SGMP auxiliary training
- Conditional BVSA text routing: `all_text_cond [B, C, 768] -> BVSA cross/local_score`

## Formal Result Status

| Experiment | Dataset | Seed | U | S | H | ZS | Status |
|---|---|---:|---:|---:|---:|---:|---|
| `GTPJ-v1` | CUB GZSL | 5 | 72.36 | 75.57 | 73.93 | 81.62 | confirmed |
| `GTPJ-v2` | CUB GZSL | 5 | 71.32 | 77.52 | 74.29 | 81.59 | owner activated, needs confirmation |
| `GTPJ-v3` | CUB GZSL | 5 | 71.22 | 77.60 | 74.27 | 81.38 | owner accepted stochastic, needs confirmation |
| `v3 CONFIRM-001 local-v3-054` | CUB GZSL | 5 | 71.53 | 77.66 | 74.47 | 81.25 | confirmed config under v3; H_mean=74.45 |
| `GTPJ-v5` | CUB GZSL | 5 | 72.00 | 77.07 | 74.44 | 81.56 | owner activated provisional active mainline |

## Known Risks

- `GTPJ-v5` has a best single repeat of `H=74.54`, but its 5-repeat mean is `H=74.44`, below the confirmed v3 config `confirmed_H=74.47`.
- Future manuscript-grade claims should cite whether a number is `confirmed_H`, repeat mean, or `best_observed_H`.
- The next tuning round should start from `config/versions/v5.yaml` but still compare against `v3/CONFIRM-001 local-v3-054 confirmed_H=74.47`.

## Warehouse Retention

2026-06-29 checkpoint retention has been applied on `lab4090`:

```text
manifest: /data/lby/projects/cv_project/GTPJ_Warehouse/retention/model_best_retention_20260629_v4.json
policy: keep Top-5 best model_best/best-model checkpoints by H
kept: 5
deleted: 199 training checkpoint files
deleted_bytes: 31055128358
excluded: logs, receipts, summaries, configs, manifests, registries, and data/cache feature tensors
```

## Next Steps

Use `GTPJ-v5` as the active base for future tune, ablation, and confirmation work. Treat `v3/CONFIRM-001 local-v3-054 confirmed_H=74.47` as the reference that the next v5-derived candidate must beat by repeat evidence.
