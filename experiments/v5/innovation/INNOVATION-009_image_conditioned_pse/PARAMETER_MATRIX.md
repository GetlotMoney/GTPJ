# 参数矩阵：INNOVATION-009_image_conditioned_pse

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：由 owner 2026-08-10 选择 IDEA-0011；A/B 使用相同训练条件。RUN-001 保留失败证据，修复评估设备后由 RUN-002 完成同配置重跑。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | image-conditioned-PSE-seed5 | innovation | failed | {"interaction_mode":"image_conditioned_pse","text_source":"gpt56_8sent"} | 5 |  | RUN-001 | 验证全局图像选择8句话是否优于V5的ICSA |  | process_failed |  |
| RUN-002 | image-conditioned-PSE-seed5-evalfix | innovation | completed | {"interaction_mode":"image_conditioned_pse","text_source":"gpt56_8sent"} | 5 | RUN-001 | RUN-002 | RUN-001首次评估因CPU/CUDA索引设备不一致失败；修复后保持同参数重跑 | 59.405826 | reject |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
