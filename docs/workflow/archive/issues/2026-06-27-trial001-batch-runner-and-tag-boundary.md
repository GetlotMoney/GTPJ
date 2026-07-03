# 2026-06-27 TRIAL-001 Batch Runner And Tag Boundary Issues

## Scope

- Trial: `TRIAL-001_clip_a_self_residual_seenonly`
- Completed result set: `ATTEMPT-009` through `ATTEMPT-020`
- Current best: `ATTEMPT-019`, `H=74.29`
- Incomplete range: `ATTEMPT-021` through `ATTEMPT-028`
- Tag policy clarified: trial-level tags are allowed; attempt-level tags are not used.

## ISSUE-20260627-007: Long batch stopped at ATTEMPT-021 with truncated conda traceback

Status: retry-needed

Symptom:

- Batch `RUN-20260626-235934-trial001-009-028` completed `ATTEMPT-009` through `ATTEMPT-020`.
- `ATTEMPT-021` failed before training epochs began.
- Runtime status recorded only:

```text
Traceback (most recent call last):
```

- Available partial evidence:

```text
.gtpj_runtime/runs/RUN-20260626-235934-trial001-009-028/stdout_ATTEMPT-021.log
train_log/CUB/training_log_CUB_2026-06-27_01-43-16.txt
```

Impact:

- `ATTEMPT-021` is not valid experiment evidence.
- `ATTEMPT-009..020` remain valid because each completed attempt has full log/checkpoint evidence.
- `ATTEMPT-021..028` still need a resume batch.

Root Cause:

- Not fully determined from the truncated traceback.
- The visible CUDA `pin_memory failed ... fallback to plain CPU tensor` warning also appeared in successful attempts, so it is not enough to identify the root cause.

Resolution:

- Do not register the partial `ATTEMPT-021` log as a result.
- Resume from `ATTEMPT-021` using the already frozen configs.
- Keep both runtime run ids so later artifact registration maps logs to the correct execution.

Prevention:

- Long batch runner should support explicit resume ranges.
- If `conda run` exits before epochs start, retry the same frozen config once before blaming the config.
- Capture full stderr for each attempt, not only the runner-level summary.

Helper Candidate:

- Add a `run-attempt-range --start ATTEMPT-021 --end ATTEMPT-028` wrapper.
- Add a failure classifier: before-first-epoch failures are `runner/environment`, not `result`.

## ISSUE-20260627-008: Trial tag and attempt tag boundary confusion

Status: fixed

Symptom:

- An attempt-level tag was created and pushed:

```text
trial/v1/idea-0001/trial-001-attempt-019-best-h7429
```

- This conflicted conceptually with the existing trial-level tag:

```text
trial/v1/idea-0001/trial-001
```

Impact:

- The attempt tag could be misread as a formal result or a promoted baseline.
- It also blurred three separate concepts:
  - trial code snapshot,
  - best attempt evidence,
  - formal version tag.

Root Cause:

- The workflow had a `trial/...` tag policy, but the boundary between trial-level tag and attempt-level evidence was not explicit enough.
- The best attempt result was incorrectly treated as something that needed a git tag.

Resolution:

- Delete the remote and local attempt-level tag:

```text
trial/v1/idea-0001/trial-001-attempt-019-best-h7429
```

- Keep and push only the trial-level tag:

```text
trial/v1/idea-0001/trial-001
```

- Replace `best_attempt_tag` fields with:

```text
best_attempt_record_commit: 3a7945a
attempt_git_tag_policy: not_used_for_trial_internal_attempts
```

Prevention:

- Trial-level tags are allowed:

```text
trial/<base-version>/idea-xxxx/trial-xxx
```

- Attempt-level tags are not used.
- Best attempts are recorded with `best_attempt_id`, `attempts/ATTEMPT-xxx/`, `run_commit`, `record_commit`, and Warehouse artifact ids.
- Only promoted baselines get `vX` tags.

Helper Candidate:

- Add `validate-tags` to reject tags matching attempt/best metric patterns.

## ISSUE-20260627-009: Trial/root indexes drift from current best attempt

Status: fixed

Symptom:

- Trial-local records correctly identified `ATTEMPT-019` as current best.
- Higher-level indexes still described the old `ATTEMPT-003` state.

Affected files:

```text
experiments/EXPERIMENT_REGISTRY.md
experiments/module_trials/INDEX.md
```

Impact:

- A reader who only checks the global registry could believe the current best is still `ATTEMPT-003 H=74.27`.
- This weakens the value of the repo as a lightweight result index.

Root Cause:

- Attempt-level result registration updated local evidence, but not all higher-level human indexes were refreshed.

Resolution:

- Update the global registry and module-trial index to say:

```text
Current best is ATTEMPT-019 with H=74.29; promotion remains blocked pending clean confirmation and U/S gap review.
```

Prevention:

- Whenever the trial root `best_attempt_id` changes, update:
  - trial `README.md`,
  - trial `result.yaml`,
  - trial `result.md`,
  - trial `quality_check.md`,
  - `experiments/module_trials/INDEX.md`,
  - `experiments/EXPERIMENT_REGISTRY.md`.

Helper Candidate:

- Add a `sync-trial-summary --best-attempt ATTEMPT-xxx` helper.
