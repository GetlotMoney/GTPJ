# Campaign Plan

## Scope

This campaign validates the new workflow-v2 agent runtime hard gate with a small formal mixed experiment:

```text
2 innovation probes + 8 tune jobs
```

The method scope stays inside `IDEA-0003 / TRIAL-001 Dynamic Residual Routing`.

## Candidate Set

Profile:

```text
workflow-v2-2innov-8tune
```

Innovation probes:

1. `innov_local_direction_sample_h48_l0.06_w0.50_a0.003`
2. `innov_direction_pse_class_h48_w0.50_p0.55_a0.003`

Tune jobs:

1. `tune_direction_h48_w0.475_a0.003`
2. `tune_direction_h48_w0.525_a0.003`
3. `tune_direction_h48_w0.50_a0.001`
4. `tune_direction_h48_w0.50_a0.005`
5. `tune_direction_h40_w0.50_a0.003`
6. `tune_direction_h56_w0.50_a0.003`
7. `tune_direction_class_h48_w0.50_a0.003`
8. `tune_direction_h48_w0.45_a0.004`

## Boundaries

- No new forward path, loss, data split, label mapping, metric semantics, or class order changes.
- The two innovation probes are combinations of existing legal dynamic routing switches.
- `dynamic_pse_mode=sample` is forbidden.
- This campaign cannot promote a new model version by itself.
- Best single must be separated from repeat mean and confirmation evidence.

## Runtime

Planned run id:

```text
RUN-20260702-0003-mixed2innov8tune-2gpu
```

The formal Runner may start only after:

```text
python workflow/gtpj_workflow.py validate-agent-runtime --path experiments/campaigns/CAMP-20260702-workflow-v2-2innov8tune/agent_runtime.yaml
```

and after a clean freeze commit has been synced to `lab4090`.
