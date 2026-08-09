# 模块来源

## 最小真实问题

旧 `ProgressiveSemanticSelfAttention` 接收 `[C, M, D]`，PyTorch 的 batch-first attention 会把 `C` 当作互不相干的 batch，把 `M` 当作 token。因此它能在一个类别的多条文本句子之间聚合，却不能让类别 A 参考类别 B。

## 直接证据

- 代码锚点：`model/MyModel.py::ProgressiveSemanticSelfAttention`。
- 反事实输入：固定所有类别，只大幅改变类别 0 的原型。
- 观察结果：类别 0 输出发生变化；其他类别输出 `max delta=0.0`。
- 判定：旧模块不具备本计划需要的类别关系建模能力。

## 外部方法来源

1. Calibrated stacking：Chao 等人，[An Empirical Study and Analysis of Generalized Zero-Shot Learning for Object Recognition](https://arxiv.org/pdf/1605.04253)。本实验采用 `seen logits -= gamma`，且只允许从验证划分选择 `gamma`。
2. DAZLE 的训练期 self-calibration 提供“给未见类保留概率”的动机。原论文损失并非直接适配本实验的 seen-only CE，因此这里只采用有界概率下限，明确标为 DAZLE-inspired，不声称复现原损失。

## 与 V5 的关系

V5 的其他路径保持不变：FGVD、BVSA、ICSA、SGMP、`global + 0.2 * local`、类别编号和 U/S/H/ZS 计算都不是本次创新变量。
