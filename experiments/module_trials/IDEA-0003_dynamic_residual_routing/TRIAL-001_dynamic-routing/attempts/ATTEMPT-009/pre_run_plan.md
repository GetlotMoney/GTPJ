# Pre-run Plan: ATTEMPT-009

attempt_id: `ATTEMPT-009`
run_id: `RUN-20260704-0002-h76-existing-routing-100-2gpu`
profile: `h76-existing-routing-100`
result_type: `trial_internal_score_search`

## Schedule

```text
Config epochs field: 30
Planned train epochs: 50
Epoch schedule source: lr_stages
LR stages: 20 + 20 + 10
batch_size: 64
seed: 5
```

## Target

在已有 dynamic routing 框架内做 100 个调参/路由组合实验，目标是寻找向稳定 `GZSL-H=76.00` 推进的候选。

## Scope

允许：

- `direction_gate` 的 sample/class/fixed 相关配置。
- `local_gate` 低权重 sample/class 探针。
- `pse_gate=class` 或 fixed。
- 少量 guarded low-ratio ICSA probe。
- `direction + local`、`direction + PSE`、`direction + local + PSE` 组合。

禁止：

- 改 CUB split、class order、label mapping、metric semantics。
- 使用 `dynamic_pse_mode=sample`。
- 把单次高分写成 confirmed。
- 因纯调参直接开新 `vX`。

## Decision Rule

单次 `H>=74.75` 且 U/S 无明显塌陷的候选进入后续 min3。只有 repeat 证据通过后，才能升级为 confirmed candidate。
