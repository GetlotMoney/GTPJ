# Playbook: Mixed Experiment Campaign

Use for arbitrary combinations such as `跑10创新+100调参`.

## Read

```text
START_HERE.md
WORKFLOW_KERNEL.md
WORKFLOW_ROUTER.md
mixed_experiment_campaign_protocol.md
one playbook per requested workstream
```

## Structure

```text
campaign
  -> workstream: innovation / tune / ablation / confirmation / debug
    -> task
      -> run
```

Do not create one permanent agent per run.

## Agents

Campaign-level defaults:

```text
Workflow Coordinator
Campaign Planner
Runner Monitor
Result Comparator
Evidence Quality Checker
Warehouse Registrar
```

Add workstream-specific agents from the relevant playbook.

## Scheduling Rule

The Coordinator owns priority and boundaries.

Runner Monitor owns GPU/server execution and failure isolation.

Result Comparator decides which directions need 3-repeat confirmation, based on evidence.

## Required Campaign Report

```text
requested mix
actual planned runs
completed/running/pending/failed
best single
top repeated candidates
confirmed/rejected directions
next 10-50 run plan
checkpoint retention result
```
