# ATTEMPT-016 Pre-Run Plan

## 目标

复现 ATTEMPT-015 中已经达到 H>=75 的两个 tune single，验证它们能否在相同 seed=5 和相同配置下再次达到原水平。

## 计划

| 项目 | 值 |
|---|---|
| run_id | RUN-20260708-0005-h76-hotspot-top2-restore10-exact-repeat-2gpu |
| profile | h76-hotspot-top2-restore10-exact-repeat |
| jobs | 10 |
| GPUs | 0,1 |
| source_seed | 5 |
| max_repeat_per_candidate | 5 |
| local_batch_dir | .gtpj_runtime/batches/RUN-20260708-0005-h76-hotspot-top2-restore10-exact-repeat-2gpu |
| server_batch_dir | /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260708-0005-h76-hotspot-top2-restore10-exact-repeat-2gpu |

## 复现规则

```yaml
repeat_type: exact_repeat
original_seed: 5
max_attempts: 5
max_attempts_hard_cap: true
early_stop_on_best_hit: true
restore_target_H: per_job_source_H
near_miss_tolerance_H: 0.2
near_miss_not_restored: true
seed_change_allowed: false
not_confirmation_evidence: false
```

## 启动前检查

- `validate-agent-runtime` 必须通过。
- `multi-agent-preflight` 必须通过。
- `agent-cleanup-plan` 必须显示 no named threads。
- 本地 `validate`、`validate-workflow-consistency`、`git diff --check` 必须通过。
- 服务器启动前必须确认 GPU 空闲、同 run id 无旧进程、目标目录未污染。

## 失败排除

`RUN-20260708-0004-h76-hotspot-top2-restore10-exact-repeat-2gpu` 已归类为 runner environment failed：它使用默认 `python + conda_env`，远端非交互环境找不到 `conda`，所有 job 在训练前失败，不作为方法或复现证据。有效计划改为 `RUN-20260708-0005...`，并固定 `/data/lby/.conda/envs/dvsr_gpu/bin/python`。
