# 实现记录

```yaml
experiment_id: V5-ABLATION-006
implementation_status: review_pending
review_tier: review-1
change_type: config_only
formal_evidence: true
not_confirmation_evidence: true
formal_runtime_backend: server_detached_role_only
```

本实验不修改模型、训练入口或评估代码，只复制 V5 基础配置并生成 16 份 RUN 快照。CE-ONLY 关闭五项辅助损失；BMDD-OFF 和 CONSIST-OFF 各只改一个系数；LOCAL-AUX-OFF 关闭 `consist/bmdd/mpp/neg`，同时明确 topology 保持 0.1。

两个种子使用 5 和 17，repeat 2 只指同候选、同 seed 的 repeat 1。两种子双重复不是 confirmation。物理 GPU 0 只写在服务器计划，配置内设备保持 `cuda:0`。

专项测试、helper 定向测试、参数矩阵、母版绑定、边界审计和源码 blob 检查通过后，最终 HEAD 才能作为后续 `run_commit`；失败时保持不训练，不改写历史。
