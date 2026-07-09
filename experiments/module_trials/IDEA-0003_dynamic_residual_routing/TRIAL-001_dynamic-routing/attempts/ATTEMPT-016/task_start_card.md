# ATTEMPT-016 Task Start Card

## 结论

本轮做 ATTEMPT-015 top2 的严格复现实验：只复现原配置、原 seed=5，不换 seed，不改参数。运行模式暂定为 `server_frozen_runner`，因此不创建左侧命名线程，也不启动右侧 temporary subagents。

## 路由

| 项目 | 值 |
|---|---|
| task_type | confirmation |
| repeat_type | exact_repeat |
| subject_id | ATTEMPT-016 |
| source_attempt | ATTEMPT-015 |
| source_run | RUN-20260708-0003-h76-hotspot100-tune-live-multiagent-2gpu |
| target_profile | h76-hotspot-top2-restore10-exact-repeat |
| planned_jobs | 10 |
| workflow_mode | server_frozen_runner |
| activation_mode | role_only |
| formal_runtime_backend | server_detached_role_only |
| thread_creation_allowed | false |

## 候选

| Candidate | Source job | Config | Source H | Restore target |
|---|---|---|---:|---:|
| A015DR004 | DR-004 | direction_sample_h48_w0.495_a0.003 | 75.04 | 75.04 |
| A015DR035 | DR-035 | direction_sample_h48_w0.525_a0.0035 | 75.00 | 75.00 |

## 硬规则

- 每个候选最多 5 次 exact repeat。
- 只有 `H >= restore_target_H` 才算 restored，并只跳过该候选剩余 repeat。
- 接近但未达到只能记为 `near_miss_not_restored`，不能确认，不能 promotion。
- 本轮不改变模型代码、数据、split、label mapping、class order、logits shape 或 metric 语义。

