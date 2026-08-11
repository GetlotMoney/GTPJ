# 实现说明

保留同一 top-K、embed_cv、BVSA、SGMP 和融合，只令 fgvd_memory=fgvd_patch_z。

共享入口与完整公式见 `experiments/v5/local_evidence_runtime/implementation.md`。
冻结母版、数据划分、类别轴、训练日程和评估口径不变。
