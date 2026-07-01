# Workflow Version

```yaml
current_workflow_version: workflow-v1.5
next_target: workflow-v2
workflow_v2_status: implementing
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
