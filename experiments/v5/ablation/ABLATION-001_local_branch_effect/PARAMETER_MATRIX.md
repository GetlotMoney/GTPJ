# 参数矩阵：ABLATION-001_local_branch_effect

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：R3/R4 历史证据保留；R4 的 seed 5 与 R5 的 seed 17、29 全部完成，形成 FULL 与 GLOBAL_ONLY 三种子配对结果。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 完整 V5 seed 5 | ablation | failed | {} | 5 |  | RUN-20260807-V5ABL001-R3-FULL-S5 | 与无局部组做同种子配对比较 |  | process_failed_cuda_class_identity_device_mismatch |  |
| RUN-002 | 完整 V5 seed 17 | ablation | cancelled | {} | 17 |  | RUN-20260807-V5ABL001-R3-FULL-S17 | 与无局部组做同种子配对比较 |  | not_started_after_stop_or_failure |  |
| RUN-003 | 完整 V5 seed 29 | ablation | cancelled | {} | 29 |  | RUN-20260807-V5ABL001-R3-FULL-S29 | 与无局部组做同种子配对比较 |  | not_started_after_stop_or_failure |  |
| RUN-004 | 干净无局部 seed 5 | ablation | failed | {} | 5 |  | RUN-20260807-V5ABL001-R3-GLOBAL-S5 | 删除 FGVD、BVSA、SGMP、局部融合和局部损失；保留 PSE、ICSA、CE、topology |  | process_failed_cuda_class_identity_device_mismatch |  |
| RUN-005 | 干净无局部 seed 17 | ablation | cancelled | {} | 17 |  | RUN-20260807-V5ABL001-R3-GLOBAL-S17 | 删除 FGVD、BVSA、SGMP、局部融合和局部损失；保留 PSE、ICSA、CE、topology |  | not_started_after_stop_or_failure |  |
| RUN-006 | 干净无局部 seed 29 | ablation | cancelled | {} | 29 |  | RUN-20260807-V5ABL001-R3-GLOBAL-S29 | 删除 FGVD、BVSA、SGMP、局部融合和局部损失；保留 PSE、ICSA、CE、topology |  | not_started_after_stop_or_failure |  |
| RUN-007 | 完整 V5 seed 5 | ablation | completed | {} | 5 | RUN-001 | RUN-20260808-V5ABL001-R4-FULL-S5 | 与无局部组做同种子配对比较 | 74.17 | completed_recovered_after_v5_log_parser_fix | 3eb27b0e18327ebcef8d89131040322851302deedbdd6a594b8bf58973c4146b |
| RUN-008 | 完整 V5 seed 17 | ablation | cancelled | {} | 17 | RUN-002 | RUN-20260808-V5ABL001-R4-FULL-S17 | 与无局部组做同种子配对比较 |  | not_started_after_r4_bookkeeping_failure |  |
| RUN-009 | 完整 V5 seed 29 | ablation | cancelled | {} | 29 | RUN-003 | RUN-20260808-V5ABL001-R4-FULL-S29 | 与无局部组做同种子配对比较 |  | not_started_after_r4_bookkeeping_failure |  |
| RUN-010 | 干净无局部 seed 5 | ablation | completed | {} | 5 | RUN-004 | RUN-20260808-V5ABL001-R4-GLOBAL-S5 | 删除 FGVD、BVSA、SGMP、局部融合和局部损失；保留 PSE、ICSA、CE、topology | 73.92 | completed_recovered_after_v5_log_parser_fix | f7d6228fda5bd9ce99c191911022206697d88ece5d89dc0d558a300deecdf4ef |
| RUN-011 | 干净无局部 seed 17 | ablation | cancelled | {} | 17 | RUN-005 | RUN-20260808-V5ABL001-R4-GLOBAL-S17 | 删除 FGVD、BVSA、SGMP、局部融合和局部损失；保留 PSE、ICSA、CE、topology |  | not_started_after_r4_bookkeeping_failure |  |
| RUN-012 | 干净无局部 seed 29 | ablation | cancelled | {} | 29 | RUN-006 | RUN-20260808-V5ABL001-R4-GLOBAL-S29 | 删除 FGVD、BVSA、SGMP、局部融合和局部损失；保留 PSE、ICSA、CE、topology |  | not_started_after_r4_bookkeeping_failure |  |
| RUN-013 | 完整 V5 seed 17 | ablation | completed | {} | 17 | RUN-008 | RUN-20260808-V5ABL001-R5-FULL-S17 | 与无局部组做同种子配对比较 | 74.05 | completed_r5_formal_run | 425d94bce817534180028b372704e38c177556d63ada23c7df6295501bb95e0f |
| RUN-014 | 完整 V5 seed 29 | ablation | completed | {} | 29 | RUN-009 | RUN-20260808-V5ABL001-R5-FULL-S29 | 与无局部组做同种子配对比较 | 74.12 | completed_r5_formal_run | 6160ffa42bbe8e90dabd83c7802b495d9fb588b885d2f78b602a13e46a03cd1d |
| RUN-015 | 干净无局部 seed 17 | ablation | completed | {} | 17 | RUN-011 | RUN-20260808-V5ABL001-R5-GLOBAL-S17 | 删除 FGVD、BVSA、SGMP、局部融合和局部损失；保留 PSE、ICSA、CE、topology | 74.14 | completed_r5_formal_run | 0a70e516c1da2633878cd2e65df09774e8f4578d5e766f5fda484baa023c7fa3 |
| RUN-016 | 干净无局部 seed 29 | ablation | completed | {} | 29 | RUN-012 | RUN-20260808-V5ABL001-R5-GLOBAL-S29 | 删除 FGVD、BVSA、SGMP、局部融合和局部损失；保留 PSE、ICSA、CE、topology | 74.03 | completed_r5_formal_run | bfb1e0455d9870a44cf4cd7da66ed42f56068a0a80dd2f0488a6ce697e0fafa4 |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
