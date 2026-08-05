# 参数矩阵总看板

这是所有实验“参数表”的总入口，不替代 `EXPERIMENT_REGISTRY.md` 的版本关系记录。

## 当前规则

- 从 2026-08-04 起，新建实验必须遵守 [参数矩阵规范](../docs/workflow/protocols/parameter_matrix_protocol.md)。
- 每一行是一个实际任务；每一批 Attempt 至少有一张完整参数矩阵。
- 原始日志、模型和完整训练输出仍在 Warehouse，表中只保留引用和校验信息。

## 历史迁移队列

| 范围 | 当前可见程度 | 处理方式 |
|---|---|---|
| `v3 → v4` 的纯配置调参 | 已知最终参数和 3 次确认结果；缺少完整候选搜索清单 | 从 Warehouse 的 `local-v3-054` 来源恢复；无法恢复的标为历史缺失 |
| 动态路由 `ATTEMPT-001` 至 `ATTEMPT-018` | 有批次摘要、部分 `WORK_ITEMS.md` 和结果；早期批次缺少逐任务表 | 从每批 `plan.json`、`summary.csv` 和配置快照恢复 |
| 今后所有新实验 | 完整参数矩阵 | 开跑前生成，跑完回填 |

## 使用顺序

```text
总看板 -> 具体版本或 Attempt 的 PARAMETER_MATRIX.md -> 该行的完整配置/结果/Warehouse 引用
```

不要从运行缓存目录猜测待跑任务；是否可跑只看正式账本和参数矩阵。
