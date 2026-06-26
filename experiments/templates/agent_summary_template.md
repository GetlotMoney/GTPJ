# Agent Summary

```text
experiment_id:
run_id:
base_version:
code_branch:
code_commit:
agent_set:
serial_agents:
parallel_agents:
disabled_agents:
runtime_state:
warehouse_report_artifacts:
final_decision:
```

## Coordinator

```text
role:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
```

## Runner

```text
role:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
```

## Log Analyst

```text
role:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
```

## Quality Checker

```text
role:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
```

## Interface Checker

仅在代码、接口、loss、eval、label mapping、seen/unseen split、class order、logits shape 或 metric semantics 可能变化时填写。

```text
role:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
```

## Reviewer / Result Analyst

仅在 innovation、ablation 或 promotion 需要独立审查时填写。

```text
role:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
```

