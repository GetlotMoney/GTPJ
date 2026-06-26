# TRIAL-001 Attempts

This trial currently has one recorded run. The root-level `config.yaml`, `manifest.yaml`, `result.yaml`, `quality_check.md`, and `result.md` act as the legacy evidence files for `ATTEMPT-001`.

## Attempts

| Attempt ID | Type | Parameter / Change | Old | New | Seed | U | S | H | ZS | Best epoch | Log artifact | Decision | Directory |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| ATTEMPT-001 | param_tune | `clip_a_self_residual_seenonly` baseline trial run | - | - | 5 | 72.32 | 75.19 | 73.72 | 81.13 | 30 | `log:v1:module_trial:TRIAL-001:attempt-001` | revise | `.` |

## Notes

- This trial was created before the dedicated `attempts/ATTEMPT-xxx/` layout was added to the workflow.
- Any new attempt added after this point should be appended here and, unless there is a compatibility reason not to, should use the new `attempts/ATTEMPT-xxx/` subdirectory layout.
