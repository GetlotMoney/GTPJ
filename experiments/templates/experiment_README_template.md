# 实验

```text
experiment_id:
version:
base_template_id: FRAMEWORK-VX
base_template_tag: vX
base_template_commit:
template_registry_commit:
template_ledger: experiments/vX/TEMPLATE.yaml
experiment_binding: EXPERIMENT.yaml
branch_source: exact_template_commit
candidate_family: none
target_framework: none
candidate_framework_status: not_applicable
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
`EXPERIMENT.yaml` 同时绑定 `FRAMEWORK-VX`、Tag、准确 commit 和登记它的 `template_registry_commit`。
`framework/vX` 本身就是最简模板；新实验分支必须从准确框架提交独立分叉，命名为
`exp/vX/<type>/<experiment-id>-<slug>`；实验代码不得并回正式框架，也不得从另一项实验接着改。结果写回该框架的四类账本，再同步
`main` 总索引。

若 innovation 只是面向未来框架的尝试，填写 `candidate_family`、`target_framework` 和
`candidate_framework_status: attempt_only`。这只表示候选归属，不代表目标框架已经注册；
正式 `framework/vY` 与 `vY` Tag 仍须 confirmation、质量门和 owner 接纳。

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
