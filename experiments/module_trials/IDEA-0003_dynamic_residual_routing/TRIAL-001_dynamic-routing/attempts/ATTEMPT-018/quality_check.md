# ATTEMPT-018 Quality Check

status: completed_not_restored

## Required Before Runner

- [x] Named left-sidebar Codex threads created with exact titles.
- [x] Reviewer checks helper profile and tests.
- [x] Runner Monitor allows resource and launch plan.
- [x] Interface Checker allows exact-repeat interface.
- [x] Evidence Quality Checker allows evidence chain.
- [x] Log Analyst has post-run parsing criteria ready.
- [x] Result Analyst has restore/near-miss/stability criteria ready.
- [x] `agent_runtime.yaml` passes `validate-agent-runtime`.
- [x] `multi-agent-preflight` passes.
- [x] `validate`, `validate-workflow-consistency`, `audit-boundary`, `validate-evidence-routing`, and `git diff --check` pass.

## Launch Snapshot

- server_batch_dir: `/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260709-0002-a017dr095-restore5-live-multiagent-2gpu`
- launch_method: `direct_nohup_controllers_after_screen_wrapper_exit`
- controller_pids: gpu0=`421592`, gpu1=`422312`
- initial_status: running=2, pending=3, completed=0, failed=0, skipped=0
- running_jobs: `DR-001` on GPU0, `DR-002` on GPU1
- owner monitor: `monitor-workflow --report-new-completions`

## Post-Run

- [x] Server `batch_status.status=completed`.
- [x] 5/5 completed, 0 failed, 0 skipped.
- [x] GPU0/GPU1 idle after completion.
- [x] Local runtime has `batch_status.json`, `summary.csv`, `summary.jsonl`, `events.jsonl`.
- [x] Best repeat is `DR-001`, H=74.71, U=72.19, S=77.40, ZS=81.95, best_epoch=48.
- [x] No repeat reached `restore_target_H=75.11`.
- [x] Best repeat is below near-miss threshold 74.91, so do not mark `near_miss_not_restored`.

## Result Boundary

ATTEMPT-018 is a completed max-5 exact-repeat non-restore observation for DR-095. It does not produce confirmation evidence, restored evidence, or promotion evidence.

Because this run was planned before the later source-control helper hardening, do not use it as a post-fix source-control confirmation. A future restored claim must be generated under the fixed strict gate and clean server worktree.

## Decision

- evidence_state: `stopped_repeat_unstable`
- confirmation_decision: `not_restored`
- promotion_decision: `blocked`
- next_action: post-fix strict-gate rerun or a new 4-candidate x 5 exact-repeat plan, but only after real strict-3 review passes.
