# Playbook: Ablation

Use for removing, replacing, disabling, or isolating a component.

## Read

```text
START_HERE.md
WORKFLOW_KERNEL.md
experiment_protocol.md
code_interface_contract.md
ARTIFACT_REGISTRATION.md when raw artifacts are produced
```

If the ablation is inside a module trial, also read:

```text
module_trial_protocol.md
```

## Agents

Default formal set:

```text
Coordinator
Reader/Planner
Interface Checker
Runner Monitor
Log Analyst
Evidence Quality Checker
Result Comparator
```

Add `Implementer` only if code changes are required.

## Stop Gates

- Label mapping, seen/unseen split, class order, logits shape, or metric semantics are unclear.
- Ablation silently changes more than the intended component.
- Result would be compared against an unconfirmed baseline without marking that boundary.
