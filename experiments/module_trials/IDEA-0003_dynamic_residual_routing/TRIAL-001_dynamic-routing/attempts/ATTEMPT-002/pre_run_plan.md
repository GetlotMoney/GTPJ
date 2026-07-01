# ATTEMPT-002 Pre-Run Plan

```text
attempt_id: ATTEMPT-002
run_ids:
  - RUN-20260701-0007-dynroute-bs128-exploit50-2gpu
  - RUN-20260701-0008-dynroute-bs128-bold50-2gpu
trial: IDEA-0003 / TRIAL-001 Dynamic Residual Routing
base_version: v5
batch_size: 128
profiles:
  - direction-exploit-followup
  - dynamic-bold-followup
jobs: 100
gpus: 0,1
seed: 5
status: planned
pre_run_freeze_commit: this commit
```

## Purpose

Run the next dynamic routing search with `batch_size=128` to use the available RTX 4090 memory
while keeping the existing 50-job workflow runner unchanged. The batch is intentionally split
into two workflow batches:

- exploit 50: follow the current stronger direction/local/PSE signal near the best observed region.
- bold 50: explore wider direction, PSE, local, ICSA-safe, and combination settings.

The interrupted bs=64 `RUN-20260701-0005` / `RUN-20260701-0006` sequence is superseded and must
not be used as formal evidence.

## Batch Shape

| Batch | Profile | Count | Configuration Focus |
|---|---|---:|---|
| 1 | `direction-exploit-followup` | 50 | direction microgrid, local-direction microgrid, direction-PSE microgrid |
| 2 | `dynamic-bold-followup` | 50 | bold direction/PSE/local/ICSA-safe/combination search |

## Batch Size Rationale

- Current bs=64 uses about 4.75 GiB per GPU.
- Conservative linear estimate puts bs=128 at about 9.5 GiB, leaving large headroom on 24 GiB 4090 cards.
- bs=128 halves optimizer steps per epoch versus bs=64, so it is a planned batch-size intervention and must not
  be mixed with bs=64 results in the same evidence summary.

## Decision Rules

- First compare within bs=128: best single, top cluster consistency, U/S balance, failures, and best epoch.
- Then compare against references as provisional evidence only: `v3/CONFIRM-001 local-v3-054` confirmed_H=74.47 and v5 repeat mean H=74.44.
- Promotion discussion only starts if bs=128 repeat or cluster evidence clearly beats both references while keeping U/S stable.
- A single high-H job is not enough for promotion.

## Planned Commands

```bash
/usr/bin/python3 workflow/gtpj_workflow.py plan-dynamic-routing-batch \
  --trial-dir experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing \
  --run-id RUN-20260701-0007-dynroute-bs128-exploit50-2gpu \
  --jobs 50 \
  --profile direction-exploit-followup \
  --gpus 0,1 \
  --branch dev/v5-idea-0003-trial-001-dynamic-routing \
  --commit <pre_run_freeze_commit> \
  --git-remote /data/lby/projects/cv_project/_transfer/<bundle>.bundle \
  --server-repo /data/lby/projects/cv_project/GTPJ \
  --warehouse-root /data/lby/projects/cv_project/GTPJ_Warehouse \
  --conda-env direct \
  --python /data/lby/.conda/envs/dvsr_gpu/bin/python \
  --controller-python /usr/bin/python3

/usr/bin/python3 workflow/gtpj_workflow.py plan-dynamic-routing-batch \
  --trial-dir experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing \
  --run-id RUN-20260701-0008-dynroute-bs128-bold50-2gpu \
  --jobs 50 \
  --profile dynamic-bold-followup \
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

- Local validation must pass before freeze commit.
- Server GPU processes from the superseded bs=64 sequence must be stopped before starting bs=128.
- Server `audit-boundary` must pass before planning.
- Server `validate` may still fail on historical `.gtpj_runtime` references to old TUNE records;
  that is a known pre-existing runtime preflight exception and must not be counted as ATTEMPT-002 evidence.

## Post-Run Resolution

- `RUN-20260701-0007-dynroute-bs128-exploit50-2gpu`: 50 completed / 0 failed; best H=70.58.
- `RUN-20260701-0008-dynroute-bs128-bold50-2gpu`: 44 completed / 6 failed; best H=70.84.
- The bs=128 static v5 control reached only H=69.70, so bs=128 is rejected as a batch-size / schedule mismatch.
- Future dynamic routing batches are locked back to `batch_size=64` unless the owner explicitly reopens batch-size ablation.
- Future profile generation should avoid `dynamic_pse_mode=sample`; current PSE routing supports only `fixed` and `class`.
