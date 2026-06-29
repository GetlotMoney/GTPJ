# Project Status

Date: 2026-06-29

## Current Formal Version

```text
name: GTPJ-v4
code_tag: v4
status: confirmed
dataset: CUB GZSL
baseline_evidence: experiments/v4/baseline/
best_observed_H: 74.47
confirmed_H: 74.45
confirmation_status: confirmed
active_main_update: not_activated
```

`GTPJ-v4` is the current confirmed formal version. It promotes the min3-confirmed
`local-v3-054` tuned v3 configuration: H values `74.46 / 74.42 / 74.47`,
`confirmed_H=74.45`, and `best_observed_H=74.47`.

Promotion creates a formal version/tag. It does not automatically run
`activate-version` or switch current active code aliases.

## Enabled Modules

- Frozen CLIP ViT-L/14@336px backbone
- GPT text description prototypes
- PSE / CLIP-A-self sentence-level text prototype adapter
- FGVD geometry-aware visual memory
- BVSA bidirectional visual-semantic alignment
- ICSA conditional text adaptation
- SGMP auxiliary training

## Formal Result Status

| Experiment | Dataset | Seed | U | S | H | ZS | Status |
|---|---|---:|---:|---:|---:|---:|---|
| `GTPJ-v1` | CUB GZSL | 5 | 72.36 | 75.57 | 73.93 | 81.62 | confirmed |
| `GTPJ-v2` | CUB GZSL | 5 | 71.32 | 77.52 | 74.29 | 81.59 | owner activated, needs confirmation |
| `GTPJ-v3` | CUB GZSL | 5 | 71.22 | 77.60 | 74.27 | 81.38 | owner accepted stochastic, needs confirmation |
| `GTPJ-v4` | CUB GZSL | 5 | 71.54 | 77.61 | 74.45 | 81.30 | confirmed min3 formal version |

## Known Risks

- `GTPJ-v4` is confirmed by min3 repeats, but `activate-version` has not been run.
- `GTPJ-v3` remains preserved as an owner-accepted stochastic tag with `confirmed_H=pending`.
- Future manuscript-grade claims should cite whether a number is `confirmed_H` or `best_observed_H`.

## Next Steps

Use `GTPJ-v4` as the confirmed formal version for future version-level tune,
ablation, and confirmation work. Run `activate-version v4` only if the owner
explicitly wants current runtime aliases switched.
