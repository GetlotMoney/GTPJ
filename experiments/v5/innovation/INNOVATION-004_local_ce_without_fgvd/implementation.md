# 实现说明

在 FGVD-off 控制上仅增加权重 0.1 的 seen-class local CE。

共享入口与完整公式见 `experiments/v5/local_evidence_runtime/implementation.md`。
冻结母版、数据划分、类别轴、训练日程和评估口径不变。
