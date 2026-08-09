# 参数矩阵：ABLATION-009_bvsa_direction_effect

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：CAMP-20260809-v5-ablation100 的 8 个冻结配置；当前未训练

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | S2V-ONLY seed=5 repeat=1 | ablation | frozen | {"weight_s2v":1} | 5 |  |  | 最终局部分数只采用 S2V 方向 |  |  |  |
| RUN-002 | S2V-ONLY seed=5 repeat=2 | ablation | frozen | {"weight_s2v":1} | 5 | RUN-001 |  | 最终局部分数只采用 S2V 方向 |  |  |  |
| RUN-003 | S2V-ONLY seed=17 repeat=1 | ablation | frozen | {"weight_s2v":1} | 17 |  |  | 最终局部分数只采用 S2V 方向 |  |  |  |
| RUN-004 | S2V-ONLY seed=17 repeat=2 | ablation | frozen | {"weight_s2v":1} | 17 | RUN-003 |  | 最终局部分数只采用 S2V 方向 |  |  |  |
| RUN-005 | V2S-ONLY seed=5 repeat=1 | ablation | frozen | {"weight_s2v":0} | 5 |  |  | 最终局部分数只采用 V2S 方向 |  |  |  |
| RUN-006 | V2S-ONLY seed=5 repeat=2 | ablation | frozen | {"weight_s2v":0} | 5 | RUN-005 |  | 最终局部分数只采用 V2S 方向 |  |  |  |
| RUN-007 | V2S-ONLY seed=17 repeat=1 | ablation | frozen | {"weight_s2v":0} | 17 |  |  | 最终局部分数只采用 V2S 方向 |  |  |  |
| RUN-008 | V2S-ONLY seed=17 repeat=2 | ablation | frozen | {"weight_s2v":0} | 17 | RUN-007 |  | 最终局部分数只采用 V2S 方向 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
