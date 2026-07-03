# Attempts

| Attempt | Server run | Status | Best single | Best dynamic | Repeat evidence | Decision |
|---|---|---|---|---|---|---|
| `ATTEMPT-001` | `RUN-20260630-0005-dynroute50-2gpu` | 50 completed / 0 failed | DR-001 static control H=74.40 | DR-008 local_class_h24 H=74.39 | DR-008 repeat mean H=74.23 | revise, no promotion |
| `ATTEMPT-002` | `RUN-20260701-0007-dynroute-bs128-exploit50-2gpu` + `RUN-20260701-0008-dynroute-bs128-bold50-2gpu` | 94 completed / 6 failed, bs=128 | DR-014 H=70.84 | DR-014 direction_sample_h112_w0.5_a0.02 H=70.84 | no repeat; bs128 control H=69.70 | reject, restore bs=64 |
| `ATTEMPT-003` | `RUN-20260701-0009-dynroute-bs64-repro-tune50-2gpu` aborted pre-evidence; `RUN-20260701-0010-dynroute-bs64-repro-tune50-2gpu` | 50 completed / 0 failed | DR-018 direction_sample_h48_w0.5_a0.003 H=74.86 | DR-018 direction_sample_h48_w0.5_a0.003 H=74.86 | static mean H=74.49; DR-008 mean H=74.28; DR-023 mean H=74.60 | tune_promising; needs min3 confirmation + direction ablation |
| `ATTEMPT-004` | `RUN-20260702-0002-dr018-confirm-ablate50-2gpu` | 50 completed / 0 failed | DR-035 direction_sample_h48_w0.525_a0.005 H=75.02 | DR-035 direction_sample_h48_w0.525_a0.005 H=75.02 | DR-009 H=75.00 supporting single | tune_promising; repeat DR-035 first; promotion blocked |
| `ATTEMPT-005` | `RUN-20260703-0001-dr035-min3-confirm-2gpu` | 3 completed / 0 failed | DR-002 seed7 H=74.39 | DR-002 seed7 H=74.39 | seeds 6/7/8 H=73.91/74.39/74.15; mean H=74.15; exact_repeat not run | seed_sweep only; not_confirmed; promotion blocked |
| `ATTEMPT-006` | `RUN-20260702-0003-mixed2innov8tune-2gpu` | 10 completed / 0 failed | TUNE-002 / DR-004 direction_sample_h48_w0.525_a0.003 H=74.75 | TUNE-002 / DR-004 H=74.75 | no exact repeat; campaign is routing index only | tune_promising; formal ledger for workflow-v2 2-probe + 8-tune batch |
| `ATTEMPT-007` | `RUN-20260703-0002-dr035-exact-repeat-s5-min3-2gpu` | 3 completed / 0 failed | DR-002/DR-003 H=74.62 | DR-002/DR-003 H=74.62 | same-seed exact repeat seed 5 x3: 74.58/74.62/74.62; mean H=74.61; min H=74.58; range H=0.04 | confirmed_candidate; promotion blocked |

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
  around H=74.47 and hold up under its reproduce cluster before any v6 discussion.

## ATTEMPT-003 Post-Run Notes

`RUN-20260701-0010-dynroute-bs64-repro-tune50-2gpu` completed 50 / 50 jobs with 0 failures.

Epoch schedule clarification:

- `config_epochs_field=30`
- `planned_train_epochs=50`
- `epoch_schedule_source=lr_stages`
- `lr_stages=20 + 20 + 10`

Main observations:

- Best single: DR-018 `direction_sample_h48_w0.5_a0.003`, H=74.86, U=73.10, S=76.71.
- Static v5 control reproduced at mean H=74.49 over 3 runs.
- DR-008 local reproduced weaker at mean H=74.28 over 3 runs.
- DR-023 direction reproduced at mean H=74.60 over 3 runs.
- The evidence state is `tune_promising`, not `min3_confirmed`.
- Promotion remains blocked until DR-018 has clean min3 confirmation and direction-gate ablation.

Checkpoint retention:

- Current-run copied `best_model_*.pth` files seen: 49.
- Deleted non-Top-3 current-run model checkpoints: 46.
- Retained current-run Top-3 checkpoints: DR-018, DR-019, DR-016.

Attempt-local records:

- `attempts/ATTEMPT-003/config.yaml`
- `attempts/ATTEMPT-003/pre_run_plan.md`
- `attempts/ATTEMPT-003/manifest.yaml`
- `attempts/ATTEMPT-003/result.yaml`
- `attempts/ATTEMPT-003/result.md`
- `attempts/ATTEMPT-003/quality_check.md`
- `attempts/ATTEMPT-003/agent_summary.md`
- `attempts/ATTEMPT-003/TRANSITIONS.jsonl`
- `attempts/ATTEMPT-003/evidence_routing.yaml`

## ATTEMPT-004 Pre-Run Notes

ATTEMPT-004 is the workflow-v2 follow-up for ATTEMPT-003's best observed single:

- Target: DR-018 `direction_sample_h48_w0.5_a0.003`.
- Planned formal run: `RUN-20260702-0002-dr018-confirm-ablate50-2gpu`.
- Workflow profile: `dr018-confirm-ablate`.
- Batch size: 64.
- Config epochs field: 30.
- Planned train epochs: 50.
- Epoch schedule source: `lr_stages`.
- LR stages: 20 + 20 + 10.
- GPUs: 0,1.

Budget:

- 12 repeat / confirmation jobs.
- 10 ablation / control jobs.
- 22 narrow direction tune jobs.
- 6 trial-internal mechanism probes.

The profile is designed to answer two formal questions:

- Does DR-018 hold up under clean repeat?
- Does the dynamic direction gate beat a one-factor fixed-direction ablation?

The tune and probe jobs may create `valid_single_run` or `tune_promising` evidence, but they
cannot produce confirmed or promotion-grade evidence without later repeat and quality checks.

Launch note:

- `RUN-20260702-0001-dr018-confirm-ablate50-2gpu` failed before training because the runner
  tried to call `conda` in the non-interactive server environment.
- This is classified as `runner_environment`, not method evidence.
- The runner was fixed to use an absolute Python path directly; the formal rerun id is
  `RUN-20260702-0002-dr018-confirm-ablate50-2gpu`.

Pre-run records:

- `attempts/ATTEMPT-004/config.yaml`
- `attempts/ATTEMPT-004/pre_run_plan.md`
- `attempts/ATTEMPT-004/manifest.yaml`
- `attempts/ATTEMPT-004/quality_check.md`
- `attempts/ATTEMPT-004/agent_summary.md`
- `attempts/ATTEMPT-004/TRANSITIONS.jsonl`
- `attempts/ATTEMPT-004/evidence_routing.yaml`

## ATTEMPT-004 Post-Run Notes

`RUN-20260702-0002-dr018-confirm-ablate50-2gpu` completed 50 / 50 jobs with 0 failures.

Main observations:

- Best observed single so far: DR-035 `direction_sample_h48_w0.525_a0.005`, H=75.02, U=72.69, S=77.51, ZS=82.04.
- Closest supporting prior run: DR-009 `dr016_direction_sample_h48_w0.45_a0.003_r02`, H=75.00, U=72.93, S=77.19.
- Direction sample with hidden 48 and anchor lambda around 0.003-0.005 is the strongest current family.

Evidence boundary:

- These are single-run / supporting-single results, not `confirmed_H`.
- Promotion is blocked until min3 repeat, log audit, artifact identity, GZSL rule checks, and checkpoint retention are complete.
- Overall next repeat priority is DR-035.

## ATTEMPT-006 Post-Run Notes

`RUN-20260702-0003-mixed2innov8tune-2gpu` completed 10 / 10 jobs with 0 failures.
It is recorded as ATTEMPT-006 because mixed campaigns must not become a separate
formal result branch. The campaign directory is only a routing index.

Main observations:

- Best workflow-v2 campaign result: TUNE-002 / DR-004 `tune_direction_h48_w0.525_a0.003`,
  H=74.75, U=72.90, S=76.69.
- TUNE-004 / DR-006 scored H=74.67 and TUNE-008 / DR-010 scored H=74.64.
- The two workflow-v2 innovation probes INNOV-001/INNOV-002 scored H=73.62/73.63 and
  are stopped for this campaign.
- These were existing-switch probes, not paper-derived full innovations and not new Trials.

Evidence boundary:

- These are single-run / tune-promising results, not `confirmed_H`.
- Promotion is blocked until repeat/stability, log audit, artifact identity, GZSL rule checks,
  checkpoint retention, and necessary ablation evidence are complete.

Attempt-local records:

- `attempts/ATTEMPT-006/manifest.yaml`
- `attempts/ATTEMPT-006/result.yaml`
- `attempts/ATTEMPT-006/result.md`
- `attempts/ATTEMPT-006/WORK_ITEMS.md`
- `attempts/ATTEMPT-006/quality_check.md`
- `attempts/ATTEMPT-006/agent_summary.md`
- `attempts/ATTEMPT-006/TRANSITIONS.jsonl`
- `attempts/ATTEMPT-006/evidence_routing.yaml`

Campaign routing-index records:

- `experiments/campaigns/CAMP-20260702-workflow-v2-2innov8tune/FINAL_REPORT.md`
- `experiments/campaigns/CAMP-20260702-workflow-v2-2innov8tune/RESULT_INDEX.md`
- `experiments/campaigns/CAMP-20260702-workflow-v2-2innov8tune/quality_check.md`
- `experiments/campaigns/CAMP-20260702-workflow-v2-2innov8tune/agent_summary.md`

## ATTEMPT-007 Post-Run Notes

`RUN-20260703-0002-dr035-exact-repeat-s5-min3-2gpu` completed 3 / 3 jobs with 0 failures.

Main observations:

- Exact-repeat scope is correct: all three jobs used source seed 5, not seeds 6/7/8.
- Results were H=74.58 / 74.62 / 74.62; mean H=74.61, min H=74.58, max H=74.62, range H=0.04.
- The configured confirmation gate passed: mean H >= 74.60, min H >= 74.45, range H <= 0.50.
- Evidence state is `min3_confirmed` and result state is `confirmed_candidate`.
- Promotion remains blocked; this repeat does not create a new `vX` and does not replace the need for separate promotion evidence.

Evidence boundary:

- Runtime batch evidence remains on lab4090 under `.gtpj_runtime/batches/RUN-20260703-0002-dr035-exact-repeat-s5-min3-2gpu`.
- Current logs/configs/checkpoints were copied to a dedicated ATTEMPT-007 warehouse directory because the runner's default `attempt-001/002/003` warehouse paths are shared with historical runs.
- The generated runner top-level `batch_status.status` remains `planned`; job-level statuses, `summary.csv/jsonl`, and `events.jsonl` are authoritative and show 3/3 completed.

Attempt-local records:

- `attempts/ATTEMPT-007/config.yaml`
- `attempts/ATTEMPT-007/pre_run_plan.md`
- `attempts/ATTEMPT-007/manifest.yaml`
- `attempts/ATTEMPT-007/result.yaml`
- `attempts/ATTEMPT-007/result.md`
- `attempts/ATTEMPT-007/quality_check.md`
- `attempts/ATTEMPT-007/agent_summary.md`
- `attempts/ATTEMPT-007/AGENT_ACTIVITY.md`
- `attempts/ATTEMPT-007/TRANSITIONS.jsonl`
- `attempts/ATTEMPT-007/evidence_routing.yaml`
