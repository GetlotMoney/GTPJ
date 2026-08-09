# 实现记录

```yaml
experiment_id: V5-ABLATION-009
implementation_status: review_pending
review_tier: review-1
change_type: config_only
formal_evidence: true
not_confirmation_evidence: true
formal_runtime_backend: server_detached_role_only
```

只复制 V5 配置并生成 8 份快照：S2V-ONLY 使用 `weight_s2v=1.0`，V2S-ONLY 使用 `weight_s2v=0.0`，另加对应 seed。不修改模型、训练入口或评估代码。

该设置只选择最终局部分数方向；两个方向仍计算，BMDD 仍约束，不得称为移除模块。repeat 2 只指同候选、同 seed 的 repeat 1；两种子双重复不是 confirmation。物理 GPU 1 只写服务器计划。

全部机器门通过后，最终 HEAD 才能作为后续 `run_commit`。
