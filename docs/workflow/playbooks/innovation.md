# Playbook: Innovation / Module Trial

Use when the owner asks to open a new module, test a new mechanism, or turn an idea into code.

## Read

```text
START_HERE.md
WORKFLOW_KERNEL.md
idea_tree_protocol.md
module_trial_protocol.md
code_interface_contract.md
innovation_code_review_protocol.md
agent_orchestration.md
agent_report_policy.md
```

## Agents

Formal innovation work requires `real_multi_agent`.

Default set:

```text
Coordinator
Reader/Planner
Implementer
Interface Checker
Runner Monitor
Log Analyst
Evidence Quality Checker
Result Comparator
Reviewer
```

Use one Implementer per code path.

## Review Loop

Keep Review 0-3:

```text
Review 0: idea and interface before coding
Review 1: implementation boundary
Review 2: runtime and evidence readiness
Review 3: result and promotion boundary
```

## Outputs

```text
idea_tree/
experiments/module_trials/<IDEA-ID>/TRIAL-xxx/
GTPJ_Research when long reasoning is needed
GTPJ_Warehouse for raw logs/checkpoints
```

## Stop Gates

- No valid idea id or accepted local heuristic.
- Interface semantics are unclear.
- The attempt changes the implementation hypothesis enough to require a new trial.
- Formal multi-agent support is unavailable and the owner did not accept a debug-only downgrade.
