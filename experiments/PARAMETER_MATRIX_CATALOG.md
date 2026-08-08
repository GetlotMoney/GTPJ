# 参数表总入口

每一行 `RUN-xxx` 都代表一次实际训练或明确记录的历史状态；结果、配置快照和外部证据位置均从同一行回查。

| 实验 | 行数 | 当前状态 | 阅读入口 |
|---|---:|---|---|
| `V5-ABLATION-001` | 16 | 6 条有效配对训练完成；其余为保留的失败、取消或未启动历史 | `experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.md` |

原始日志、checkpoint、缓存和数据集不在 GitHub；参数表只保存 Warehouse 位置、哈希、运行编号和最终指标。
