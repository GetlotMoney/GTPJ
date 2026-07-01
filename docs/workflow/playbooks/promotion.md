# Playbook: Promotion

Use when a result may become a new baseline/version.

## Read

```text
START_HERE.md
WORKFLOW_KERNEL.md
promotion.md
quality_gate.md
versioning.md
git_policy.md
```

## Agents

Promotion requires formal independent checking:

```text
Coordinator
Evidence Quality Checker
Interface Checker
Result Comparator
Reviewer
```

## Required Evidence

```text
promotion_decision: promote
complete manifest/result/quality/interface evidence
repeat or confirmation evidence when required
target version declared
no unresolved hard gate
```

## Boundary

Tuning alone does not create a new `vX`.

Promotion may create local files, commits, and local tags if the protocol requires it.

Do not push unless the owner explicitly asks.
