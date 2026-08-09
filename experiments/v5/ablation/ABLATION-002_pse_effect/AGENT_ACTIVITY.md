# Agent Activity

subject_id: V5-ABLATION-002
current_stage: pre_run_frozen
activation_mode: role_only
formal_runtime_backend: server_detached_role_only

- 运行前由 runner_monitor、interface_checker、evidence_quality_checker 分别完成只读检查。
- 训练期不创建新的命名任务；统一 campaign 在服务器后台持续写状态。
- 当前没有训练结果；完成后只回填轻量指标和证据索引。
