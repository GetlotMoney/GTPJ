# Workflow Version

```yaml
current_workflow_version: workflow-v2-runtime-gate
next_target: workflow-v2
workflow_v2_status: evidence_state_machine_plus_agent_runtime_gate
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
right_sidebar_temporary_agents
```

The evidence state machine records state changes. The agent runtime gate decides whether
a formal Runner is allowed to start.
