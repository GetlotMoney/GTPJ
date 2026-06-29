# Quality Check

Status: PASS_BASELINE_GRADE_PROMOTE_TO_V4

## Scope

This check covers only the server min3 reproduction evidence for `local-v3-054` and the local ledger files under `experiments/v3/confirmation/CONFIRM-001_local_v3_054_min3`.

## Checks

| Check | Status | Evidence |
|---|---|---|
| At least 3 completed repeats with H | PASS | `74.46 / 74.42 / 74.47` |
| All repeats share the same source job id | PASS | `local-v3-054` |
| All repeats use the intended config delta | PASS | `clip_a_self_outer_ratio=0.5`, `pse_outer_ratio=0.5`, `local_weight=0.1` |
| Server artifact URI, sha256, and size recorded | PASS | `manifest.yaml` |
| Warehouse registry exists | PASS | `/data/lby/projects/cv_project/GTPJ_Warehouse/ARTIFACT_REGISTRY.yaml` |
| Raw logs/checkpoints kept out of Git | PASS | Warehouse URIs only |
| Metric contract preserved | PASS | `gzsl_u_s_h_zs_v1` |
| Split, class order, and label mapping preserved | PASS | `standard_v1` |
| v3 baseline result not overwritten | PASS | Promotion creates `v4`; it does not mutate v3. |
| Formal version promotion target recorded | PASS | `promotion_decision: promote`, `promote_to: v4` |
| Boundary audit required | PASS | `workflow/gtpj_workflow.py audit-boundary` must pass before commit |

## Notes

- `local-v3-054` is baseline-grade under the owner standing min3 rule because all three repeats exceed the accepted v3 reference `H=74.27`.
- `local-v3-022` and `trial003-tune-026` are intentionally not promoted by this record; their min3 repeats did not reproduce their strongest single-run values.
- This ledger record promotes `local-v3-054` to `GTPJ-v4`, but it is not an automatic mutation of the canonical v3 result and does not activate current code aliases.
