# Quality Check

```text
runtime: local archive
decision: ACCEPTED
```

## Scope

- Confirm `GTPJ-v1` as the first accepted baseline configuration.
- Confirm the baseline uses `conditional_text_ratio=0.008`.
- Do not modify model code, training scripts, dataset splits, evaluation logic, or loss structure.

## Findings

- Task path: CUB GZSL, seed=5.
- Training schedule: SGDR 20+20+10; all three stages use non-zero `eta_min`; stages 2 and 3 use `restart_from_best=False`.
- Result: U=72.36, S=75.57, H=73.93, ZS=81.62, best epoch=26.
- Config snapshot: `experiments/v1/baseline/config.yaml`.
- Raw log artifact:
  - `artifact_id: log:legacy:v1_baseline:GTPJ-v1_CUB_seed5_20260613-145232`
  - `artifact_uri: warehouse://logs/legacy/v1_baseline/GTPJ-v1_CUB_seed5_20260613-145232.txt`
  - `sha256: 850a01a5c1500f75fef3d9729b8e89b47c78aa40203792341b03515ddc5edfb9`
  - `size_bytes: 139148`

## Decision

ACCEPTED
