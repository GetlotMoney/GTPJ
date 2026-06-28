# TRIAL-002 Attempts

## Attempts

| Attempt ID | Type | Parameter / Change | Old | New | Seed | U | S | H | ZS | Best epoch | Log artifact | Decision | Directory |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| ATTEMPT-001 | valid_single_run | strict main-path FAE memory + conditional AG-JEPA text | TRIAL-001 keep-only | fae_main_memory + conditional | 5 | 71.15 | 77.11 | 74.01 | 81.31 | 33 | `log:v2:module_trial:TRIAL-002:attempt-001` | keep | `attempts/ATTEMPT-001/` |
| ATTEMPT-002 | confirmation | clean rerun of ATTEMPT-001 frozen config | ATTEMPT-001 valid_single_run H=74.01 | same config and seed | 5 | 71.32 | 77.40 | 74.24 | 81.62 | 33 | `log:v2:module_trial:TRIAL-002:attempt-002` | keep | `attempts/ATTEMPT-002/` |
| ATTEMPT-003 | confirmation | second clean rerun of ATTEMPT-002 confirmed config | ATTEMPT-002 confirmed_H=74.24 | same config and seed | 5 | 71.19 | 76.62 | 73.81 | 81.08 | 42 | `log:v2:module_trial:TRIAL-002:attempt-003` | not_confirmed | `attempts/ATTEMPT-003/` |
| ATTEMPT-004 | confirmation | third clean rerun of ATTEMPT-002 confirmed config | ATTEMPT-002 confirmed_H=74.24 | same config and seed | 5 | - | - | - | - | - | pending | pending | `attempts/ATTEMPT-004/` |

## Notes

- TRIAL-002 exists because the strict path changes the implementation hypothesis relative to TRIAL-001.
- ATTEMPT-001 and ATTEMPT-002 were originally misfiled under TRIAL-001 as ATTEMPT-002 and ATTEMPT-003. They are re-registered here with corrected trial identity and Warehouse artifact ids.
- ATTEMPT-003 and ATTEMPT-004 are exact same-config confirmation reruns of the confirmed strict path. They must pass before any 10-run tuning sweep starts.
