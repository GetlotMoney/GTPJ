# ATTEMPT-002 Pre-Run Plan

```text
attempt_id: ATTEMPT-002
run_id: RUN-20260630-0007-dynroute-dr009-repeat-2gpu
trial: IDEA-0003 / TRIAL-001 Dynamic Residual Routing
base_version: v5
profile: direction-repeat-confirmation
jobs: 50
gpus: 0,1
seed: 5
status: planned
pre_run_freeze_commit: this commit
```

## Purpose

Confirm whether the best partial RUN-0006 direction gate signal is reproducible under the formal
workflow runner. RUN-0006 was stopped after the current round and is not promotion-grade evidence.

## Batch Shape

| Group | Count | Configuration |
|---|---:|---|
| direction_confirmation | 20 | direction sample, hidden 48, anchor 0.005, weight_s2v 0.45 |
| direction_neighbor | 10 | direction sample, hidden 48, anchor 0.005, weight_s2v 0.50 |
| direction_neighbor | 10 | direction sample, hidden 64, anchor 0.010, weight_s2v 0.50 |
| sanity_control | 5 | static v5 control |
| sanity_control | 5 | dynamic routing enabled with all gates fixed |

## Decision Rules

- Promotion discussion only starts if the confirmation mean clearly beats v4 confirmed_H=74.45
  and v5 repeat mean H=74.44 while keeping U/S stable.
- A single high-H job is not enough for promotion.
- If confirmation is noisy or below reference, keep direction routing as an observation and revise
  the next profile around sample-level direction gates.

## Planned Command

```bash
/usr/bin/python3 workflow/gtpj_workflow.py plan-dynamic-routing-batch \
  --trial-dir experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing \
  --run-id RUN-20260630-0007-dynroute-dr009-repeat-2gpu \
  --jobs 50 \
  --profile direction-repeat-confirmation \
  --gpus 0,1 \
  --branch dev/v5-idea-0003-trial-001-dynamic-routing \
  --commit <pre_run_freeze_commit> \
  --git-remote /data/lby/projects/cv_project/_transfer/<bundle>.bundle \
  --server-repo /data/lby/projects/cv_project/GTPJ \
  --warehouse-root /data/lby/projects/cv_project/GTPJ_Warehouse \
  --conda-env direct \
  --python /data/lby/.conda/envs/dvsr_gpu/bin/python \
  --controller-python /usr/bin/python3
```

## Preflight Notes

- Local validation must pass before push.
- Server `audit-boundary` must pass before planning.
- Server `validate` may still fail on historical `.gtpj_runtime` references to old TUNE records;
  that is a known pre-existing runtime preflight exception and must not be counted as ATTEMPT-002
  evidence.
