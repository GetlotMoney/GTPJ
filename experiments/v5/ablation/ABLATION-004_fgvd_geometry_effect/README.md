# 去掉 FGVD 几何编码

- 问题：只跳过 FGVD 几何关系与几何编码器，最终 H 是否持平或提高？
- 基线：MODEL-V5-TEMPLATE-V1@2f5fa5e；参考完整模型同 seed H≈74.23、global-only H≈74.11。
- 唯一改动：保留同一 top-K、embed_cv、BVSA、SGMP 和融合，只令 fgvd_memory=fgvd_patch_z。
- 初筛：固定 seed 5；训练方案保持 50 epoch。
- 完成条件：独立 RUN 目录包含日志、最终指标；训练方案另含最佳模型。
- 停止条件：出现非有限数值、代码/输入变化或输出目录冲突时立即失败。
