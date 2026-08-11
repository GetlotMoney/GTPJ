# 实现说明

在 local CE 上增加两视角 crop teacher 概率平均后的 KL，权重 0.05、温度 2.0。

共享入口与完整公式见 `experiments/v5/local_evidence_runtime/implementation.md`。
冻结母版、数据划分、类别轴、训练日程和评估口径不变。
