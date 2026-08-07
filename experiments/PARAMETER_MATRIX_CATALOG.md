# 参数矩阵总看板

这是所有实验“参数表”的总入口，不替代 `EXPERIMENT_REGISTRY.md` 的版本关系记录。

## 当前规则

- 从 2026-08-06 起，正式入口是 `FRAMEWORK-VX / VX-TYPE-xxx / RUN-xxx`，完整规则见 [框架与实验正式规范](../docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md)。
- 每一行是一个实际任务；旧 Attempt 只作 `legacy_ref`。无法恢复逐任务参数时明确写 `legacy_summary_only`。
- 原始日志、模型和完整训练输出仍在 Warehouse，表中只保留引用和校验信息。

## 当前正式参数表

| 实验 | 行数 | 状态 | 阅读入口 |
|---|---:|---|---|
| `V1-INNOVATION-001` | 1 | 历史摘要 | `experiments/v1/innovation/INNOVATION-001_clip_a_self/PARAMETER_MATRIX.md` |
| `V1-CONFIRM-001` | 1 | 历史摘要 | `experiments/v1/confirmation/CONFIRM-001_v1_seed5/PARAMETER_MATRIX.md` |
| `V2-INNOVATION-001` | 1 | 历史摘要 | `experiments/v2/innovation/INNOVATION-001_strict_conditional_jepa/PARAMETER_MATRIX.md` |
| `V3-TUNE-001` | 1 | 历史候选摘要 | `experiments/v3/tune/TUNE-001_local_v3_054/PARAMETER_MATRIX.md` |
| `V3-CONFIRM-001` | 3 | 历史复跑摘要 | `experiments/v3/confirmation/CONFIRM-001_local_v3_054_min3/PARAMETER_MATRIX.md` |
| `V3-INNOVATION-001` | 6 | 已知来源与复跑 | `experiments/v3/innovation/INNOVATION-001_conditional_bvsa/PARAMETER_MATRIX.md` |
| `V5-TUNE-001` | 8 | 从 ATTEMPT-006 恢复的真实调参任务 | `experiments/v5/tune/TUNE-001_dynamic_routing_search/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-001` | 2 | 从 ATTEMPT-006 恢复的真实创新探针；其余见历史批次映射 | `experiments/v5/innovation/INNOVATION-001_dynamic_routing/PARAMETER_MATRIX.md` |
| `V5-ABLATION-001` | 6 | ready_to_run，三个 seed 的 FULL/GLOBAL_ONLY 配对 | `experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.md` |

## 历史迁移队列

| 范围 | 当前可见程度 | 处理方式 |
|---|---|---|
| `v3 → v4` 的纯配置调参 | 已知最终参数和 3 次确认结果；缺少完整候选搜索清单 | 从 Warehouse 的 `local-v3-054` 来源恢复；无法恢复的标为历史缺失 |
| 动态路由 `ATTEMPT-001` 至 `ATTEMPT-018` | ATTEMPT-006 已恢复 10 个真实任务；其余多数只有批次或分组摘要 | 先看 `LEGACY_ATTEMPT_MAP.md`；以后只有找到逐任务原始配置和结果才能继续补，禁止猜测 |
| 今后所有新实验 | 完整参数矩阵 | 开跑前生成，跑完回填 |

## 使用顺序

```text
总看板 -> 具体版本或 Attempt 的 PARAMETER_MATRIX.md -> 该行的完整配置/结果/Warehouse 引用
```

不要从运行缓存目录猜测待跑任务；是否可跑只看正式账本和参数矩阵。
