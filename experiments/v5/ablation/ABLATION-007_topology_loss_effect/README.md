# V5-ABLATION-007：Topology 损失作用

```yaml
experiment_id: V5-ABLATION-007
status: pre_run_gated
campaign_id: CAMP-20260809-v5-ablation100
base_template_id: MODEL-V5-TEMPLATE-V1
code_ref: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
implementation_status: review_pending
review_tier: review-1
formal_runtime_backend: server_detached_role_only
```

本实验只把 `lambda_topo_pearson` 从 0.1 改为 0，候选名为 TOPO-OFF；其余 V5 配置保持不变。四行顺序为 (seed, repeat) = (5,1)、(5,2)、(17,1)、(17,2)。

两种子双重复不是 confirmation，只能回答 topology Pearson 损失在这组搜索条件下的影响。基础 `config.yaml` 与 V5 模板逐字相同；RUN 配置只允许候选字段和 `random_seed` 变化，进程内设备始终为 `cuda:0`。模板提交写入 `code_ref`，最终冻结 HEAD 由后续 campaign 作为 `run_commit`。

当前没有训练、指标、receipt、日志、checkpoint 或结果文件。
