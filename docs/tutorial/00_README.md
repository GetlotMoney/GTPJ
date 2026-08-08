# GTPJ 代码完全教程 — 目录

> **目标读者**：PyTorch 初学者，想逐行理解 GTPJ 框架的全部代码。
> **阅读顺序**：按编号依次读。每篇末尾有"你已经学会"检查点。

> **阅读范围**：本套教程解释仓库根目录的 `model/MyModel.py`、`train_GTPJ_CUB.py` 和 `tools/`。
> 正式 V5 新实验的代码起点以冻结母版 `model/v5-template-v1`（commit `2f5fa5e`）及
> `experiments/v5/TEMPLATE.yaml` 为准；教程用于理解代码，不替代正式实验配置和母版身份。
> 当前框架、母版和四类实验状态请看
> [UI-FRAMEWORK-REGISTRY-V3](../diagrams/GTPJ_FRAMEWORK_REGISTRY_UI-V3.html)。

---

## 教程列表

| 编号 | 文档 | 内容 | 预计时间 |
|---|---|---|---|
| 01 | [PyTorch 基础速览](01_pytorch_basics.md) | `nn.Module`、`forward`、`nn.Parameter`、`register_buffer`、张量形状操作等代码中用到的所有 PyTorch 概念 | 30 分钟 |
| 02 | [框架全景图](02_framework_overview.md) | 数据从哪里来、经过哪些模块、最终到哪里去——完整数据流，附张量形状变化表 | 30 分钟 |
| 03 | [模型代码详解](03_model_explained.md) | `model/MyModel.py` 逐类、逐函数讲解，从工具函数到 GTPJ.forward | 2 小时 |
| 04 | [训练代码详解](04_training_explained.md) | `train_GTPJ_CUB.py` 从头到尾：配置加载、数据准备、训练循环、评估、Resume、多段训练 | 1.5 小时 |
| 05 | [工具代码详解](05_tools_explained.md) | `tools/dataset.py`（数据加载）+ `tools/helper_func.py`（特征提取 + 评估）| 1 小时 |

---

## 使用方式

1. 如果你连 `nn.Linear` 都不熟 → 从 01 开始
2. 如果你会 PyTorch 但不知道 GTPJ 整体架构 → 从 02 开始
3. 如果你已经看了框架图，想看代码细节 → 从 03 开始
4. 如果你想理解训练流程、怎么调参 → 从 04 开始

每篇文档可以独立阅读，但建议按顺序读。

---

## 代码阅读的最佳方式

打开两个窗口：
- 左边：VS Code 打开 `model/MyModel.py` 或 `train_GTPJ_CUB.py`
- 右边：浏览器打开对应的教程文档

对照着看，效率最高。
