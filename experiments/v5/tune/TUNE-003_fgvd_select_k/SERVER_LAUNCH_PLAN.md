# 服务器启动计划

```yaml
campaign_id: CAMP-20260809-v5-ablation100
experiment_id: V5-TUNE-003
workflow_mode: server_frozen_runner
formal_runtime_backend: server_detached_role_only
physical_gpu: 0
process_device: cuda:0
run_count: 8
run_commit: final_pre_run_freeze_HEAD
```

- 物理 GPU 0 由后续 campaign 映射，配置内部仍写 `cuda:0`。
- RUN-001..004 为 FGVD-K16，RUN-005..008 为 FGVD-K64。
- 启动前核对工作树 clean、HEAD、数据与划分身份、GPU 可见及输出目录不存在。
- `fgvd_select_k` 同时改变 BVSA 和 SGMP 接收的局部块数；TUNE003 与 TUNE004 绝不合并。
- `K16+topk16` 会被 `N-1` 上限截成 15，该组合不在本轮。
