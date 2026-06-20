# 项目状态

日期：2026-06-20

## 当前基线

```text
name: GTPJ-v1
code_tag: v1
status: initialized, pending clean rerun
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

导入的第一版 baseline 的历史参考值：

| 数据集 | Seed | U | S | H | ZS | 状态 |
|---|---:|---:|---:|---:|---:|---|
| CUB GZSL | 5 | 71.46 | 76.40 | 73.85 | 81.61 | 仅作参考，必须重跑 |

## 下一步

在 `experiments/v1/confirmation/` 下运行 `CONFIRM-001_clean_seed5`，
确认这个干净仓库中的第一版 baseline。
