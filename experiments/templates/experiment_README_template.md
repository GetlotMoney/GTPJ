# 实验

```text
experiment_id:
version:
base_template_id: MODEL-VX-TEMPLATE-VN
base_template_tag:
base_template_commit:
template_registry_commit:
template_ledger: experiments/vX/TEMPLATE.yaml
experiment_binding: EXPERIMENT.yaml
branch_source: exact_template_commit
run_commit:
dirty_state:
config:
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
attempt_id:
failure_stage:
decision:
promotion_decision:
evidence_level:
result_status:
best_observed_H:
confirmed_H:
confirmation_status:
```

## 问题

说明这次实验要回答的具体问题。先读取所属框架的 `TEMPLATE.yaml`，再由本目录的
`EXPERIMENT.yaml` 同时绑定母版编号、Tag、准确 commit 和登记它的 `template_registry_commit`。
母版代码提交与管理登记提交是两个对象；新实验分支必须从母版代码 commit 独立开出，命名为
`exp/vX/<type>/<experiment-id>-<slug>`；不得从另一项实验接着改。结果写回该框架的四类账本，再同步
`main` 总索引。

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
