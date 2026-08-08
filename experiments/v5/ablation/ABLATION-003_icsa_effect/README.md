# ABLATION-003_icsa_effect

```text
experiment_id: ABLATION-003
kind: ablation
version: v5
base_code_tag: model/v5-template-v1
branch_source: exact_template_commit
code_branch: exp/v5/ablation/ablation-003-icsa-effect
runtime: OpenClaw preferred / Codex compatible
quality_check_mode: STANDARD
code_snapshot_commit: 2cbf9664900065955221eb66ba42c562e0bd4c4b
pre_run_freeze_commit: pending
run_commit: captured_at_launch_from_pre_run_freeze_commit
dirty_state: clean_required_before_formal_launch
config: configs/RUN-001.yaml
command: prepare-run-start-receipt (not launched yet)
seed: RUN-001=5, RUN-002=17, RUN-003=29
python_env:
torch_cuda:
physical_gpu_assignment: GPU 1 via CUDA_VISIBLE_DEVICES=1; process uses logical cuda:0
dataset_split:
cache_fingerprint:
log_artifact_id:
log_uri:
log_sha256:
log_size_bytes:
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
agent_summary: agent_summary.md
attempt_id: attempt-001
failure_stage:
U:
S:
H:
ZS:
best_epoch:
decision:
promotion_decision: not_applicable
promote_to:
evidence_level: pending
result_status: pending
best_observed_H:
confirmed_H:
restore_target_H:
near_miss_tolerance_H:
near_miss_not_restored:
confirmation_status: pending
status: pre_run_gated
```

## 问题

描述这个实验要回答的精确问题。

本实验只回答：在完整 V5 中关闭 ICSA 后，CUB GZSL 的 U、S、H、ZS 会怎样变化。

## 消融合同

```text
disabled_module: ICSA（image-conditioned semantic adjustment）
switch_key: ablation_disable_icsa=true
off_path: 不创建 ICSA 网络；不再把图像条件偏移加到 seen 文本原型
unchanged: PSE、FGVD、BVSA、SGMP、局部融合、全部损失、数据、类别顺序、评估和训练日程
paired_full_baseline:
  seed 5  -> V5-ABLATION-001/RUN-007
  seed 17 -> V5-ABLATION-001/RUN-013
  seed 29 -> V5-ABLATION-001/RUN-014
baseline_reuse_reason: 母版提交、原始 V5 配置、数据清单、评估口径和三个 seed 一致；本分支默认开关路径已通过 V5 契约测试。
```

## 运行前检查

- [x] 分支直接从 `model/v5-template-v1` 对应提交复制，未继承旧实验代码。
- [x] 三份配置只改变 `ablation_disable_icsa=true` 和各自的随机种子。
- [x] ICSA 固定使用物理 GPU 1；进程内保持逻辑 `cuda:0`。
- [ ] 三条参数表已冻结并通过账本校验。
- [ ] 在冻结提交后的干净工作树中，通过 `prepare-run-start-receipt` 正式启动。
- [ ] 训练完成后才创建并回填 `manifest.yaml`、`result.yaml`、`result.md`、`quality_check.md`。
- [ ] 原始日志和 checkpoint 只写入 Warehouse，不写入 GitHub。

## 变量

Tune 实验填写：

```text
tuned_parameter:
old_value:
new_value:
search_space:
single_variable:
baseline_H:
trial_H:
delta_H:
promotion_rule:
```

Ablation 实验填写：

```text
disabled_module:
switch_key:
baseline_off_path:
expected_effect:
affected_contracts:
control_result:
ablation_delta:
```

本次唯一算法变量是 `ablation_disable_icsa=true`；不是把 `icsa_ratio` 改为 0，也不会保留一个仍参与前向或反向传播的 ICSA 网络。

## 结果

| 数据集 | Seed | U | S | H | ZS | Best epoch | Log artifact |
|---|---:|---:|---:|---:|---:|---:|---|

## 失败记录

```text
failure_stage:
error_summary:
stderr_or_log:
retry_decision:
impact_on_next_plan:
```

## 结论

待记录。
