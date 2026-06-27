# 项目状态

日期：2026-06-27

## 当前基线

```text
name: GTPJ-v2
code_tag: v2
status: activated_by_owner
dataset: CUB GZSL
baseline_evidence: experiments/v2/baseline/
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

`GTPJ-v2` 是当前正式主线 baseline。它由 `GTPJ-v1` 加上
`TRIAL-001 / ATTEMPT-019` 的 CLIP-A-self 文本原型 adapter 产生，使用 CUB GZSL、seed=5
和三阶段训练契约。

| 实验 | 数据集 | Seed | U | S | H | ZS | 状态 |
|---|---|---:|---:|---:|---:|---:|---|
| `GTPJ-v1` | CUB GZSL | 5 | 72.36 | 75.57 | 73.93 | 81.62 | 第一版正式 baseline |
| `GTPJ-v2` | CUB GZSL | 5 | 71.32 | 77.52 | 74.29 | 81.59 | 当前正式主线，owner activated |

## 已知风险

- `GTPJ-v2` 仍建议补一次 clean confirmation。
- `GTPJ-v2` 的 `S - U = 6.20`，后续需要 seen/unseen gap analysis。

## 下一步

使用 `GTPJ-v2` 的 CUB seed=5 基准继续调参、消融和 confirmation。优先补
`CONFIRM-001_v2_seed5`，再决定是否继续冲更高 H 或做论文级多 seed 复核。
