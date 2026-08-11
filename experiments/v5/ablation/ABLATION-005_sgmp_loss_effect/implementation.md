# 实现记录

```yaml
experiment_id: V5-ABLATION-005
implementation_status: review_pending
review_tier: review-1
change_type: config_only
formal_evidence: true
not_confirmation_evidence: true
formal_runtime_backend: server_detached_role_only
```

## 最小实现

本实验不修改模型、训练入口或评估代码，只复制 V5 基础配置并生成 12 份 RUN 快照。允许变化范围如下：

- MPP-OFF：只把 `lambda_mpp` 从 0.05 改为 0；
- NEG-OFF：只把 `lambda_neg` 从 0.01 改为 0；
- SGMP-ALL-OFF：只把上述两个系数改为 0；
- 两个种子使用 5 和 17；repeat 2 只指向同候选、同 seed 的 repeat 1。

MPP-OFF 只是系数消融，NEG 仍使用 pos_sim.detach，因此不得把它解释为移除了 SGMP。两种子双重复不是 confirmation。物理 GPU 1 只记录在 `SERVER_LAUNCH_PLAN.md`，所有配置的进程内设备保持 `cuda:0`。

## 验证与回退

专项测试、helper 定向测试、参数矩阵校验、母版绑定、边界审计和源码 blob 检查全部通过后，最终 HEAD 才能作为后续 `run_commit`。若任一检查失败，保持不训练并回到本分支修正；不改写已有提交历史。
