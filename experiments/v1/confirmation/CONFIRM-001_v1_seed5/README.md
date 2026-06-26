# CONFIRM-001_v1_seed5

```text
experiment_id: CONFIRM-001
kind: confirmation
version: v1
base_code_tag: v1
branch_source: main
code_branch: exp/v1-confirm-001-v1-seed5
runtime: OpenClaw preferred / Codex compatible
quality_check_mode: STRICT
run_id: RUN-20260626-141736-confirm-v1-seed5
run_commit: 7fe71d36bcda5652c119eea7edf72a78106a6614
dirty_state: false
config: config.yaml
command: conda run -n dvsr_gpu python train_GTPJ_CUB.py --config experiments/v1/confirmation/CONFIRM-001_v1_seed5/config.yaml
seed: 5
python_env: conda:dvsr_gpu python=3.10.20 torch=2.11.0+cu128
torch_cuda: cuda_available=true; gpu=NVIDIA GeForce RTX 5070 Ti; device=cuda:0
dataset_split: CUB standard_v1
cache_fingerprint: train_patch=6243583333@2026-05-17T02:09:11; train_cls=21680339@2026-05-17T02:09:06; train_labels=29449@2026-05-18T04:48:05; text_gpt55=616075@2026-06-11T13:41:48; test_seen_patch=1560675653@2026-05-18T04:50:04; test_unseen_patch=2625013135@2026-05-18T04:52:45
log_artifact_id:
log_uri:
log_sha256:
log_size_bytes:
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
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
status: ready_to_run
```

## 问题

在固定 `v1` 配置、seed=5、CUB standard_v1 split、标准 GZSL U/S/H/ZS 评估口径下，完整复现当前 GTPJ-v1 baseline，并确认指标是否仍可信。

## 运行前检查

- [x] 临时分支来源符合实验类型；当前版本从 `main` 切出，历史版本可从 `v1` tag 开只运行分支。
- [x] `base_code_tag: v1` 和 `branch_source` 已记录。
- [x] 配置复制自 `experiments/v1/config.yaml`。
- [x] 只改变声明过的变量或开关。本 confirmation 不改配置、不改模型结构。
- [ ] Runner 开始前已用 `runner-lock` 占用 GPU；结束、失败或人工停止后已 `runner-unlock`。
- [ ] 原始日志、checkpoint、generated figures 写入 Warehouse，不写入 GitHub。
- [ ] `manifest.yaml` 中的 artifact URI、hash、size 能对应外部资产。
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
