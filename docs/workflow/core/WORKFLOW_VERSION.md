# Workflow Version

```yaml
current_workflow_version: SKILL-GTPJ-WORKFLOW-V2.1
previous_workflow_version: workflow-v2-runtime-gate
workflow_v2_status: evidence_state_machine_plus_agent_runtime_gate_plus_preflight_plus_parameter_matrix
model_version_scope: separate_from_v1_v2_v3_v4_v5
```

## Version Meaning

```text
model vX:
  method/framework/baseline state.

workflow-vX:
  experiment governance, agent orchestration, evidence routing, and helper checks.
```

`workflow-v2` does not mean model `v6`. It adds the evidence routing kernel on top of the already usable slim workflow.

## workflow-v2 Kernel

```text
tamper-evident append-only evidence state machine
```

Minimum executable layer:

```text
schemas/evidence_routing.schema.yaml
TRANSITIONS.jsonl
evidence_routing.yaml
validate-evidence-routing
```

Runtime gate layer:

```text
AGENT_RUNTIME_HARD_GATE.md
agent_runtime.yaml
validate-agent-runtime
multi-agent-preflight
formal_runner_allowed
formal_evidence_allowed
multi_agent_preflight
agent_instance_status
agent_status_refs
agent_output_refs
left_sidebar_named_threads
thread_archive_policy: archive_completed_threads_on_stage_end
archive_completed_threads_on_stage_end
```

The evidence state machine records state changes. The agent runtime gate decides whether
a formal Runner is allowed to start and whether the owner-visible right sidebar stays
limited to the current active roles.

## SKILL-GTPJ-WORKFLOW-V2.1：参数矩阵规则

这次升级改的是工作流规则，不是模型版本。新实验必须先有一张逐任务的
`PARAMETER_MATRIX.csv`，再提交冻结并生成正式批次；`PARAMETER_MATRIX.md`
是同一张表的阅读版。相同完整配置必须标明是复跑，避免以后不知不觉重复调参。

唯一正式说明在：`docs/workflow/protocols/parameter_matrix_protocol.md`。
