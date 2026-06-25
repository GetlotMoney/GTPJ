# GTPJ-v1 Baseline

```text
version: v1
code_tag: v1
baseline_name: GTPJ-v1
dataset: CUB GZSL
seed: 5
config: config.yaml
log_artifact_id: log:legacy:v1_baseline:GTPJ-v1_CUB_seed5_20260613-145232
log_uri: warehouse://logs/legacy/v1_baseline/GTPJ-v1_CUB_seed5_20260613-145232.txt
log_sha256: 850a01a5c1500f75fef3d9729b8e89b47c78aa40203792341b03515ddc5edfb9
log_size_bytes: 139148
status: accepted
```

## Purpose

This directory records the first accepted baseline evidence for `GTPJ-v1`. It is not a tuning experiment directory.

## Key Configuration

| Parameter | Value |
|---|---:|
| `conditional_text_ratio` | 0.008 |

Training schedule:

```text
stage 1: lr=0.001, epochs=20, eta_min=1e-5
stage 2: lr=0.0001, epochs=20, eta_min=1e-6, restart_from_best=False
stage 3: lr=0.00001, epochs=10, eta_min=1e-7, restart_from_best=False
total_epochs: 50
```

## Result

| Dataset | Seed | U | S | H | ZS | Best epoch | Log artifact |
|---|---:|---:|---:|---:|---:|---:|---|
| CUB GZSL | 5 | 72.36 | 75.57 | 73.93 | 81.62 | 26 | `warehouse://logs/legacy/v1_baseline/GTPJ-v1_CUB_seed5_20260613-145232.txt` |

## Conclusion

The accepted CUB seed=5 baseline for `GTPJ-v1` is `H=73.93`. Future module trials, tuning, ablations, and cross-dataset experiments use this version configuration and result as the first comparison point.
