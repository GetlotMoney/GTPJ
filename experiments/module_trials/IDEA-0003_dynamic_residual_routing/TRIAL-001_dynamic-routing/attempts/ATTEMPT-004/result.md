# ATTEMPT-004 Result

```text
attempt_id: ATTEMPT-004
trial_id: TRIAL-001
run_id: RUN-20260702-0002-dr018-confirm-ablate50-2gpu
evidence_level: valid_single_run
confirmation_status: needs_confirmation
promotion_decision: blocked
```

## Top Results

| Rank | Job | Group | Name | U | S | H | ZS | Best epoch | Decision |
|---:|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | DR-035 | direction_narrow_tune | `direction_sample_h48_w0.525_a0.005` | 72.69 | 77.51 | 75.02 | 82.04 | 48 | repeat first |
| 2 | DR-009 | neighbor_repeat | `dr016_direction_sample_h48_w0.45_a0.003_r02` | 72.93 | 77.19 | 75.00 | 81.95 | 48 | supporting single |
| 3 | DR-011 | neighbor_repeat | `dr023_direction_sample_h48_a0.003_r02` | 73.00 | 76.90 | 74.90 | 81.72 | 37 | supporting single |
| 4 | DR-029 | direction_narrow_tune | `direction_sample_h48_w0.5_a0.001` | 73.06 | 76.84 | 74.90 | 81.89 | 48 | supporting single |

## Decision

`keep / tune_promising`.

DR-035 is the current best observed single for TRIAL-001. It is not a confirmed result.
The next valid action is min3 repeat for DR-035, with DR-004/DR-006 from the workflow-v2
campaign as neighbor stability checks if budget allows.
