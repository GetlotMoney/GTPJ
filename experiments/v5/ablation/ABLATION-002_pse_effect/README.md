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
code_snapshot_commit: 47956175d994df33e2ea6047acea0cc60b27e4d9
pre_run_freeze_commit: pending
run_commit: captured_at_launch_from_pre_run_freeze_commit
dirty_state: clean_required_before_formal_launch
config: configs/RUN-001.yaml
campaign: CAMP-20260809-v5-ablation100
command: frozen campaign background controller only (pending implementation and freeze)
launch_status: 控制器完成前不可手工正式启动
seed: RUN-001=5/repeat-1, RUN-002=5/repeat-2, RUN-003=17/repeat-1, RUN-004=17/repeat-2
python_env:
torch_cuda:
physical_gpu_assignment: GPU 0 via CUDA_VISIBLE_DEVICES=0; process uses logical cuda:0
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

本实验只回答：在完整 V5 中关闭 PSE 后，CUB GZSL 的 U、S、H、ZS 会怎样变化。

## 消融合同

```text
disabled_module: PSE（Progressive Semantic Enhancement）
switch_key: ablation_disable_pse=true
off_path: 不创建 PSE 模块；seen 文本直接使用归一化后的句向量平均
unchanged: ICSA、FGVD、BVSA、SGMP、局部融合、全部损失、数据、类别顺序、评估和训练日程
paired_full_baseline:
  seed 5/repeat 1  -> V5-ABLATION-008 中同 seed、同 repeat 的 GL-FULL
  seed 5/repeat 2  -> V5-ABLATION-008 中同 seed、同 repeat 的 GL-FULL
  seed 17/repeat 1 -> V5-ABLATION-008 中同 seed、同 repeat 的 GL-FULL
  seed 17/repeat 2 -> V5-ABLATION-008 中同 seed、同 repeat 的 GL-FULL
baseline_rule: 只与本轮相同种子、相同重复编号的完整 V5 比较，不复用 seed 29，也不把本轮筛查写成正式确认。
```

## 运行前检查

- [x] 分支直接从 `model/v5-template-v1` 对应提交复制，未继承旧实验代码。
- [x] 四份配置固定为 seed 5/17 各两次；除随机种子外训练参数完全一致。
- [x] PSE 固定使用物理 GPU 0；进程内保持逻辑 `cuda:0`。
- [x] 四条参数表随本次 pre-run freeze commit 冻结并通过账本校验。
- [ ] `CAMP-20260809-v5-ablation100` 后台控制器已实现、审核并冻结；完成前不可手工正式启动。
- [ ] 控制器从 frozen campaign map 读取本 RUN 的准确提交与配置，并在 GPU 0 串行调用训练入口。
- [ ] 控制器为每个 RUN 写独立启动/结束 receipt、stdout/stderr 和 Warehouse 目录。
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

本次唯一算法变量是 `ablation_disable_pse=true`；不是把权重设为 0，也不会保留一个仍参与前向或反向传播的 PSE 模块。

## 结果

| 数据集 | Seed | Repeat | U | S | H | ZS | Best epoch | Log artifact |
|---|---:|---:|---:|---:|---:|---:|---:|---|

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
