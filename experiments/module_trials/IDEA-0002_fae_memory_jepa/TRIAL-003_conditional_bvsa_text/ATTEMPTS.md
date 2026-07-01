# TRIAL-003 Attempts

| Attempt ID | Type | Parameter / Change | Old | New | Seed | U | S | H | ZS | Best epoch | Log artifact | Decision | Directory |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|
| ATTEMPT-001 | code_setup | BVSA text input | `bvsa_text_mode=adapted`; BVSA uses `all_text [C,768]` | `bvsa_text_mode=conditional`; BVSA uses `all_text_cond [B,C,768]` | 5 | | | | | | | code_verified | `attempts/ATTEMPT-001/` |
| MAIN100-069 | tune | `pse_outer_ratio` / `clip_a_self_outer_ratio`; `local_weight` | `0.15`; `0.3` | `0.65`; `0.2` | 5 | 71.90 | 77.16 | 74.43 | 81.62 | 34 | `summary:v3:module_trial:TRIAL-003:main100` | source_for_v5 | Warehouse main100 |
| MAIN100-091 | confirmation | frozen repeat of MAIN100-069 | same | same | 5 | 71.80 | 77.40 | 74.49 | 81.68 | 45 | `summary:v3:module_trial:TRIAL-003:main100` | repeat_ok | Warehouse main100 |
| MAIN100-092 | confirmation | frozen repeat of MAIN100-069 | same | same | 5 | 71.90 | 77.14 | 74.43 | 81.52 | 34 | `summary:v3:module_trial:TRIAL-003:main100` | repeat_ok | Warehouse main100 |
| MAIN100-093 | confirmation | frozen repeat of MAIN100-069 | same | same | 5 | 71.63 | 77.29 | 74.35 | 81.48 | 34 | `summary:v3:module_trial:TRIAL-003:main100` | repeat_ok | Warehouse main100 |
| MAIN100-094 | confirmation | frozen repeat of MAIN100-069 | same | same | 5 | 72.53 | 76.40 | 74.41 | 81.45 | 33 | `summary:v3:module_trial:TRIAL-003:main100` | repeat_ok | Warehouse main100 |
| MAIN100-095 | confirmation | frozen repeat of MAIN100-069 | same | same | 5 | 72.13 | 77.11 | 74.54 | 81.65 | 34 | `summary:v3:module_trial:TRIAL-003:main100` | best_observed_and_owner_activate | Warehouse main100 |

## Notes

- This is a new implementation hypothesis relative to TRIAL-002 because BVSA now directly consumes sample-conditioned text.
- The main100 batch completed 100 jobs with 95 conditional-mode ok runs, 4 adapted-mode ok controls, and 1 failed job.
- `trial003-main100-069` is the source config promoted to `GTPJ-v5`; `trial003-main100-095` is the best observed frozen repeat.
- Frozen repeat mean for 091-095 is `H=74.44`, so this is owner activation for future tuning, not a stronger confirmed reference than `v3/CONFIRM-001 local-v3-054 confirmed_H=74.47`.
