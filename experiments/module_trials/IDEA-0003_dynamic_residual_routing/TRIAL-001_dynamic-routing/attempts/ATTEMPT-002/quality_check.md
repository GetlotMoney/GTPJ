# ATTEMPT-002 Quality Check

```text
attempt_id: ATTEMPT-002
trial_id: TRIAL-001
quality_decision: reject
promotion_decision: rejected
checked_scope: batch status, summaries, failure cause, artifact boundary, batch-size comparison
```

## Evidence Boundary

- Runtime evidence stays on `lab4090` under `.gtpj_runtime/batches/`.
- GitHub records only summary metrics, hashes, sizes, decisions, and artifact URIs.
- No raw logs, checkpoints, or generated figures were added to GitHub.

## Checks

- Both bs=128 workflow batches finished under the runner: one clean batch and one batch with isolated failures.
- `RUN-20260701-0007-dynroute-bs128-exploit50-2gpu`: 50 completed / 0 failed.
- `RUN-20260701-0008-dynroute-bs128-bold50-2gpu`: 44 completed / 6 failed.
- The best completed bs=128 job reached only H=70.84.
- The bs=128 static control reached only H=69.70.
- The six failed jobs are explained by an unsupported profile value, not by silent metric corruption.

## Blocking / Non-Promotion Issues

- ATTEMPT-002 is a batch-size intervention and must not be mixed with ATTEMPT-001 bs=64 evidence as if it were the same training schedule.
- The performance collapse appears at the static control too, so the run does not isolate dynamic routing quality.
- No repeat evidence exists for a bs=128 candidate.
- `dynamic_pse_mode=sample` was invalid for six jobs and is now blocked in future workflow plan generation.

## Decision

This attempt is valid as negative batch-size evidence and invalid as promotion evidence.
Keep the trial decision at `revise`, keep promotion rejected, and restore future
dynamic routing batches to `batch_size=64`.
