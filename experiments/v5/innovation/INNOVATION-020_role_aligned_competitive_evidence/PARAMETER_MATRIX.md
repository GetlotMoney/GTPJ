# 参数矩阵：INNOVATION-020_role_aligned_competitive_evidence

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：`PARAMETER_MATRIX.csv`。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | race-aligned-seed5 | innovation | completed | {"module":"RACE","rival_universe":"full_200_text_only","strength_grid":"0.0:0.1:2.0","selected_strength":0.1,"controls":"no_contrast+wrong_role","official_test":"single"} | 5 |  | RUN-001 | 验证决策级同角色竞争证据能否无test选参提高Mean8 | 66.54109576619167 | stop_no_gain |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
