# 项目状态

日期：2026-06-20

## 当前基线

```text
name: GTPJ-v1
code_tag: v1
status: confirmed
dataset: CUB GZSL
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

任何结果都必须在本仓库中重跑并记录后，才算正式结果。
`CONFIRM-001_clean_seed5` 已完成，当前正式结果如下：

| 数据集 | Seed | U | S | H | ZS | 状态 |
|---|---:|---:|---:|---:|---:|---|
| CUB GZSL | 5 | 72.20 | 75.45 | 73.79 | 81.80 | 正式复现结果 |

历史导入参考值仅用于对照：CUB seed=5，U=71.46，S=76.40，H=73.85，ZS=81.61。

## 下一步

使用 `GTPJ-v1` 的正式 CUB seed=5 基准，开始模块 trial、调参或消融实验。
