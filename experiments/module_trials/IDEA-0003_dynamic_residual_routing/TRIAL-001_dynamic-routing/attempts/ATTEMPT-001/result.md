# ATTEMPT-001 Result

```text
run_id: RUN-20260630-0005-dynroute50-2gpu
status: completed
jobs: 50 completed / 0 failed
batch_profile: balanced-aggressive
trial_decision: revise
promotion_decision: rejected
```

## Baseline References

| Reference | H |
|---|---:|
| v3 CONFIRM-001 confirmed config | 74.47 |
| v5 repeat mean | 74.44 |

## Top Results

| Rank | Job | Group | Name | H | U | S | ZS | Best epoch |
|---:|---|---|---|---:|---:|---:|---:|---:|
| 1 | DR-001 | sanity_control | static_v5_control | 74.40 | 71.70 | 77.31 | 81.38 | 45 |
| 2 | DR-008 | local_gate | local_class_h24 | 74.39 | 67.94 | 82.20 | 81.27 | 26 |
| 3 | DR-023 | direction_gate | direction_sample_h48_a0.003 | 74.38 | 72.26 | 76.63 | 81.61 | 48 |
| 4 | DR-041 | top2_frozen_repeat | top1_repeat_1 | 74.37 | 71.76 | 77.17 | 81.62 | 34 |
| 5 | DR-042 | top2_frozen_repeat | top1_repeat_2 | 74.36 | 72.27 | 76.57 | 81.22 | 33 |

## Repeat Evidence

| Source | n | H mean | U mean | S mean |
|---|---:|---:|---:|---:|
| DR-001 static_v5_control | 5 | 74.34 | 71.83 | 77.02 |
| DR-008 local_class_h24 | 5 | 74.23 | 68.54 | 80.97 |

## Interpretation

The dynamic routing idea is not promoted from this attempt. The best dynamic single result was close to the static control, but it did not beat `v3/CONFIRM-001 local-v3-054` confirmed H=74.47 or v5 repeat mean H=74.44. The dynamic repeat mean weakened to H=74.23 and had low U.

Direction routing is the most promising follow-up because DR-023 reached H=74.38 with a better U/S balance than the local-gate winner. Local gates remain worth tuning, but the first repeat set suggests the class-local configuration is not stable enough. Dynamic ICSA should be treated cautiously because the ICSA group collapsed in this profile.

## Follow-Up

Use the `principled-followup` profile:

- keep ICSA fixed;
- separate direction/local/PSE rather than coupling all gates early;
- repeat top 3 instead of top 2;
- prioritize repeat mean over a single best H.
