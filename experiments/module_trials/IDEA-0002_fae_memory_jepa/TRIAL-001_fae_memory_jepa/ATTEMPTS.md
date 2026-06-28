# TRIAL-001 Attempts

## Attempts

| Attempt ID | Type | Parameter / Change | Old | New | Seed | U | S | H | ZS | Best epoch | Log artifact | Decision | Directory |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| ATTEMPT-001 | valid_single_run | jepa_context_mode | embed | fae_memory | 5 | 70.32 | 77.68 | 73.82 | 81.39 | 34 | `log:v2:module_trial:TRIAL-001:attempt-001` | revise | `attempts/ATTEMPT-001/` |
| ATTEMPT-002 | strict main-path FAE memory + conditional AG-JEPA text | jepa_context_mode=fae_main_memory; jepa_text_mode=conditional | ATTEMPT-001 keep-only FAE context + raw CLIP text in AG-JEPA | main-path jepa_memory context + sample-conditioned adapted text in AG-JEPA | 5 | 71.15 | 77.11 | 74.01 | 81.31 | 33 | `log:v2:module_trial:TRIAL-001:attempt-002` | keep | `attempts/ATTEMPT-002/` |
| ATTEMPT-003 | confirmation | clean rerun of ATTEMPT-002 frozen config | ATTEMPT-002 valid_single_run H=74.01 | ATTEMPT-003 confirmation rerun of same config/seed | 5 | 71.32 | 77.40 | 74.24 | 81.62 | 33 | `log:v2:module_trial:TRIAL-001:attempt-003` | keep | `attempts/ATTEMPT-003/` |

## Notes

- ATTEMPT-001 tests the keep-only FAE-memory JEPA context mode: the loss branch re-runs FAE on keep tokens only. It is valid evidence for that variant, but it is not strict main-path `jepa_memory` context.
- Existing v2 values for CLIP-A-self, AG-JEPA weights, FAE, MSDN, topology, and training schedule are kept.
- ATTEMPT-001 completed from clean pre-run freeze commit `5ca8245e37856e426407612b1a95bcdcfbd92697`.
- Post-run Review 3 decision is `revise`: H=73.82 underperformed active v2 H=74.29 by -0.47.
- ATTEMPT-002 is planned to test the owner's corrected path: `context = mean(kept main-path jepa_memory)`, `target = mean(masked patch_z).detach()`, and AG-JEPA positive/negative text conditions both use sample-conditioned text.
- ATTEMPT-003 is a clean confirmation rerun of ATTEMPT-002. It reuses the same config and seed to test whether the observed `H=74.01` is reproducible before any promotion/tag decision.
