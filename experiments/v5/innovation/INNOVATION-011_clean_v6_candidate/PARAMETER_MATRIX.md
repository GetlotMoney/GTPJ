# 参数矩阵：INNOVATION-011_clean_v6_candidate

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：IDEA-0013 干净 V6 候选；RUN-001 单次有效运行完成

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | clean-v6-candidate-seed5 | innovation | completed | {"consist_dynamic_gamma":"<removed>","consist_temp":"<removed>","fgvd_select_k":"<removed>","icsa_hidden":"<removed>","icsa_ratio":"<removed>","lambda_bmdd":"<removed>","lambda_consist":"<removed>","lambda_mpp":"<removed>","lambda_neg":"<removed>","lambda_topo_pearson":"<removed>","local_weight":"<removed>","msdn_temp":"<removed>","pse_dropout":"<removed>","pse_heads":"<removed>","pse_inner_ratio":"<removed>","pse_outer_ratio":"<removed>","region_temperature":"0.07","score_mode":"<removed>","sgmp_hidden":"<removed>","sgmp_neg_margin":"<removed>","sgmp_topk":"<removed>","text_source":"<removed>","tf_common_dim":"<removed>","tf_dropout":"<removed>","tf_heads":"<removed>","weight_s2v":"<removed>"} | 5 |  | RUN-001 | 用最小干净框架验证8句句子—区域交互本身是否合理 | 61.156446573601244 | continue_clean_framework | 1dec9d21bc9e717ca481c8392fd121b2fc828a88545ddaba49d6459a82c1a328 |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
