# TRIAL-001 Attempts

## Attempts

| Attempt ID | Type | Parameter / Change | Old | New | Seed | U | S | H | ZS | Best epoch | Log artifact | Decision | Directory |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| ATTEMPT-001 | valid_single_run | jepa_context_mode | embed | fae_memory | 5 | 70.32 | 77.68 | 73.82 | 81.39 | 34 | `log:v2:module_trial:TRIAL-001:attempt-001` | revise | `attempts/ATTEMPT-001/` |

## Notes

- ATTEMPT-001 tests the keep-only FAE-memory JEPA context mode: the loss branch re-runs FAE on keep tokens only. It is valid evidence for that variant, but it is not strict main-path `jepa_memory` context.
- Existing v2 values for CLIP-A-self, AG-JEPA weights, FAE, MSDN, topology, and training schedule are kept.
- ATTEMPT-001 completed from clean pre-run freeze commit `5ca8245e37856e426407612b1a95bcdcfbd92697`.
- Post-run Review 3 decision is `revise`: H=73.82 is -0.47 below active v2 `best_observed_H=74.29`
  (`confirmed_H=pending`), so this is a comparison against an unconfirmed reference, not a confirmed baseline.
- Boundary correction: the strict main-path `jepa_memory` + conditional AG-JEPA text runs are a different implementation hypothesis, so the former ATTEMPT-002/003 have been moved to `TRIAL-002_strict_conditional_jepa` as ATTEMPT-001/002.
