# Agent Summary（智能体总结）

```text
experiment_id:
run_id:
base_version:
code_branch:
code_commit:
subject_id:
subject_type:
hypothesis_id:
evidence_state:
transition_id:
activation_mode:
agent_instance_mode:
lifecycle:
runner_scope:
formal_runner_allowed:
formal_evidence_allowed:
activation_reason:
required_roles:
required_real_agents:
agent_persistent_threads:
agent_runtime_gate:
named_thread_ids:
agent_instance_status:
agent_status_refs:
agent_output_refs:
role_file_plan:
  input_refs:
  files_reviewed_expected:
  output_ref:
  not_checked_allowed:
agent_cleanup:
  cleanup_plan_command:
  keep_agents:
  archive_agents:
  archive_results:
  unknown_ui_agents:
  archived_threads_record:
ai_cross_review:
  required:
  review_pack:
  rounds_completed:
  claude_code_read_only:
  codex_fixes_or_rebuttals_recorded:
  machine_gates_passed:
  unresolved_blocking_issues:
  validate_command:
  validate_result:
multi_agent_preflight:
  required_threads_created:
  agent_instance_ids_present:
  agent_status_refs_valid:
  independent_outputs_present:
  agent_output_refs_valid:
  pre_run_allow_checks_passed:
  agent_runtime_validated:
ui_visibility:
runner_start_gate:
pre_run_required_checks:
thread_archive_policy:
archive_completed_threads_on_stage_end:
archived_threads_record:
active_agents_after_closeout:
archived_agents_after_closeout:
agent_set:
serial_agents:
parallel_agents:
disabled_agents:
named_threads:
tool_support:
memory_policy:
memory_used:
memory_sources:
persistent_thread_ids:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
runtime_state:
warehouse_report_artifacts:
final_decision:
review_rounds:
temporary_agents:
```

## Evidence Routing（证据路由）

```text
subject_id:
transition_id:
role_key:
agent_instance_id:
lifecycle:
input_refs:
files_reviewed:
checked_inputs:
output_ref:
independence_scope:
rule_checks:
authority_refs:
decision: propose | allow | block | warn
blocking_issues:
non_blocking_warnings:
not_checked:
reason_summary:
```

## Coordinator（总控）

```text
role:
subject_id:
transition_id:
role_key:
agent_instance_id:
agent_instance_mode:
agent_instance_type:
lifecycle:
persistent_thread_id:
named_thread_reason:
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
rule_checks:
authority_refs:
not_checked:
reason_summary:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Reader/Planner（阅读与规划）

仅在 paper intake、idea discovery、tune suggestion、innovation/module trial 或需要读取论文/来源证据时填写。

```text
role:
subject_id:
transition_id:
role_key:
agent_instance_id:
agent_instance_mode:
agent_instance_type:
lifecycle:
persistent_thread_id:
named_thread_reason:
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
rule_checks:
authority_refs:
not_checked:
reason_summary:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Implementer（实现者）

仅在代码、配置、模块开关、loss、eval 或数据流发生实现改动时填写。

```text
role:
subject_id:
transition_id:
role_key:
agent_instance_id:
agent_instance_mode:
agent_instance_type:
lifecycle:
persistent_thread_id:
named_thread_reason:
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
rule_checks:
authority_refs:
not_checked:
reason_summary:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Runner（运行者）

```text
role:
subject_id:
transition_id:
role_key:
agent_instance_id:
agent_instance_mode:
agent_instance_type:
lifecycle:
persistent_thread_id:
named_thread_reason:
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
rule_checks:
authority_refs:
not_checked:
reason_summary:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Log Analyst（日志分析）

```text
role:
subject_id:
transition_id:
role_key:
agent_instance_id:
agent_instance_mode:
agent_instance_type:
lifecycle:
persistent_thread_id:
named_thread_reason:
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
rule_checks:
authority_refs:
not_checked:
reason_summary:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Quality Checker（质量检查）

```text
role:
subject_id:
transition_id:
role_key:
agent_instance_id:
agent_instance_mode:
agent_instance_type:
lifecycle:
persistent_thread_id:
named_thread_reason:
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
rule_checks:
authority_refs:
not_checked:
reason_summary:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Interface Checker（接口检查）

仅在代码、接口、loss、eval、label mapping、seen/unseen split、class order、logits shape 或 metric semantics 可能变化时填写。

```text
role:
subject_id:
transition_id:
role_key:
agent_instance_id:
agent_instance_mode:
agent_instance_type:
lifecycle:
persistent_thread_id:
named_thread_reason:
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
rule_checks:
authority_refs:
not_checked:
reason_summary:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Result Analyst（结果分析）

在 tune、ablation、confirmation、innovation/module trial 或 promotion 需要结果比较时填写。

```text
role:
subject_id:
transition_id:
role_key:
agent_instance_id:
agent_instance_mode:
agent_instance_type:
lifecycle:
persistent_thread_id:
named_thread_reason:
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
rule_checks:
authority_refs:
not_checked:
reason_summary:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Reviewer（复核者）

仅在 innovation、争议结果、promotion 或 owner 明确要求独立 review 时填写。

```text
role:
subject_id:
transition_id:
role_key:
agent_instance_id:
agent_instance_mode:
agent_instance_type:
lifecycle:
persistent_thread_id:
named_thread_reason:
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```
