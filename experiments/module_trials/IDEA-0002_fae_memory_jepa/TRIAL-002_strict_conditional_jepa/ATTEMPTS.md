# TRIAL-002 Attempts

## Attempts

| Attempt ID | Type | Parameter / Change | Old | New | Seed | U | S | H | ZS | Best epoch | Log artifact | Decision | Directory |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| ATTEMPT-001 | valid_single_run | strict main-path FAE memory + conditional AG-JEPA text | TRIAL-001 keep-only | fae_main_memory + conditional | 5 | 71.15 | 77.11 | 74.01 | 81.31 | 33 | `log:v2:module_trial:TRIAL-002:attempt-001` | keep | `attempts/ATTEMPT-001/` |
| ATTEMPT-002 | confirmation | clean rerun of ATTEMPT-001 frozen config | ATTEMPT-001 valid_single_run H=74.01 | same config and seed | 5 | 71.32 | 77.40 | 74.24 | 81.62 | 33 | `log:v2:module_trial:TRIAL-002:attempt-002` | keep | `attempts/ATTEMPT-002/` |
| ATTEMPT-003 | confirmation | second clean rerun of ATTEMPT-002 confirmed config | ATTEMPT-002 confirmed_H=74.24 | same config and seed | 5 | 71.19 | 76.62 | 73.81 | 81.08 | 42 | `log:v2:module_trial:TRIAL-002:attempt-003` | not_confirmed | `attempts/ATTEMPT-003/` |
| ATTEMPT-004 | confirmation | third clean rerun of ATTEMPT-002 confirmed config | ATTEMPT-002 confirmed_H=74.24; ATTEMPT-003 H=73.81 not_confirmed | same config and seed | 5 | 71.22 | 77.60 | 74.27 | 81.38 | 33 | `log:v2:module_trial:TRIAL-002:attempt-004` | keep | `attempts/ATTEMPT-004/` |
| ATTEMPT-005 | reproducibility_diagnosis | deterministic confirmation of mixed same-seed result | ATTEMPT-004 config | same model config + strict_determinism + use_dedicated_batch_rng | 5 | 71.69 | 76.01 | 73.79 | 81.32 | 43 | `log:v2:module_trial:TRIAL-002:attempt-005` | not_confirmed | `attempts/ATTEMPT-005/` |
| ATTEMPT-006 | reproducibility_diagnosis | exact deterministic rerun of ATTEMPT-005 | ATTEMPT-005 H=73.79 | same config and seed | 5 | 71.29 | 76.73 | 73.91 | 81.52 | 42 | `log:v2:module_trial:TRIAL-002:attempt-006` | not_confirmed | `attempts/ATTEMPT-006/` |
| ATTEMPT-007 | reproducibility_diagnosis | seed sensitivity rerun with deterministic controls | ATTEMPT-006 config seed=5 | same model/training config with seed=42 | 42 | - | - | - | - | - | pending | planned | `attempts/ATTEMPT-007/` |
| ATTEMPT-008 | reproducibility_diagnosis | exact seed=42 deterministic rerun of ATTEMPT-007 | ATTEMPT-007 planned | same config and seed | 42 | - | - | - | - | - | pending | planned | `attempts/ATTEMPT-008/` |

## Notes

- TRIAL-002 exists because the strict path changes the implementation hypothesis relative to TRIAL-001.
- ATTEMPT-001 and ATTEMPT-002 were originally misfiled under TRIAL-001 as ATTEMPT-002 and ATTEMPT-003. They are re-registered here with corrected trial identity and Warehouse artifact ids.
- ATTEMPT-003 and ATTEMPT-004 are exact same-config confirmation reruns of the strict path. ATTEMPT-003 did not confirm the 74-level result, while ATTEMPT-004 reached H=74.27.
- Confirmation gate is mixed, not stable. Do not start the planned 10-run tuning sweep, promotion, or tag until the owner explicitly accepts this variance or requests a new confirmation strategy.
- ATTEMPT-005 is the first reproducibility diagnosis run for `mixed_confirmation`. It keeps the strict main-path FAE-memory + conditional AG-JEPA semantics unchanged and only enables deterministic runtime logging plus dedicated batch sampling RNG.
- ATTEMPT-006 repeats ATTEMPT-005 exactly to check whether the deterministic diagnosis path itself is reproducible.
- ATTEMPT-007 and ATTEMPT-008 repeat the deterministic diagnosis path with `random_seed=42` and `batch_sampling_seed=42` to test whether the seed-5 behavior is seed-sensitive.
