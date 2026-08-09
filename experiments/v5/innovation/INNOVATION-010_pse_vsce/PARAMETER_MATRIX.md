# 参数矩阵：INNOVATION-010_pse_vsce

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：已从服务器 RUN-001 的启动/结束收据、封口日志与 final_metrics.json 回填；原始证据保留在 Warehouse。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | PSE+VSCE双向句子区域交互 | innovation | completed | {"interaction_mode":"pse_vsce","text_source":"gpt56_8sent"} | 5 |  | RUN-001 | 与实验A保持训练条件一致：seed5、50epoch，仅比较VSCE双向交互 | 58.917815 | reject |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
