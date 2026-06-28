# 项目状态

日期：2026-06-28

## 当前基线

```text
name: GTPJ-v3
code_tag: v3
status: owner_accepted_stochastic_unconfirmed
dataset: CUB GZSL
baseline_evidence: experiments/v3/baseline/
best_observed_H: 74.27
confirmed_H: pending
confirmation_status: needs_confirmation
```

## 当前启用模块

- 冻结的 CLIP ViT-L/14@336px backbone
- GPT 文本描述 prototype
- CLIP-A-self sentence-level text prototype adapter
- Patch bottleneck / patch selection
- 几何感知局部视觉编码
- 双向视觉-文本交互
- 拓扑保持文本约束
- 条件文本适配
- 视觉-文本双分支互蒸馏
- AG-JEPA 辅助训练
- AG-JEPA negative text margin

## 正式结果状态

`GTPJ-v3` 是当前 owner 按随机性判断接受的正式 tag。它由 `GTPJ-v2` 加上
`IDEA-0002 / TRIAL-002 / ATTEMPT-004` 的 strict conditional FAE-memory JEPA 产生，使用 CUB GZSL、seed=5
和三阶段训练契约。`H=74.27` 作为 `best_observed_H` 保留；clean confirmation 通过前，
不得写成 `confirmed_H` 或稳定 baseline-grade 证据。

| 实验 | 数据集 | Seed | U | S | H | ZS | 状态 |
|---|---|---:|---:|---:|---:|---:|---|
| `GTPJ-v1` | CUB GZSL | 5 | 72.36 | 75.57 | 73.93 | 81.62 | 第一版正式 baseline |
| `GTPJ-v2` | CUB GZSL | 5 | 71.32 | 77.52 | 74.29 | 81.59 | owner activated, needs confirmation |
| `GTPJ-v3` | CUB GZSL | 5 | 71.22 | 77.60 | 74.27 | 81.38 | owner accepted stochastic, needs confirmation |

## 已知风险

- `GTPJ-v3` 必须补 clean confirmation / multi-seed 复核后，才能把 `best_observed_H=74.27` 升级为
  `confirmed_H` 或 baseline-grade 证据。
- `GTPJ-v2` 的 `S - U = 6.20`，后续需要 seen/unseen gap analysis。

## 下一步

使用 `GTPJ-v3` 的 CUB seed=5 基准继续调参、消融和 confirmation。优先补
`CONFIRM-001_v3_seed5`，再决定是否继续冲更高 H 或做论文级多 seed 复核。
