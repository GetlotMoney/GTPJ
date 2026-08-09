# 参数矩阵：INNOVATION-008_pse_class_relation_calibration

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：由 new-experiment 生成；该草稿必须填写并通过校验后才能用于正式运行。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | E0 新公平基线 | innovation | planned | {"pse_mode":"legacy_sentence","pse_apply_unseen":false,"lambda_self_calibration":0.0} | 5 |  |  | 在独立批次随机数与测试集只评一次口径下建立基线 |  |  |  |
| RUN-002 | E1 修复类别自注意力 | innovation | planned | {"pse_mode":"class_relation","pse_apply_unseen":false,"pse_class_residual_ratio":0.1} | 5 |  |  | 验证类别间原型关系是否真正有用 |  |  |  |
| RUN-003 | E2 未见类共享 PSE | innovation | planned | {"pse_mode":"class_relation","pse_apply_unseen":true,"pse_class_residual_ratio":0.1} | 5 |  |  | 验证共享权重分组处理未见类原型是否改善迁移 |  |  |  |
| RUN-004 | E3 训练期概率下限校准 | innovation | planned | {"pse_mode":"class_relation","pse_apply_unseen":true,"lambda_self_calibration":0.1,"self_calibration_target":0.05} | 5 |  |  | 验证训练阶段能否减少已见类偏置且不把未见类加入交叉熵 |  |  |  |
| RUN-005 | E4 验证集选 gamma 的推理校准 | innovation | planned | {"checkpoint_from":"RUN-003","gamma":null,"gamma_source":"class_disjoint_validation"} | 5 |  |  | 只用验证划分确定 gamma 后复用 E2 checkpoint 并同时报告原始与校准分数 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
