# ATTEMPT-003 Result

## Summary

ATTEMPT-003 returned to `batch_size=64` and completed
`RUN-20260701-0010-dynroute-bs64-repro-tune50-2gpu` with 50 completed jobs and
0 failed jobs.

Important epoch note:

```text
config_epochs_field: 30
planned_train_epochs: 50
epoch_schedule_source: lr_stages
lr_stages: 20 + 20 + 10
```

The best single result is `DR-018 direction_sample_h48_w0.5_a0.003` at H=74.86.
This is promising but not confirmed evidence.

## Top Results

| Rank | Job | Group | Name | U | S | H | ZS | Best epoch |
|---:|---|---|---|---:|---:|---:|---:|---:|
| 1 | DR-018 | direction_repro_tune | direction_sample_h48_w0.5_a0.003 | 73.10 | 76.71 | 74.86 | 81.84 | 37 |
| 2 | DR-019 | direction_repro_tune | direction_sample_h48_w0.5_a0.005 | 73.00 | 76.73 | 74.82 | 81.86 | 37 |
| 3 | DR-016 | direction_repro_tune | direction_sample_h48_w0.45_a0.003 | 72.96 | 76.51 | 74.69 | 81.71 | 37 |

## Reproduce Clusters

| Cluster | H values | Mean | Min | Max |
|---|---|---:|---:|---:|
| static_v5_control x3 | 74.49 / 74.35 / 74.62 | 74.49 | 74.35 | 74.62 |
| DR-008 local_class_h24_a0.001 x3 | 74.38 / 74.18 / 74.27 | 74.28 | 74.18 | 74.38 |
| DR-023 direction_sample_h48_a0.003 x3 | 74.58 / 74.61 / 74.61 | 74.60 | 74.58 | 74.61 |

## Decision

`ATTEMPT-003` is `tune_promising`.

It is not promoted because the new top config has not yet passed clean min3
confirmation and direction-gate ablation.

Next valid experiment:

```text
DR-018 direction_sample_h48_w0.5_a0.003 x3 confirmation
same config with dynamic_direction_mode=fixed x3 ablation
static_v5_control x3 sentinel if needed
```
