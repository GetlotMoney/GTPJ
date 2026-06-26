# 实验

```text
experiment_id:
version:
base_code_tag:
branch_source: main
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
```

## 问题

说明这次实验要回答的具体问题。`base_code_tag` 是代码来源；临时分支默认从当前
`main` 开出以继承最新账本。历史版本 tune、ablation、confirmation 可以从目标 tag
开只运行代码的临时分支，跑完回当前 `main` 入账。

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
