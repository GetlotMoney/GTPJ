# ATTEMPT-004 Quality Check

```text
attempt_id: ATTEMPT-004
subject_id: ATTEMPT-004
quality_stage: post_run
quality_decision: warn_keep_needs_repeat
promotion_decision: blocked
evidence_level: valid_single_run
```

## Checks

- [x] ATTEMPT-003 root summary has been synchronized before planning ATTEMPT-004.
- [x] ATTEMPT-004 is trial-internal and does not create a new method version.
- [x] The planned profile uses only legal dynamic routing modes.
- [x] `dynamic_pse_mode=sample` is prohibited.
- [x] The minimal DR-018 direction ablation changes only `dynamic_direction_mode=sample -> fixed`.
- [x] `batch_size=64` is fixed.
- [x] Config epochs field and actual planned train epochs are both disclosed.
- [x] Planned train epochs are 50 because `lr_stages=20+20+10`.
- [x] GZSL split, label mapping, class order, logits shape, evaluator, and metric semantics are unchanged.
- [x] Raw logs and checkpoints will stay outside GitHub.
- [x] Top-3 checkpoint retention is required after completion.
- [x] `RESULT_INDEX` or campaign summaries, if created, are derived indexes only.
- [x] `RUN-20260702-0002-dr018-confirm-ablate50-2gpu` completed 50 / 50 jobs with 0 failures.
- [x] Best observed single is DR-035 H=75.02.
- [x] Related workflow-v2 campaign completed 10 / 10 jobs with 0 failures.
- [x] Artifact identities for summary/status/plan/events are recorded in the campaign final report.
- [ ] Min3 repeat for DR-035 is not complete.
- [ ] Full per-log traceback/missing-metric audit is not recorded yet.
- [ ] Top-3 checkpoint retention is not recorded yet.

## Role Checks

| Role | Lifecycle | Decision | Summary |
|---|---|---|---|
| Runner Monitor | workflow_scoped temporary_subagent | warn | Server is idle, but must be aligned to the pre-run freeze commit before launch. |
| Interface Checker | task_scoped temporary_subagent | allow | DR-018 fixed-direction ablation is legal; PSE sample mode remains forbidden. |
| Result Planner | workstream_scoped temporary_subagent | allow | 50-run plan should prioritize repeat, ablation, narrow tune, and limited probes. |
| Evidence Quality Checker | task_scoped temporary_subagent | warn | Formal run is blocked until clean freeze commit and ATTEMPT-004 pre-run files exist. |

## Blocking Issues

No summary-level hard blocker is visible. Confirmed result and promotion remain blocked.

## Non-Blocking Warnings

- ATTEMPT-003 H=74.86 is a best observed single, not `confirmed_H`.
- ATTEMPT-004 can only become promotion-facing if repeat and ablation gates pass.
- The current active v5 reference is owner-activated provisional; promotion comparisons must report both `best_observed_H` and `confirmed_H`.

## Not Checked Yet

- Min3 repeat stability for DR-035.
- Full log audit and Warehouse checkpoint retention.
- Post-run U/S stability.

## Post-Run Decision

`keep / tune_promising`.

DR-035 is the current best observed single for TRIAL-001, but it is not `confirmed_H`.
The next valid action is min3 repeat for DR-035 before any promotion or baseline claim.
