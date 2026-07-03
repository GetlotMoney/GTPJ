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

## workflow-v2 right-sidebar cleanup

Added the owner-visible agent cleanup rule:

```text
right_sidebar_retention_policy: current_stage_active_only
close_completed_agents_on_stage_end: true
closed_agents_record: AGENT_ACTIVITY.md
```

At workflow or stage closeout, Coordinator must record keep/close lists, persist
completed agent conclusions to `agent_summary.md` / `AGENT_ACTIVITY.md` / result /
quality / issues / memory, then close completed temporary agents. The right sidebar
should show current active roles, not historical windows.

## workflow-v2 formal multi-agent preflight

Tightened the formal evidence rule:

```text
formal_runner_allowed: true
formal_evidence_allowed: true
multi_agent_preflight
agent_instance_status / agent_status_refs / agent_output_refs
multi-agent-preflight helper
```

If real multi-agent cannot be proven, formal Runner start is blocked. `role_only`
and sequential structured review remain useful for read-only triage, drafts and
debug/smoke, but they cannot be promoted into formal evidence after the fact.
The helper now verifies local status/output evidence files for each recorded
temporary sub-agent; Codex tool state must be captured into those files because
the Python helper cannot query hidden chat-tool sandbox state directly.
