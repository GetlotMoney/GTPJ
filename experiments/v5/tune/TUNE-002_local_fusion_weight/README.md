# V5-TUNE-002：局部融合权重实验

本实验只回答一个问题：保持 V5 模型、损失、数据划分和评估口径不变时，局部分支在最终分数中的权重取多少更合适。

- 代码母版：`model/v5-template-v1@2f5fa5e631ef82658d4bac587cdfd17f3534cb35`
- 实现代码：`3af9bfa8247b7aa6bc4ba4b5aa6c69f35277cd28`
- 冻结权重：`0.05 / 0.10 / 0.30 / 0.40`
- 每个权重：seed 5 复跑两次，seed 17 复跑两次，共 16 个 RUN
- 运行设备：物理 GPU 0，进程内逻辑设备 `cuda:0`
- 证据边界：`not_confirmation_evidence: true`
- 审核状态：`strict-3 / review_pending`

当前只完成运行前代码与参数冻结，没有训练、指标、结果文件或性能结论。
