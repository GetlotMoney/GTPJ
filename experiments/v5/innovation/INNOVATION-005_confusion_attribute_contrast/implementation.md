# 实现说明

在 local CE 上，用 detached global seen logits 选 top-5 非真类，加入 0.1 权重、0.1 margin 排序损失。

共享入口与完整公式见 `experiments/v5/local_evidence_runtime/implementation.md`。
冻结母版、数据划分、类别轴、训练日程和评估口径不变。
