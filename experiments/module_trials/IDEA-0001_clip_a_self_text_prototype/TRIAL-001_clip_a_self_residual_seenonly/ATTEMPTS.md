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

| ATTEMPT-009 | confirmation | `ATTEMPT-006` clean confirmation | `ATTEMPT-006` | same config | 5 | 70.83 | 77.03 | 73.80 | 81.22 | 42 | `log:v1:module_trial:TRIAL-001:attempt-009` | not_confirmed | `attempts/ATTEMPT-009/` |
| ATTEMPT-010 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (outer ratio local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.125 / 0.25 / 0.5` | 5 | 70.76 | 77.49 | 73.97 | 81.22 | 42 | `log:v1:module_trial:TRIAL-001:attempt-010` | keep | `attempts/ATTEMPT-010/` |
| ATTEMPT-011 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (outer ratio local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.15 / 0.25 / 0.5` | 5 | 70.76 | 77.54 | 74.00 | 81.19 | 42 | `log:v1:module_trial:TRIAL-001:attempt-011` | keep | `attempts/ATTEMPT-011/` |
| ATTEMPT-012 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (outer ratio local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.175 / 0.25 / 0.5` | 5 | 71.19 | 77.08 | 74.02 | 81.22 | 27 | `log:v1:module_trial:TRIAL-001:attempt-012` | keep | `attempts/ATTEMPT-012/` |
| ATTEMPT-013 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (inner ratio local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.1 / 0.3 / 0.5` | 5 | 71.19 | 76.52 | 73.76 | 80.91 | 33 | `log:v1:module_trial:TRIAL-001:attempt-013` | reject | `attempts/ATTEMPT-013/` |
| ATTEMPT-014 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (inner/outer local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.125 / 0.3 / 0.5` | 5 | 71.35 | 76.99 | 74.07 | 81.28 | 33 | `log:v1:module_trial:TRIAL-001:attempt-014` | keep | `attempts/ATTEMPT-014/` |
| ATTEMPT-015 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (inner/outer local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.15 / 0.3 / 0.5` | 5 | 70.99 | 77.88 | 74.27 | 81.45 | 33 | `log:v1:module_trial:TRIAL-001:attempt-015` | keep | `attempts/ATTEMPT-015/` |
| ATTEMPT-016 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (inner/outer local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.175 / 0.3 / 0.5` | 5 | 70.85 | 77.12 | 73.85 | 81.05 | 33 | `log:v1:module_trial:TRIAL-001:attempt-016` | reject | `attempts/ATTEMPT-016/` |
| ATTEMPT-017 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (inner ratio local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.1 / 0.35 / 0.5` | 5 | 71.59 | 76.32 | 73.88 | 81.21 | 33 | `log:v1:module_trial:TRIAL-001:attempt-017` | reject | `attempts/ATTEMPT-017/` |
| ATTEMPT-018 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (inner/outer local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.125 / 0.35 / 0.5` | 5 | 71.08 | 77.42 | 74.12 | 81.51 | 33 | `log:v1:module_trial:TRIAL-001:attempt-018` | keep | `attempts/ATTEMPT-018/` |
| ATTEMPT-019 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (inner/outer local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.15 / 0.35 / 0.5` | 5 | 71.32 | 77.52 | 74.29 | 81.59 | 33 | `log:v1:module_trial:TRIAL-001:attempt-019` | best | `attempts/ATTEMPT-019/` |
| ATTEMPT-020 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (inner/outer local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.175 / 0.35 / 0.5` | 5 | 71.13 | 77.63 | 74.24 | 81.42 | 48 | `log:v1:module_trial:TRIAL-001:attempt-020` | keep | `attempts/ATTEMPT-020/` |
| ATTEMPT-021 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (inner ratio local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.1 / 0.4 / 0.5` | 5 | - | - | - | - | - | - | pending | `attempts/ATTEMPT-021/` |
| ATTEMPT-022 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (inner/outer local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.125 / 0.4 / 0.5` | 5 | - | - | - | - | - | - | pending | `attempts/ATTEMPT-022/` |
| ATTEMPT-023 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (inner/outer local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.15 / 0.4 / 0.5` | 5 | - | - | - | - | - | - | pending | `attempts/ATTEMPT-023/` |
| ATTEMPT-024 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (bridge toward ATTEMPT-003 outer ratio) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.2 / 0.4 / 0.5` | 5 | - | - | - | - | - | - | pending | `attempts/ATTEMPT-024/` |
| ATTEMPT-025 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (lower outer ratio check) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.075 / 0.25 / 0.5` | 5 | - | - | - | - | - | - | pending | `attempts/ATTEMPT-025/` |
| ATTEMPT-026 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (lower outer with higher inner check) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.075 / 0.35 / 0.5` | 5 | - | - | - | - | - | - | pending | `attempts/ATTEMPT-026/` |
| ATTEMPT-027 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (dropout local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.125 / 0.3 / 0.3` | 5 | - | - | - | - | - | - | pending | `attempts/ATTEMPT-027/` |
| ATTEMPT-028 | param_tune | `clip_a_self_outer_ratio` + `clip_a_self_inner_ratio` + `clip_a_self_dropout` (dropout local sweep) | `4 / 0.1 / 0.25 / 0.5` | `4 / 0.125 / 0.3 / 0.4` | 5 | - | - | - | - | - | - | pending | `attempts/ATTEMPT-028/` |

## Notes

- ATTEMPT-002 through ATTEMPT-006 changed only trial-local parameters; the TRIAL-001 code path itself did not change.
- ATTEMPT-007 is a clean confirmation of the ATTEMPT-003 config from pre-run freeze commit `2820b17`.
- ATTEMPT-008 is a second clean confirmation of the same config from pre-run freeze commit `8b6acac`.
- ATTEMPT-003 remains the highest observed setting, but ATTEMPT-007 and ATTEMPT-008 did not confirm it; promotion remains blocked.
