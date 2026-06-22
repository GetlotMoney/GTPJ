# TRIAL

```text
trial_id:
idea_id:
idea_title:
base_version:
base_code_tag:
branch_source: main
code_branch: dev/v1-idea-xxxx-trial-001-short-name
code_tag: trial/v1/idea-xxxx/trial-001
code_commit:
changed_files:
run_config:
run_log:
trial_decision:
promote_to:
promotion_decision:
```

`code_branch` 从当前 `main` 开出，`base_code_tag` 才是代码来源。

## 结果

| 数据集 | Seed | U | S | H | ZS | Best epoch |
|---|---:|---:|---:|---:|---:|---:|

## Promotion Gate

仅当 `decision: promote` 时填写：

```text
parent_version:
parent_tag:
baseline_H:
trial_H:
delta_H:
same_seed_control:
multi_seed_required:
config_snapshot:
original_log:
copied_log:
eval_contract_changed: yes/no
switch_off_equivalent: yes/no
version_tree_updated: yes/no
promotion_decision: PENDING
```
