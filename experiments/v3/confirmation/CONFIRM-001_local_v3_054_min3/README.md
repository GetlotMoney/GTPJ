# CONFIRM-001 local-v3-054 min3 confirmation

```text
experiment_id: CONFIRM-001
experiment_name: CONFIRM-001_local_v3_054_min3
kind: confirmation
version: v3
base_code_tag: v3
branch_source: tag v3 / frozen server worktree v3_baseline_13529cb
code_branch: exp/v3-confirm-001-local-v3-054-min3
run_commit: 13529cb1d3ed8405e2f5cbb4832eff8d1c78db16
ledger_commit_base: 4b259379d99c1a791442ea9e2fac0bb22b2411a9
dirty_state: server worktree clean; ledger branch records result only
config: config.yaml
command: /data/lby/.conda/envs/dvsr_gpu/bin/python -u train_GTPJ_CUB.py --config <warehouse config>
seed: 5
python_env: /data/lby/.conda/envs/dvsr_gpu
torch_cuda: torch 2.5.1 / CUDA available / NVIDIA GeForce RTX 4090
dataset_split: standard_v1
class_order_id: standard_v1
label_mapping_id: standard_v1
metric_contract_id: gzsl_u_s_h_zs_v1
warehouse_run: RUN-20260629-1722-server-gpu0-local-top2-min3
warehouse_base: /data/lby/projects/cv_project/GTPJ_Warehouse/runs/v3/confirmation/RUN-20260629-1722-server-gpu0-local-top2-min3
warehouse_registry: /data/lby/projects/cv_project/GTPJ_Warehouse/ARTIFACT_REGISTRY.yaml
warehouse_registry_sha256: 61b35ba5774b963b4b61af90705c1504dcdc2dffdbf80b4bca2dd6be7ae2947d
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
agent_summary: agent_summary.md
quality_check: quality_check.md
attempt_id: attempt-001
decision: confirmed_config
promotion_decision: confirmed_config_only
promote_to:
evidence_level: baseline_grade
result_status: confirmed
best_observed_H: 74.47
confirmed_H: 74.47
H_mean: 74.45
confirmation_target: local-v3-054
confirmation_tolerance_H: min3 clean server repeats, no tolerance override
confirmation_status: confirmed
status: confirmed_config
```

## Question

Does the local search candidate `local-v3-054` remain above the v3 accepted-but-unconfirmed reference (`H=74.27`) when replayed on the server at least three times with the same configuration?

## Configuration Delta

The confirmation uses the v3 baseline model/training code and changes only the selected config hyperparameters from the local exploration source:

| Key | v3 value | confirmed value |
|---|---:|---:|
| `pse_outer_ratio` / `clip_a_self_outer_ratio` | 0.15 | 0.5 |
| `local_weight` | 0.3 | 0.1 |

All model/training framework semantics remain the v3 frozen implementation: PSE, ICSA, FGVD, BVSA, and SGMP, with `all_text_cond` entering BVSA through `bvsa_text_mode: conditional`. This is therefore a confirmed config under `v3`, not a new formal framework version.

## Server Repeats

| Run | U | S | H | ZS | Best epoch | Receipt artifact | Training log artifact |
|---|---:|---:|---:|---:|---:|---|---|
| `local-v3-054-rep01` | 71.56 | 77.60 | 74.46 | 81.41 | 34 | `receipt:v3:confirmation:CONFIRM-001:local-v3-054-rep01` | `log:v3:confirmation:CONFIRM-001:local-v3-054-rep01` |
| `local-v3-054-rep02` | 71.53 | 77.56 | 74.42 | 81.25 | 34 | `receipt:v3:confirmation:CONFIRM-001:local-v3-054-rep02` | `log:v3:confirmation:CONFIRM-001:local-v3-054-rep02` |
| `local-v3-054-rep03` | 71.53 | 77.66 | 74.47 | 81.25 | 34 | `receipt:v3:confirmation:CONFIRM-001:local-v3-054-rep03` | `log:v3:confirmation:CONFIRM-001:local-v3-054-rep03` |

Summary:

| Metric | Value |
|---|---:|
| `U_mean` | 71.54 |
| `S_mean` | 77.61 |
| `confirmed_H` / official H | 74.47 |
| `H_mean` | 74.45 |
| `H_min` | 74.42 |
| `H_max` / `best_observed_H` | 74.47 |
| `ZS_mean` | 81.30 |
| `delta_H_vs_74.27_mean` | +0.18 |
| `delta_H_vs_74.27_best` | +0.20 |

## Related Candidates

| Candidate | Source H | Server min3 H values | Outcome |
|---|---:|---|---|
| `local-v3-022` | 74.45 | 73.91 / 73.86 / 73.86 | not reproduced |
| `trial003-tune-026` | 74.40 | 74.29 / 73.94 / 73.95 | not confirmed as stable |
| `local-v3-054` | 74.41 | 74.46 / 74.42 / 74.47 | confirmed |

## Decision

`local-v3-054` is accepted as a confirmed config under `GTPJ-v3`. Because the min3 cluster passed, the confirmed result uses the highest successful repeat (`rep03`, H=74.47) as `confirmed_H`, while the mean (`H_mean=74.45`) remains stability evidence. Under the current version rule, pure tuning/config-only confirmation does not create a new formal `vX`; the historical `v4` tag is retained only as a legacy record.
