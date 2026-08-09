# Agent Summary

```text
experiment_id: CONFIRM-001
run_id:
base_version: v5
code_branch: exp/v5/confirmation/confirm-001-v5-code-equivalence
code_commit:
activation_mode:
agent_instance_mode: named_owner_thread
lifecycle: workflow_scoped
activation_reason:
required_roles:
required_real_agents:
agent_persistent_threads: none
agent_set: Coordinator, Runner, Log Analyst, Quality Checker
serial_agents: Coordinator -> Runner -> Coordinator
parallel_agents: Log Analyst + Quality Checker after/around run evidence collection
disabled_agents: Reader/Planner, Implementer, Interface Checker, Reviewer, Result Analyst
named_threads: workflow-scoped named Codex role threads
tool_support:
memory_policy:
memory_used:
memory_sources:
persistent_thread_ids: none
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
runtime_state:
warehouse_report_artifacts:
final_decision: pending
review_rounds:
temporary_agents:
```

## Coordinator

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
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

## Reader/Planner

仅在 paper intake、idea discovery、tune suggestion、innovation/module trial 或需要读取论文/来源证据时填写。

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
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

## Implementer

仅在代码、配置、模块开关、loss、eval 或数据流发生实现改动时填写。

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
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

## Runner

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
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

## Log Analyst

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
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

## Quality Checker

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
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

## Interface Checker

仅在代码、接口、loss、eval、label mapping、seen/unseen split、class order、logits shape 或 metric semantics 可能变化时填写。

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
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

## Result Analyst

在 tune、ablation、confirmation、innovation/module trial 或 promotion 需要结果比较时填写。

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
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

## Reviewer

仅在 innovation、争议结果、promotion 或 owner 明确要求独立 review 时填写。

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
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
