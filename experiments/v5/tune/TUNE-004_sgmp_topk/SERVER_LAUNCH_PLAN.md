# 服务器启动计划

```yaml
campaign_id: CAMP-20260809-v5-ablation100
experiment_id: V5-TUNE-004
workflow_mode: server_frozen_runner
formal_runtime_backend: server_detached_role_only
physical_gpu: 1
process_device: cuda:0
run_count: 4
run_commit: final_pre_run_freeze_HEAD
```

- 物理 GPU 1 由后续 campaign 映射，配置内部仍写 `cuda:0`。
- RUN-001..004 均为 SGMP-TOPK16，按两个 seed 各双重复排列。
- 启动前核对工作树 clean、HEAD、数据与划分身份、GPU 可见及输出目录不存在。
- TUNE003 与 TUNE004 绝不合并；`K16+topk16` 会被 `N-1` 上限截成 15，该组合不在本轮。
