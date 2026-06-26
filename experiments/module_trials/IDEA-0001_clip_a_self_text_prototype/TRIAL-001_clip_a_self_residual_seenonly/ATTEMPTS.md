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

## Notes

- All five new attempts changed only trial-local parameters; the TRIAL-001 code path itself did not change.
- ATTEMPT-003 is the current best setting and is the only attempt above both the authoritative v1 baseline and the same-day confirmation run by a meaningful margin.
