# V5-ABLATION-009：BVSA 方向权重作用

```yaml
experiment_id: V5-ABLATION-009
status: pre_run_gated
campaign_id: CAMP-20260809-v5-ablation100
base_template_id: MODEL-V5-TEMPLATE-V1
code_ref: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
implementation_status: review_pending
review_tier: review-1
formal_runtime_backend: server_detached_role_only
```

本实验只改变 `weight_s2v`：S2V-ONLY 设为 1.0，V2S-ONLY 设为 0.0；每个候选四行，顺序为 (5,1)、(5,2)、(17,1)、(17,2)，共 8 行。

## 解释边界

单方向设置只选择最终局部分数方向；两个方向仍计算，BMDD 仍约束，因此不得称为移除模块，也不能声称只执行了一条 BVSA 计算路径。

两种子双重复不是 confirmation。基础 `config.yaml` 与 V5 模板逐字相同；RUN 配置只允许 `weight_s2v` 和 `random_seed` 变化，进程内设备为 `cuda:0`。模板提交写入 `code_ref`，最终冻结 HEAD 由后续 campaign 作为 `run_commit`。当前没有训练或结果证据。
