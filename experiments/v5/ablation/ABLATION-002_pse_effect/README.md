# ABLATION-002_pse_effect

```text
experiment_id: ABLATION-002
kind: ablation
version: v5
base_code_tag: model/v5-template-v1
branch_source: exact_template_commit
code_branch: exp/v5/ablation/ablation-002-pse-effect
runtime: OpenClaw preferred / Codex compatible
quality_check_mode: STANDARD
run_commit:
dirty_state:
config: configs/RUN-001.yaml
command:
seed:
python_env:
torch_cuda:
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
status: planned
```

## 问题

描述这个实验要回答的精确问题。

本实验只回答：在完整 V5 中关闭 PSE 后，CUB GZSL 的 U、S、H、ZS 会怎样变化。

## 消融合同

```text
disabled_module: PSE（Progressive Semantic Enhancement）
switch_key: ablation_disable_pse=true
off_path: 不创建 PSE 模块；seen 文本直接使用归一化后的句向量平均
unchanged: ICSA、FGVD、BVSA、SGMP、局部融合、全部损失、数据、类别顺序、评估和训练日程
paired_full_baseline:
  seed 5  -> V5-ABLATION-001/RUN-007
  seed 17 -> V5-ABLATION-001/RUN-013
  seed 29 -> V5-ABLATION-001/RUN-014
baseline_reuse_reason: 母版提交、原始 V5 配置、数据清单、评估口径和三个 seed 一致；本分支默认开关路径已通过 V5 契约测试。
```

## 运行前检查

- [ ] 实验分支从 `framework/v5` 切出，并按 `exp/v5/<type>/<experiment-id>-<slug>` 命名。
- [ ] `base_code_tag: v5` 和 `branch_source` 已记录。
- [ ] 配置复制自 `experiments/v5/config.yaml`。
- [ ] 只改变声明过的变量或开关。
- [ ] Runner 开始前已用 `runner-lock` 占用 GPU；结束、失败或人工停止后已 `runner-unlock`。
- [ ] 原始日志、checkpoint、generated figures 写入 Warehouse，不写入 GitHub。
- [ ] `manifest.yaml` 中的 artifact URI、hash、size 能对应外部资产。
- [ ] `agent_summary.md` 已记录参与 agents、检查范围、发现和结论。
- [ ] `quality_check.md` 已创建；实验完成后再填写 decision。

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

本次唯一算法变量是 `ablation_disable_pse=true`；不是把权重设为 0，也不会保留一个仍参与前向或反向传播的 PSE 模块。

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
