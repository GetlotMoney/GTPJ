# 参数矩阵：INNOVATION-003_confidence_local_gate

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：IDEA-0005 已由主分支提交 6e42dfcff09a87c14aba807e4bb0fd7ab0d73350 登记；三份 seed=5 配置已冻结，尚未训练。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 低置信度局部增强-重复1 | innovation | completed | {"gate":"sigmoid(bias-softplus(slope_raw)*margin)","gate_beta":0.05,"gate_bias_init":-1.0,"gate_slope_init":1.0} | 5 |  | V5INN003-RUN-001 | 验证固定门控路线的首个同配置运行 | 73.20367652523284 | reject |  |
| RUN-002 | 低置信度局部增强-重复2 | innovation | completed | {"gate":"sigmoid(bias-softplus(slope_raw)*margin)","gate_beta":0.05,"gate_bias_init":-1.0,"gate_slope_init":1.0} | 5 | RUN-001 | V5INN003-RUN-002 | 检查相同配置在独立运行中的稳定性 | 73.50497581403644 | reject |  |
| RUN-003 | 低置信度局部增强-重复3 | innovation | completed | {"gate":"sigmoid(bias-softplus(slope_raw)*margin)","gate_beta":0.05,"gate_bias_init":-1.0,"gate_slope_init":1.0} | 5 | RUN-001 | V5INN003-RUN-003 | 检查相同配置在独立运行中的稳定性 | 73.57355961856747 | reject |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
