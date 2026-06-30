# Agent Summary

```text
experiment_id:
run_id:
base_version:
code_branch:
code_commit:
activation_mode:
agent_instance_mode:
activation_reason:
required_roles:
required_real_agents:
agent_persistent_threads:
agent_set:
serial_agents:
parallel_agents:
disabled_agents:
temporary_subagents:
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

## Coordinator

```text
role:
agent_instance_mode:
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
independence_scope:
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

## Reader/Planner

仅在 paper intake、idea discovery、tune suggestion、innovation/module trial 或需要读取论文/来源证据时填写。

```text
role:
agent_instance_mode:
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
independence_scope:
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

## Implementer

仅在代码、配置、模块开关、loss、eval 或数据流发生实现改动时填写。

```text
role:
agent_instance_mode:
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
independence_scope:
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

## Runner

```text
role:
agent_instance_mode:
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
independence_scope:
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

## Log Analyst

```text
role:
agent_instance_mode:
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
independence_scope:
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

## Quality Checker

```text
role:
agent_instance_mode:
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
independence_scope:
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

## Interface Checker

仅在代码、接口、loss、eval、label mapping、seen/unseen split、class order、logits shape 或 metric semantics 可能变化时填写。

```text
role:
agent_instance_mode:
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
independence_scope:
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

## Result Analyst

在 tune、ablation、confirmation、innovation/module trial 或 promotion 需要结果比较时填写。

```text
role:
agent_instance_mode:
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
independence_scope:
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

## Reviewer

仅在 innovation、争议结果、promotion 或 owner 明确要求独立 review 时填写。

```text
role:
agent_instance_mode:
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
independence_scope:
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
