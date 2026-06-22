# 项目状态

日期：2026-06-21

## 当前基线

```text
name: GTPJ-v1
code_tag: v1
status: confirmed
dataset: CUB GZSL
baseline_evidence: experiments/v1/baseline/
```

## 当前启用模块

- 冻结的 CLIP ViT-L/14@336px backbone
- GPT 文本描述 prototype
- Text Adapter
- Patch bottleneck / patch selection
- 几何感知局部视觉编码
- 双向视觉-文本交互
- 拓扑保持文本约束
- 条件文本适配
- 视觉-文本双分支互蒸馏
- AG-JEPA 辅助训练
- AG-JEPA negative text margin

## 正式结果状态

`GTPJ-v1` 已确定为新仓库第一版正式 baseline。该结果使用同一主框架、CUB GZSL、seed=5 和三阶段训练契约。

| 实验 | 数据集 | Seed | U | S | H | ZS | 状态 |
|---|---|---:|---:|---:|---:|---:|---|
| `GTPJ-v1` | CUB GZSL | 5 | 72.36 | 75.57 | 73.93 | 81.62 | 第一版正式 baseline |

## 下一步

使用 `GTPJ-v1` 的 CUB seed=5 基准，开始模块 trial、调参、消融或跨数据集实验。
