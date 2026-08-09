# V5-TUNE-004：SGMP top-k

```yaml
experiment_id: V5-TUNE-004
status: pre_run_gated
campaign_id: CAMP-20260809-v5-ablation100
base_template_id: MODEL-V5-TEMPLATE-V1
code_ref: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
implementation_status: review_pending
review_tier: review-1
formal_runtime_backend: server_detached_role_only
```

本实验只把 `sgmp_topk` 设为 16，`fgvd_select_k` 保持模板值 32；四行顺序为 (5,1)、(5,2)、(17,1)、(17,2)。

## 解释边界

TUNE003 与 TUNE004 绝不合并，本轮只判断 SGMP 的 top-k 变化。假设把 FGVD 也改成 K16，`K16+topk16` 会被 `N-1` 上限截成 15；这个组合不在本轮，不能由本实验推断。

两种子双重复不是 confirmation。基础 `config.yaml` 与 V5 模板逐字相同；RUN 配置只允许 `sgmp_topk` 和 `random_seed` 变化，进程内设备为 `cuda:0`。模板提交写入 `code_ref`，最终冻结 HEAD 由后续 campaign 作为 `run_commit`。当前没有训练或结果证据。
