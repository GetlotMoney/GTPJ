# ATTEMPT-002 Result

```text
attempt_id: ATTEMPT-002
trial_id: TRIAL-001
base_version: v5
attempt_type: batch_size_ablation_followup
batch_size: 128
status: completed_with_failures
jobs: 94 completed / 6 failed
trial_decision: revise
promotion_decision: rejected
```

ATTEMPT-002 tested whether using the available RTX 4090 memory with `batch_size=128`
could improve the next dynamic routing search. It did not.

## Runs

| Run | Profile | Completed | Failed | Best H | Best job |
|---|---|---:|---:|---:|---|
| `RUN-20260701-0007-dynroute-bs128-exploit50-2gpu` | `direction-exploit-followup` | 50 | 0 | 70.58 | DR-029 `direction_sample_h56_w0.52_a0.01` |
| `RUN-20260701-0008-dynroute-bs128-bold50-2gpu` | `dynamic-bold-followup` | 44 | 6 | 70.84 | DR-014 `direction_sample_h112_w0.5_a0.02` |

The bs=128 static v5 control in the bold batch reached only H=69.70. This is far
below the bs=64 ATTEMPT-001 static control H=74.40, so the degradation is treated
as a batch-size / schedule mismatch rather than as direct evidence against the
dynamic routing mechanism.

## Failure Cause

The six failed bold jobs used unsupported `dynamic_pse_mode=sample`:

```text
DR-017, DR-018, DR-019, DR-020, DR-041, DR-045
```

PSE gates are built before sample-conditioned text exists, so PSE dynamic routing
currently supports only `fixed` and `class`. The workflow planner has been updated
to prevent future profiles from emitting `dynamic_pse_mode=sample`.

## Decision

`promotion_decision: rejected`.

ATTEMPT-002 does not approach v4 confirmed H=74.47, v5 repeat mean H=74.44, or
the ATTEMPT-001 bs=64 control region. It is not a promotion candidate and does
not change the current best evidence from ATTEMPT-001.

`trial_decision: revise`.

Future dynamic routing work is locked back to `batch_size=64` unless the owner
explicitly reopens batch-size ablation. Continue from the bs64 direction/local
and legal PSE signals; treat dynamic ICSA and coupled multi-gate profiles cautiously.
