# 参数矩阵：INNOVATION-003_confidence_local_gate

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：本任务冻结的科学规格与 configs/RUN-001..003.yaml 预跑草案；尚未产生训练结果。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 低置信度局部增强-重复1 | innovation | planned | {"gate":"sigmoid(bias-softplus(slope_raw)*margin)","gate_beta":0.05,"gate_bias_init":-1.0,"gate_slope_init":1.0} | 5 |  |  | 验证固定门控路线的首个同配置运行 |  |  |  |
| RUN-002 | 低置信度局部增强-重复2 | innovation | planned | {"gate":"sigmoid(bias-softplus(slope_raw)*margin)","gate_beta":0.05,"gate_bias_init":-1.0,"gate_slope_init":1.0} | 5 | RUN-001 |  | 检查相同配置在独立运行中的稳定性 |  |  |  |
| RUN-003 | 低置信度局部增强-重复3 | innovation | planned | {"gate":"sigmoid(bias-softplus(slope_raw)*margin)","gate_beta":0.05,"gate_bias_init":-1.0,"gate_slope_init":1.0} | 5 | RUN-001 |  | 检查相同配置在独立运行中的稳定性 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
