# 实现说明

不重训；固定 k=5、residual_cap=0.25，局部不能提升候选集外类别。

共享入口与完整公式见 `experiments/v5/local_evidence_runtime/implementation.md`。
冻结母版、数据划分、类别轴、训练日程和评估口径不变。
