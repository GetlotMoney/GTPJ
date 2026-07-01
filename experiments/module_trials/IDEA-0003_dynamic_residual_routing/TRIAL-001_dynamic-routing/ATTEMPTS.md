# Attempts

| Attempt | Server run | Status | Best single | Best dynamic | Repeat evidence | Decision |
|---|---|---|---|---|---|---|
| `ATTEMPT-001` | `RUN-20260630-0005-dynroute50-2gpu` | 50 completed / 0 failed | DR-001 static control H=74.40 | DR-008 local_class_h24 H=74.39 | DR-008 repeat mean H=74.23 | revise, no promotion |
| `ATTEMPT-002` | `RUN-20260701-0007-dynroute-bs128-exploit50-2gpu` + `RUN-20260701-0008-dynroute-bs128-bold50-2gpu` | 94 completed / 6 failed, bs=128 | DR-014 H=70.84 | DR-014 direction_sample_h112_w0.5_a0.02 H=70.84 | no repeat; bs128 control H=69.70 | reject, restore bs=64 |
| `ATTEMPT-003` | `RUN-20260701-0009-dynroute-bs64-repro-tune50-2gpu` aborted pre-evidence; `RUN-20260701-0010-dynroute-bs64-repro-tune50-2gpu` planned | planned | pending | pending | static / DR-008 / DR-023 each x3 | run bs64 reproduce + tune |

## ATTEMPT-001 Notes

This attempt used the `balanced-aggressive` 50-job profile across two GPUs.

Main observations:

- Static v5 control remained the top single result at H=74.40.
- Best dynamic single was close but below references: DR-008 H=74.39.
- Best dynamic repeat mean was weaker: DR-008 repeat mean H=74.23.
- Direction gate had the most promising first-principles signal, especially DR-023 with H=74.38 and U=72.26.
- Dynamic ICSA and multi-gate combinations were unstable in this profile.
- Follow-up profile should freeze ICSA and explore direction/local/PSE gates with fewer coupled moving parts.

Attempt-local records:

- `attempts/ATTEMPT-001/config.yaml`
- `attempts/ATTEMPT-001/manifest.yaml`
- `attempts/ATTEMPT-001/result.yaml`
- `attempts/ATTEMPT-001/result.md`
- `attempts/ATTEMPT-001/quality_check.md`

## ATTEMPT-002 Pre-Run Notes

This attempt supersedes the early bs=64 follow-up sequence with a clean bs=128 workflow run.
It uses two 50-job workflow batches so the existing dynamic routing runner remains unchanged:

- `RUN-20260701-0007-dynroute-bs128-exploit50-2gpu`: direction/local/PSE exploit follow-up.
- `RUN-20260701-0008-dynroute-bs128-bold50-2gpu`: bolder direction/PSE/local/ICSA-safe/combination follow-up.

The stopped bs=64 `RUN-20260701-0005` / `RUN-20260701-0006` sequence is treated as superseded
runtime only and must not be used as valid evidence. ATTEMPT-002 becomes formal evidence only
after both bs=128 batches finish or fail under the workflow runner.

Attempt-local records:

- `attempts/ATTEMPT-002/config.yaml`
- `attempts/ATTEMPT-002/manifest.yaml`
- `attempts/ATTEMPT-002/pre_run_plan.md`
- `attempts/ATTEMPT-002/result.yaml`
- `attempts/ATTEMPT-002/result.md`
- `attempts/ATTEMPT-002/quality_check.md`
- `attempts/ATTEMPT-002/agent_summary.md`

## ATTEMPT-002 Post-Run Notes

ATTEMPT-002 completed as a batch-size intervention and is rejected for promotion.

Main observations:

- `RUN-20260701-0007-dynroute-bs128-exploit50-2gpu`: 50 completed / 0 failed; best was DR-029 direction_sample_h56_w0.52_a0.01 at H=70.58.
- `RUN-20260701-0008-dynroute-bs128-bold50-2gpu`: 44 completed / 6 failed; best was DR-014 direction_sample_h112_w0.5_a0.02 at H=70.84.
- The bs=128 static v5 control was only H=69.70, far below the bs=64 ATTEMPT-001 static control H=74.40.
- The six failed bold jobs used invalid `dynamic_pse_mode=sample`; PSE dynamic routing currently supports only `fixed` and `class`.
- The degradation is treated as a batch-size / schedule mismatch, not evidence against dynamic routing itself.

Workflow decision:

- Restore and keep `batch_size=64` for future dynamic routing trials unless the owner explicitly reopens batch-size ablation.
- Future profiles should avoid `dynamic_pse_mode=sample` until the model supports sample-conditioned PSE gates.

## ATTEMPT-003 Pre-Run Notes

This attempt returns to the validated bs=64 setting and uses the `best-repro-tune-followup`
workflow profile for one 50-job two-GPU batch.

The initial `RUN-20260701-0009-dynroute-bs64-repro-tune50-2gpu` launch was stopped before
completion evidence because one controller hit a concurrent `batch_status.json` read/write race.
The formal evidence run is `RUN-20260701-0010-dynroute-bs64-repro-tune50-2gpu` after the runner
status writer was changed to atomic replace plus short read retries.

Plan:

- Reproduce current leading evidence three times each: static v5 control, DR-008 local_class_h24,
  and DR-023 direction_sample_h48_a0.003.
- Tune direction routing around the DR-023 signal with small changes to gate hidden width,
  anchor strength, and `weight_s2v`.
- Tune local routing around the DR-008 signal with lower local residual weight to improve U/S balance.
- Tune legal PSE modes only (`fixed` and `class`); `sample` remains prohibited until model support exists.
- Keep dynamic ICSA frozen in this profile because ATTEMPT-001 and ATTEMPT-002 showed instability.

Promotion boundary:

- Do not promote from a single run. A dynamic route must beat the v4/v5 reference boundary
  around H=74.45 and hold up under its reproduce cluster before any v6 discussion.
