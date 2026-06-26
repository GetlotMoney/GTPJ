# TRIAL-001 Attempts

ATTEMPT-001 was originally recorded at the trial root. A compatibility copy now lives in `attempts/ATTEMPT-001/`, while the root trial files summarize the current best attempt.

## Attempts

| Attempt ID | Type | Parameter / Change | Old | New | Seed | U | S | H | ZS | Best epoch | Log artifact | Decision | Directory |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| ATTEMPT-001 | param_tune | `clip_a_self_residual_seenonly` baseline trial run | - | - | 5 | 72.32 | 75.19 | 73.72 | 81.13 | 30 | `log:v1:module_trial:TRIAL-001:attempt-001` | revise | `attempts/ATTEMPT-001/` |
| ATTEMPT-002 | param_tune | `clip_a_self_heads` | 1 | 2 | 5 | 71.22 | 76.98 | 73.99 | 81.25 | 33 | `log:v1:module_trial:TRIAL-001:attempt-002` | keep | `attempts/ATTEMPT-002/` |
| ATTEMPT-003 | param_tune | `clip_a_self_heads` | 1 | 4 | 5 | 71.76 | 76.97 | 74.27 | 81.72 | 33 | `log:v1:module_trial:TRIAL-001:attempt-003` | best | `attempts/ATTEMPT-003/` |
| ATTEMPT-004 | param_tune | `clip_a_self_heads` | 1 | 8 | 5 | 72.70 | 74.48 | 73.58 | 80.98 | 44 | `log:v1:module_trial:TRIAL-001:attempt-004` | reject | `attempts/ATTEMPT-004/` |
| ATTEMPT-005 | param_tune | `clip_a_self_heads` + `clip_a_self_dropout` | `1 / 0.5` | `4 / 0.1` | 5 | 74.62 | 70.85 | 72.69 | 81.18 | 49 | `log:v1:module_trial:TRIAL-001:attempt-005` | reject | `attempts/ATTEMPT-005/` |
| ATTEMPT-006 | param_tune | `clip_a_self_heads` + `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` | `1 / 0.2 / 0.5` | `4 / 0.1 / 0.25` | 5 | 70.85 | 77.36 | 73.96 | 81.46 | 33 | `log:v1:module_trial:TRIAL-001:attempt-006` | keep | `attempts/ATTEMPT-006/` |
| ATTEMPT-007 | confirmation | clean confirmation of `ATTEMPT-003` config | `ATTEMPT-003` | same config | 5 | 70.82 | 76.80 | 73.69 | 80.91 | 33 | `log:v1:module_trial:TRIAL-001:attempt-007` | not_confirmed | `attempts/ATTEMPT-007/` |
| ATTEMPT-008 | confirmation | repeat clean confirmation of `ATTEMPT-003` config with pre-run diagnostics | `ATTEMPT-003/007` | same config | 5 | 71.36 | 76.58 | 73.88 | 81.22 | 33 | `log:v1:module_trial:TRIAL-001:attempt-008` | not_confirmed | `attempts/ATTEMPT-008/` |

## Notes

- ATTEMPT-002 through ATTEMPT-006 changed only trial-local parameters; the TRIAL-001 code path itself did not change.
- ATTEMPT-007 is a clean confirmation of the ATTEMPT-003 config from pre-run freeze commit `2820b17`.
- ATTEMPT-008 is a second clean confirmation of the same config from pre-run freeze commit `8b6acac`.
- ATTEMPT-003 remains the highest observed setting, but ATTEMPT-007 and ATTEMPT-008 did not confirm it; promotion remains blocked.
