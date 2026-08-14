# 参数矩阵：INNOVATION-012_global8_clip_baseline

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：8句话纯CLIP全局零模块基线

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 8句纯CLIP全局基线 | innovation | frozen | {"trainable_parameters":0,"text_aggregation":"normalized_sentence_mean"} | 0 |  | RUN-001 | 建立8句话纯CLIP全局分数的真实U/S/H/ZS |  | pending |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
