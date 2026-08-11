# 实现记录

```yaml
experiment_id: V5-ABLATION-007
implementation_status: review_pending
review_tier: review-1
change_type: config_only
formal_evidence: true
not_confirmation_evidence: true
formal_runtime_backend: server_detached_role_only
```

只复制 V5 配置并生成四份 TOPO-OFF 快照：`lambda_topo_pearson=0`，另加对应 `random_seed`。不修改模型、训练入口或评估代码。repeat 2 只指同 seed 的 repeat 1；两种子双重复不是 confirmation。物理 GPU 1 只写服务器计划，进程内设备保持 `cuda:0`。

专项测试、helper 定向测试、矩阵、母版绑定、边界审计和源码 blob 检查通过后，最终 HEAD 才能作为后续 `run_commit`。
