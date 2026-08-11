# 服务器启动计划

本文件只冻结后续 campaign 的 GPU 分配，不在本任务中启动训练。

```yaml
campaign_id: CAMP-20260809-v5-ablation100
experiment_id: V5-ABLATION-006
workflow_mode: server_frozen_runner
formal_runtime_backend: server_detached_role_only
physical_gpu: 0
process_device: cuda:0
run_count: 16
run_commit: final_pre_run_freeze_HEAD
```

- 物理 GPU 0 由后续 campaign 映射；配置内部仍写 `cuda:0`。
- RUN-001..004：CE-ONLY；RUN-005..008：BMDD-OFF；RUN-009..012：CONSIST-OFF；RUN-013..016：LOCAL-AUX-OFF。
- 启动前核对工作树 clean、HEAD、数据与划分身份、GPU 可见性及输出目录不存在。
- 每个 RUN 使用独立配置和输出目录，禁止覆盖历史结果。
