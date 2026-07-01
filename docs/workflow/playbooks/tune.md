# Playbook: Tune

Use for parameter, seed, epoch, batch, loss weight, or narrow config search that does not change method semantics.

## Read

```text
START_HERE.md
WORKFLOW_KERNEL.md
experiment_protocol.md
ARTIFACT_REGISTRATION.md when raw artifacts are produced
```

If tuning is inside a module trial, also read:

```text
module_trial_protocol.md
```

## Agents

Formal tune defaults to `real_multi_agent`:

```text
Coordinator
Runner Monitor
Log Analyst
Evidence Quality Checker
Result Comparator
```

## Outputs

Version-level tune:

```text
experiments/vX/tune/
```

Trial-internal tune:

```text
experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md
experiments/module_trials/.../TRIAL-xxx/attempts/ATTEMPT-xxx/
```

Raw logs and checkpoints stay in Warehouse.

## Decision Rule

Tune-only gains do not create a new `vX`.

If a tuned config is important, confirm with 3 repeats before calling it formal.
