# TRIAL-001_dynamic-routing Result

## Summary

```text
kind: module-trial
run_id: RUN-20260630-0005-dynroute50-2gpu
batch_profile: balanced-aggressive
jobs: 50 completed / 0 failed
trial_decision: revise
promotion_decision: rejected
```

## Metrics

| Result | Job | Group | U | S | H | ZS | Best epoch |
|---|---|---|---:|---:|---:|---:|---:|
| Best single | DR-001 static_v5_control | sanity_control | 71.70 | 77.31 | 74.40 | 81.38 | 45 |
| Best dynamic single | DR-008 local_class_h24 | local_gate | 67.94 | 82.20 | 74.39 | 81.27 | 26 |
| Best direction single | DR-023 direction_sample_h48_a0.003 | direction_gate | 72.26 | 76.63 | 74.38 | 81.61 | 48 |

Repeat means:

| Source | n | U mean | S mean | H mean |
|---|---:|---:|---:|---:|
| DR-001 static_v5_control | 5 | 71.83 | 77.02 | 74.34 |
| DR-008 local_class_h24 | 5 | 68.54 | 80.97 | 74.23 |

References:

| Reference | H |
|---|---:|
| v3 CONFIRM-001 confirmed config | 74.47 |
| v5 repeat mean | 74.44 |

## Evidence

```text
runtime_path: /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260630-0005-dynroute50-2gpu
warehouse_summary_path: /data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/module_trial/TRIAL-001/batch-RUN-20260630-0005-dynroute50-2gpu
summary_csv_sha256: a32a748e55f810b9d1a6fa7d9f0d2cd0c7d2ab85adc41241266a6dcd4049cf20
summary_jsonl_sha256: 05f4e8804c9d60917acd6d20ac475b19218c2fc2974f08541beeb2c18c078905
batch_status_json_sha256: 5f32239fd3c94cade94b84a934b2f825f49261ee0a35bf089fbef113a5e02b44
```

## Decision

No promotion.

The best dynamic single H=74.39 and best dynamic repeat mean H=74.23 do not beat `v3/CONFIRM-001 local-v3-054` confirmed H=74.47 or v5 repeat mean H=74.44. Direction routing is the best follow-up signal; dynamic ICSA and coupled combinations should be treated as unstable in this profile.
