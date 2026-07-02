# Workflow Changelog

## workflow-v1

Original broad workflow protocol set.

## workflow-v1.5

Slim owner-facing workflow:

```text
START_HERE.md
WORKFLOW_KERNEL.md
task playbooks
TASK_START_MINI.md
TASK_START_CARD.md
```

Daily workflow became usable without reading the whole protocol directory.

## workflow-v2

Evidence routing kernel:

```text
subject_id / subject_type
TRANSITIONS.jsonl
evidence_routing.yaml
transition hash chain
agent propose/check/apply permissions
GZSL hard rules
innovation hypothesis decomposition
validate-evidence-routing
```

The goal is not more documentation. The goal is machine-checkable state transition and clear authority refs.

## workflow-v2 runtime gate

Added the formal Runner start hard gate:

```text
AGENT_RUNTIME_HARD_GATE.md
agent_runtime.yaml
validate-agent-runtime
right_sidebar_temporary_agents
```

Formal experiments now require real temporary agents with recorded `agent_instance_id`
and pre-run allow/check before Runner starts. Coordinator single-window execution is
only candidate/debug evidence, not a complete real_multi_agent workflow.
