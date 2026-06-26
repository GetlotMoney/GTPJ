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
attempts_table: ATTEMPTS.md
best_attempt_id:
best_attempt_dir:
run_config:
log_artifact_id:
log_uri:
log_sha256:
log_size_bytes:
manifest:
result_yaml:
result_md:
agent_summary: agent_summary.md
trial_decision:
promote_to:
promotion_decision:
```

`code_branch` is cut from current `main`. `base_code_tag` is the true code source.

## Changed Files

| File | Change | Code layer |
|---|---|---|

## Result

| Attempt ID | Dataset | Seed | U | S | H | ZS | Best epoch | Log artifact |
|---|---|---:|---:|---:|---:|---:|---:|---|

## Attempts

Detailed attempt records live in `ATTEMPTS.md`. Reproducibility evidence for each attempt should live in `attempts/ATTEMPT-xxx/`, unless this is a legacy single-attempt trial.

## Promotion Gate

Fill only when `trial_decision: promote`:

```text
parent_version:
parent_tag:
baseline_H:
trial_H:
delta_H:
same_seed_control:
multi_seed_required:
config_snapshot:
log_artifact_id:
log_uri:
log_sha256:
eval_contract_changed: yes/no
switch_off_equivalent: yes/no
version_tree_updated: yes/no
promotion_decision: PENDING
```
