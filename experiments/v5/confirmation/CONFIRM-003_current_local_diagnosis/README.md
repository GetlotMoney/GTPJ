# V5-CONFIRM-003：最新母版基线与局部互补性

本实验只使用 `MODEL-V5-TEMPLATE-V1@2f5fa5e`。固定 seed=5 独立训练三次，
完整报告 U/S/H/ZS 的 mean/min/max/range；随后对三份最佳模型做推理诊断。

诊断统计全局、局部、原融合、全局错误但局部正确、全局正确但局部错误、
全局到融合的救对/破坏、分支相关性、seen 预测偏置和理想选择器上限。
测试标签只用于事后解释，不用于选择门控参数。

原始日志和模型写入项目内被 Git 忽略的
`.runtime/runs/v5/local_complementarity/V5-CONFIRM-003/`，不会进入 Git。
