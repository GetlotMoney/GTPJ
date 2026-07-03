# ATTEMPT-005 Result

```yaml
attempt_id: ATTEMPT-005
run_id: RUN-20260703-0001-dr035-min3-confirm-2gpu
result_type: seed_sweep
exact_repeat: false
confirmation_status: not_confirmed
promotion_decision: blocked
```

## Target

Source result:

```text
ATTEMPT-004 / RUN-20260702-0002 / DR-035
direction_sample_h48_w0.525_a0.005
seed=5
H=75.02, U=72.69, S=77.51, ZS=82.04, best_epoch=48
```

## Classification Correction

This run was planned with the historical profile name `dr035-min3-confirm`, but
the executed jobs used seeds 6, 7, and 8. Because seed is part of the experiment
configuration, this is not an exact repeat of DR-035. The correct classification
is:

```text
multi_seed_stability / seed_sweep
```

It can show seed sensitivity and score-search behavior, but it cannot by itself
confirm the original seed=5 result.

## Results

| Job | Seed | U | S | H | ZS | Best epoch |
|---|---:|---:|---:|---:|---:|---:|
| DR-001 | 6 | 70.99 | 77.09 | 73.91 | 81.01 | 43 |
| DR-002 | 7 | 71.49 | 77.54 | 74.39 | 81.55 | 41 |
| DR-003 | 8 | 70.92 | 77.70 | 74.15 | 81.62 | 40 |

Summary:

```text
H mean = 74.15
H min  = 73.91
H max  = 74.39
H range = 0.48
U mean = 71.13
S mean = 77.44
```

## Gate

| Criterion | Required | Observed | Pass |
|---|---:|---:|---|
| mean H | >= 74.60 | 74.15 | no |
| min H | >= 74.45 | 73.91 | no |
| range H | <= 0.50 | 0.48 | yes |

Decision:

```text
not_confirmed
stopped_repeat_unstable
promotion blocked
```

Next valid action is an exact-repeat run of the original DR-035 config with
seed=5. Multi-seed runs may be used for score search, but must not be described
as strict reproduction.

