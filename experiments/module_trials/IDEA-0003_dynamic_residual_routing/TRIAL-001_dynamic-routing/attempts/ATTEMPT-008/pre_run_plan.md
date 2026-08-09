# Pre-run Plan: ATTEMPT-008

attempt_id: `ATTEMPT-008`
run_id: `RUN-20260704-0001-dr035-min6-confirm-s5-2gpu`
profile: `dr035-min6-confirm`
repeat_type: `same_seed_min6_exact_repeat`

## Target

复现 `ATTEMPT-004 / DR-035 / direction_sample_h48_w0.525_a0.005`，并把 `ATTEMPT-007` 的 min3 exact repeat 扩展到 min6。

## Frozen Config

```text
base_version: v5
base_code_tag: v5
seed: 5
batch_size: 64
Config epochs field: 30
Planned train epochs: 50
Epoch schedule source: lr_stages
LR stages: 20 + 20 + 10
use_dynamic_routing: true
dynamic_local_mode: fixed
dynamic_icsa_mode: fixed
dynamic_direction_mode: sample
dynamic_pse_mode: fixed
dynamic_gate_hidden: 48
dynamic_gate_anchor_lambda: 0.005
weight_s2v: 0.525
```

## Decision Rule

必须报告六次的 mean/min/max/range。即使出现单次接近或超过 75.02，也不能隐藏较弱 repeat。
