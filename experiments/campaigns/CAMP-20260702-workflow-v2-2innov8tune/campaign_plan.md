# Campaign Plan

## Scope

This campaign validates the new workflow-v2 agent runtime hard gate with a small formal mixed experiment:

```text
2 innovation probes + 8 tune jobs
```

The method scope stays inside `IDEA-0003 / TRIAL-001 Dynamic Residual Routing`.

Campaign run map:

```text
campaign_run_map.md
campaign_run_map.html
```

Formal result evidence is not stored in this campaign directory. This campaign
is a routing index; the formal trial-local ledger is:

```text
experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-006/
```

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

Owner-facing work item ids are recorded in `WORK_ITEMS.md`:

```text
INNOV-001..INNOV-002 -> runner jobs DR-001..DR-002
TUNE-001..TUNE-008   -> runner jobs DR-003..DR-010
```

Runner-local `attempt_id` values in server summaries are batch-local and do not
equal GitHub formal `ATTEMPT-xxx` records.

## Boundaries

- No new forward path, loss, data split, label mapping, metric semantics, or class order changes.
- The two innovation probes are combinations of existing legal dynamic routing switches.
- `dynamic_pse_mode=sample` is forbidden.
- This campaign cannot promote a new model version by itself.
- Best single must be separated from repeat mean and confirmation evidence.
- Campaign files must not be used as authoritative H/U/S/ZS sources; use
  ATTEMPT-006 result and quality files instead.

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
