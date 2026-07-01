# Playbook: Autonomous Research Campaign

Use for the long-term target where the owner provides sources, evaluation standards, safety boundaries, and experiment standards, then workflow manages the rest.

## Read

```text
START_HERE.md
WORKFLOW_KERNEL.md
WORKFLOW_ROUTER.md
autonomous_research_campaign.md
mixed_experiment_campaign_protocol.md when multiple experiment types are requested
```

## Inputs From Owner

```text
paper/source scope
evaluation metric and baseline
safety boundaries
experiment budget and stop conditions
promotion standard
final deliverable standard
```

## Workflow Owns

```text
paper intake
source review
idea discovery and ranking
experiment planning
code changes
server runs
evidence registration
repeat/confirmation
promotion proposal
final result and code report
```

## Agent Shape

Use campaign-scoped real multi-agent. Add persistent threads only for visible long-running Coordinator/Monitor continuity when explicitly useful.

Formal evidence remains file-backed.

## Final Deliverables

```text
final experiment table
best confirmed framework and parameters
failed directions and why
code/config diff summary
Warehouse artifact index
promotion recommendation
remaining risks
```
