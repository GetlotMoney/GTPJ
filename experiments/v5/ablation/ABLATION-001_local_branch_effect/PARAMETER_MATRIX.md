# 参数矩阵：ABLATION-001_local_branch_effect

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：正式第一批仅比较完整 V5 与干净无局部版本；seed 5、17、29 配对。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 完整 V5 seed 5 | ablation | frozen | {} | 5 |  | RUN-20260808-V5ABL001-R4-FULL-S5 | 与无局部组做同种子配对比较 |  |  |  |
| RUN-002 | 完整 V5 seed 17 | ablation | frozen | {} | 17 |  | RUN-20260808-V5ABL001-R4-FULL-S17 | 与无局部组做同种子配对比较 |  |  |  |
| RUN-003 | 完整 V5 seed 29 | ablation | frozen | {} | 29 |  | RUN-20260808-V5ABL001-R4-FULL-S29 | 与无局部组做同种子配对比较 |  |  |  |
| RUN-004 | 干净无局部 seed 5 | ablation | frozen | {} | 5 |  | RUN-20260808-V5ABL001-R4-GLOBAL-S5 | 删除 FGVD、BVSA、SGMP、局部融合和局部损失；保留 PSE、ICSA、CE、topology |  |  |  |
| RUN-005 | 干净无局部 seed 17 | ablation | frozen | {} | 17 |  | RUN-20260808-V5ABL001-R4-GLOBAL-S17 | 删除 FGVD、BVSA、SGMP、局部融合和局部损失；保留 PSE、ICSA、CE、topology |  |  |  |
| RUN-006 | 干净无局部 seed 29 | ablation | frozen | {} | 29 |  | RUN-20260808-V5ABL001-R4-GLOBAL-S29 | 删除 FGVD、BVSA、SGMP、局部融合和局部损失；保留 PSE、ICSA、CE、topology |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
