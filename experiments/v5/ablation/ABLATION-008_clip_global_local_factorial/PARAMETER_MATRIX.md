# 参数矩阵：ABLATION-008_clip_global_local_factorial

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：由 16 份冻结配置逐行生成；每行只改变 `score_path` 和运行种子。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | C-FROZEN-seed-5-repeat-1 | ablation | frozen | {"score_path":"frozen_clip"} | 5 |  |  | determinism_check_not_training_stability |  |  |  |
| RUN-002 | C-FROZEN-seed-5-repeat-2 | ablation | frozen | {"score_path":"frozen_clip"} | 5 | RUN-001 |  | determinism_check_not_training_stability |  |  |  |
| RUN-003 | C-FROZEN-seed-17-repeat-1 | ablation | frozen | {"score_path":"frozen_clip"} | 17 |  |  | determinism_check_not_training_stability |  |  |  |
| RUN-004 | C-FROZEN-seed-17-repeat-2 | ablation | frozen | {"score_path":"frozen_clip"} | 17 | RUN-003 |  | determinism_check_not_training_stability |  |  |  |
| RUN-005 | G-GLOBAL-seed-5-repeat-1 | ablation | frozen | {"score_path":"global"} | 5 |  |  | G-GLOBAL：种子 5 第 1 次，分解全局与局部路径贡献 |  |  |  |
| RUN-006 | G-GLOBAL-seed-5-repeat-2 | ablation | frozen | {"score_path":"global"} | 5 | RUN-005 |  | G-GLOBAL：种子 5 第 2 次，分解全局与局部路径贡献 |  |  |  |
| RUN-007 | G-GLOBAL-seed-17-repeat-1 | ablation | frozen | {"score_path":"global"} | 17 |  |  | G-GLOBAL：种子 17 第 1 次，分解全局与局部路径贡献 |  |  |  |
| RUN-008 | G-GLOBAL-seed-17-repeat-2 | ablation | frozen | {"score_path":"global"} | 17 | RUN-007 |  | G-GLOBAL：种子 17 第 2 次，分解全局与局部路径贡献 |  |  |  |
| RUN-009 | L-LOCAL-SCORE-seed-5-repeat-1 | ablation | frozen | {"score_path":"local"} | 5 |  |  | L-LOCAL-SCORE：种子 5 第 1 次，分解全局与局部路径贡献 |  |  |  |
| RUN-010 | L-LOCAL-SCORE-seed-5-repeat-2 | ablation | frozen | {"score_path":"local"} | 5 | RUN-009 |  | L-LOCAL-SCORE：种子 5 第 2 次，分解全局与局部路径贡献 |  |  |  |
| RUN-011 | L-LOCAL-SCORE-seed-17-repeat-1 | ablation | frozen | {"score_path":"local"} | 17 |  |  | L-LOCAL-SCORE：种子 17 第 1 次，分解全局与局部路径贡献 |  |  |  |
| RUN-012 | L-LOCAL-SCORE-seed-17-repeat-2 | ablation | frozen | {"score_path":"local"} | 17 | RUN-011 |  | L-LOCAL-SCORE：种子 17 第 2 次，分解全局与局部路径贡献 |  |  |  |
| RUN-013 | GL-FULL-seed-5-repeat-1 | ablation | frozen | {"score_path":"full"} | 5 |  |  | GL-FULL：种子 5 第 1 次，分解全局与局部路径贡献 |  |  |  |
| RUN-014 | GL-FULL-seed-5-repeat-2 | ablation | frozen | {"score_path":"full"} | 5 | RUN-013 |  | GL-FULL：种子 5 第 2 次，分解全局与局部路径贡献 |  |  |  |
| RUN-015 | GL-FULL-seed-17-repeat-1 | ablation | frozen | {"score_path":"full"} | 17 |  |  | GL-FULL：种子 17 第 1 次，分解全局与局部路径贡献 |  |  |  |
| RUN-016 | GL-FULL-seed-17-repeat-2 | ablation | frozen | {"score_path":"full"} | 17 | RUN-015 |  | GL-FULL：种子 17 第 2 次，分解全局与局部路径贡献 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
