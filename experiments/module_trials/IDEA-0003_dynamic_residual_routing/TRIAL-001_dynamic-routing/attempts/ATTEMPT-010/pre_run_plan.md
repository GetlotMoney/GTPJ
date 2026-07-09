# ATTEMPT-010 Pre-Run Plan

## 目的

这次只验证四个 `ATTEMPT-009` top 候选是否能在同 seed 下重复出现，不新增方法、不改训练入口、不改变评估语义。

## 运行计划

```text
run_id: RUN-20260705-0001-confirm-dr020-051-041-047-sameseed5x-2gpu
profile: h76-top4-min5-repeat
repeat_type: same_seed_min5_exact_repeat
source_run: RUN-20260704-0002-h76-existing-routing-100-2gpu
source_attempt: ATTEMPT-009
target_attempt: ATTEMPT-010
base_version: v5
seed: 5
gpus: 0,1
jobs: 20
```

## 固定配置

所有 job 固定：

```yaml
use_dynamic_routing: true
dynamic_local_mode: fixed
dynamic_icsa_mode: fixed
dynamic_direction_mode: sample
dynamic_pse_mode: fixed
dynamic_gate_hidden: 48
random_seed: 5
batch_size: 64
planned_train_epochs: 50
lr_stages: [20, 20, 10]
```

四个候选分别固定：

```text
DR-020: weight_s2v=0.525, dynamic_gate_anchor_lambda=0.003
DR-051: weight_s2v=0.545, dynamic_gate_anchor_lambda=0.004
DR-041: weight_s2v=0.515, dynamic_gate_anchor_lambda=0.002
DR-047: weight_s2v=0.535, dynamic_gate_anchor_lambda=0.002
```

## 判定

- `best_hit`：任一 repeat 单次达到或超过来源 H。
- `stable_confirm`：每个候选单独报告 mean/min/max/range；不能只报 best。
- promotion：本轮不自动 promotion。

