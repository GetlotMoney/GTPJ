# ATTEMPT-012 Pre-run Plan

## 目标

本轮接在 ATTEMPT-011 的 200 组服务器离线搜索之后，做 50 个多 seed 稳定性确认 job。它不再继续大范围搜索，而是围绕已经收敛出的 `direction_sample / h48 / w≈0.515-0.555 / 小 anchor` 热点，检查不同随机种子下是否稳定。

## 实验组成

| 候选 | 配置 | 来源 | 本轮 seeds | Jobs |
|---|---|---|---|---:|
| DR047 | `direction_sample_h48_w0.535_a0.002` | ATTEMPT-011 repeat mean best | 6 到 15 | 10 |
| DR020 | `direction_sample_h48_w0.525_a0.003` | ATTEMPT-011 repeat mean second | 6 到 15 | 10 |
| DR041 | `direction_sample_h48_w0.515_a0.002` | ATTEMPT-011 repeat range tightest | 6 到 15 | 10 |
| A011DR042 | `direction_sample_h48_w0.515_a0.004` | ATTEMPT-011 best single H=75.00 | 6 到 15 | 10 |
| A011DR020 | `direction_sample_h48_w0.555_a0.0045` | ATTEMPT-011 top single H=74.98 | 6 到 15 | 10 |

总计 50 jobs，使用两张 GPU 轮转分配。

## 固定训练设置

```text
base_version: v5
batch_size: 64
Config epochs field: 30
Planned train epochs: 50
Epoch schedule source: lr_stages
LR stages: 20 + 20 + 10
GPUs: 0,1
```

## 证据边界

- 本轮可以产生 multi-seed stability evidence。
- 本轮不直接 promotion，因为仍缺少完整质量闭环、artifact identity 和独立 promotion gate。
- ATTEMPT-011 的 200/200 完成结果是候选来源，ATTEMPT-010 仍只作为 workflow smoke，不作为完整 confirmation 证据。
- 如需停止，创建服务器 batch 目录中的 `STOP_REQUESTED` 文件，runner 会停止领取新 job。
