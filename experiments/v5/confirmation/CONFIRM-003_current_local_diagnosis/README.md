# V5-CONFIRM-003：最新母版基线与局部互补性

本实验只使用 `MODEL-V5-TEMPLATE-V1@2f5fa5e`。固定 seed=5 独立训练三次，
完整报告 U/S/H/ZS 的 mean/min/max/range；随后对三份最佳模型做推理诊断。

诊断统计全局、局部、原融合、全局错误但局部正确、全局正确但局部错误、
全局到融合的救对/破坏、分支相关性、seen 预测偏置和理想选择器上限。
测试标签只用于事后解释，不用于选择门控参数。

原始日志和模型写入项目内被 Git 忽略的
`.runtime/runs/v5/local_complementarity/V5-CONFIRM-003/`，不会进入 Git。

## 启动失败留痕

提交 `a7d3289dbe9b06341f2d8ceb3296c23d25909ca2` 的首次启动在 epoch 1 前失败：
类别划分已被训练入口放到 CUDA，而模型构造期用 CPU 类别轴检查，触发设备不一致。
失败日志保存在 `RUN-000-startup-failure/`，不计入计划的三次训练。修复只让
`load_v5_cub_split` 在构造期返回 CPU 类别编号，模型整体 `.to(cuda)` 时再统一迁移；
配置、模型公式、数据、seed 和评估口径均未改变。
