# 参数矩阵：INNOVATION-018_dual_prototype_expert_fusion

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：`experiments/v5/innovation/INNOVATION-018_dual_prototype_expert_fusion/PARAMETER_MATRIX.csv`

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | dpef-score-search-seed5 | innovation | completed | {"strong_expert":"uniform_seenonly_topology","shared_source":"V5-INNOVATION-017/RUN-002","seen_blend":"0.00:0.01:0.30","unseen_blend":"0.80:0.02:1.00","selection":"official_test_score_search"} | 5 |  | RUN-001 | 验证双原型专家融合能否在已披露 test 搜索口径达到75+ | 76.44701608042955 | keep_score_search |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
