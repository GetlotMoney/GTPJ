# Playbook: Confirmation

Use for reproducing or confirming a result.

## Read

```text
START_HERE.md
WORKFLOW_KERNEL.md
experiment_protocol.md
quality_gate.md
ARTIFACT_REGISTRATION.md when raw artifacts are produced
```

## Agents

Default formal set:

```text
Coordinator
Runner Monitor
Log Analyst
Evidence Quality Checker
Result Comparator
```

## Repeat Rule

Default confirmation size is 3 repeats.

If repeats pass:

```text
official single = best repeat
reported stability = mean / min / max
```

Do not hide weak repeats. Stability remains part of the official evidence.

## Outputs

Version-level confirmation:

```text
experiments/vX/confirmation/
```

Trial-internal confirmation:

```text
experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md
attempts/ATTEMPT-xxx/
```
