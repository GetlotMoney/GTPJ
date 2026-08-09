# 实现记录

```yaml
experiment_id: V5-TUNE-004
implementation_status: review_pending
review_tier: review-1
change_type: config_only
formal_evidence: true
not_confirmation_evidence: true
formal_runtime_backend: server_detached_role_only
```

只复制 V5 配置并生成 4 份快照：全部使用 `sgmp_topk=16`，另加对应 seed；`fgvd_select_k=32` 保持不变。不修改模型、训练入口或评估代码。

TUNE003 与 TUNE004 绝不合并。假设组合 `K16+topk16`，会被 `N-1` 上限截成 15，但该组合不在本轮。repeat 2 只指同候选、同 seed 的 repeat 1；两种子双重复不是 confirmation。物理 GPU 1 只写服务器计划。

全部机器门通过后，最终 HEAD 才能作为后续 `run_commit`。
