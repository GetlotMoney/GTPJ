# V5-TUNE-003：FGVD 局部块数量

```yaml
experiment_id: V5-TUNE-003
status: pre_run_gated
campaign_id: CAMP-20260809-v5-ablation100
base_template_id: MODEL-V5-TEMPLATE-V1
code_ref: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
implementation_status: review_pending
review_tier: review-1
formal_runtime_backend: server_detached_role_only
```

本实验只改变 `fgvd_select_k`：FGVD-K16 设为 16，FGVD-K64 设为 64；每个候选四行，顺序为 (5,1)、(5,2)、(17,1)、(17,2)，共 8 行。

## 解释边界

`fgvd_select_k` 同时改变 BVSA 和 SGMP 接收的局部块数，因此结果不能只归因于其中一条局部路径。TUNE003 与 TUNE004 绝不合并；`K16+topk16` 会被 `N-1` 上限截成 15，这个组合不在本轮。

两种子双重复不是 confirmation。基础 `config.yaml` 与 V5 模板逐字相同；RUN 配置只允许 `fgvd_select_k` 和 `random_seed` 变化，进程内设备为 `cuda:0`。模板提交写入 `code_ref`，最终冻结 HEAD 由后续 campaign 作为 `run_commit`。当前没有训练或结果证据。
