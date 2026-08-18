# 参数矩阵：INNOVATION-023_rpr_legacy_mapping

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：从 PARAMETER_MATRIX.csv 生成

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | clip-mean8-seed5 | innovation | completed | {"condition":"clip_mean8","text_source":"gpt55_derived8","temperature":0.05} | 5 |  | RUN-001 | 建立同次纯CLIP八句基线 | 66.64257577389857 | baseline_recorded |  |
| RUN-002 | shared-pse-seed5 | innovation | completed | {"condition":"shared_pse","text_source":"gpt55_derived8","heads":4,"residual_cap":0.35} | 5 |  | RUN-002 | 正式复跑SharedPSE来源参考 | 70.61634823737899 | source_reference_recorded |  |
| RUN-003 | rpr-off-seed5 | innovation | failed | {"condition":"rpr_off","rank":32,"gate":0.0} | 5 |  | RUN-003 | 证明RPR关闭后精确退回B0 |  | failed_numeric_guard_false_positive |  |
| RUN-004 | rpr-shared-transform-seed5 | innovation | failed | {"condition":"rpr_shared_transform","rank":32,"gate_init":0.1,"role_specific_scales":false} | 5 |  | RUN-004 | 检验单共享变换是否已经足够 |  | failed_numeric_guard_false_positive |  |
| RUN-005 | rpr-role-separated-seed5 | innovation | failed | {"condition":"rpr_role_separated","rank":32,"gate_init":0.1,"role_specific_scales":true,"weight_bounds":[0.1,0.3]} | 5 |  | RUN-005 | 验证八角色分离低秩原型残差 |  | failed_numeric_guard_false_positive |  |
| RUN-006 | rpr-classwise-shuffle-seed5 | innovation | completed | {"condition":"rpr_classwise_shuffle","rank":32,"gate_init":0.1,"shuffle_seed":1705,"unique_nonidentity_per_class":true} | 5 |  | RUN-006 | 检验收益是否依赖正确角色对应 | 34.7585788344594 | control_completed_role_mismatch_collapse |  |
| RUN-007 | rpr-off-guard-retry-seed5 | innovation | completed | {"condition":"rpr_off","rank":32,"gate":0.0,"numeric_guard_revision":"same_device_mean8"} | 5 |  | RUN-007 | 替代被CPU/GPU浮点路径误拦的C0 | 66.64257577389857 | exact_off_control_pass |  |
| RUN-008 | rpr-shared-transform-guard-retry-seed5 | innovation | completed | {"condition":"rpr_shared_transform","rank":32,"gate_init":0.1,"role_specific_scales":false,"numeric_guard_revision":"independent_fp64_deletion"} | 5 |  | RUN-008 | 替代被float32结合律误拦的C1 | 59.543354448519956 | stop_no_gain_shared_transform |  |
| RUN-009 | rpr-role-separated-guard-retry-seed5 | innovation | completed | {"condition":"rpr_role_separated","rank":32,"gate_init":0.1,"role_specific_scales":true,"weight_bounds":[0.1,0.3],"numeric_guard_revision":"independent_fp64_deletion"} | 5 |  | RUN-009 | 替代被float32结合律误拦的M1 | 51.8382476781668 | stop_no_gain |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
