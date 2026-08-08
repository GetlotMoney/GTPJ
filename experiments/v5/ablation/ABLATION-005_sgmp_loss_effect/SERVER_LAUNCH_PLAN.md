# 服务器启动计划

本文件只冻结后续 campaign 的 GPU 分配，不在本任务中启动训练。

```yaml
campaign_id: CAMP-20260809-v5-ablation100
experiment_id: V5-ABLATION-005
workflow_mode: server_frozen_runner
formal_runtime_backend: server_detached_role_only
physical_gpu: 1
process_device: cuda:0
run_count: 12
run_commit: final_pre_run_freeze_HEAD
```

- 物理 GPU 1 由后续 campaign 通过 `CUDA_VISIBLE_DEVICES=1` 映射；配置内部仍写 `cuda:0`。
- RUN-001..004：MPP-OFF；RUN-005..008：NEG-OFF；RUN-009..012：SGMP-ALL-OFF。
- 启动前依次核对：工作树 clean、HEAD 是最终冻结提交、数据与划分身份一致、GPU 可见、每个输出目录不存在。
- 每个 RUN 使用自己的 `configs/RUN-xxx.yaml`，独立输出且禁止覆盖旧目录。
- 本计划不包含训练结果，也不代表 review-1 已通过。
