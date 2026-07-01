# Quality Check

Status: PASS_CONFIRMED_CONFIG

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
| v3 baseline result not overwritten | PASS | Confirmed config record does not mutate v3. |
| Confirmed config target recorded | PASS | `promotion_decision: confirmed_config_only`, pure tuning stays under `v3` |
| Boundary audit required | PASS | `workflow/gtpj_workflow.py audit-boundary` must pass before commit |

## Notes

- `local-v3-054` is baseline-grade under the owner standing min3 rule because all three repeats exceed the accepted v3 reference `H=74.27`.
- The formal confirmed result uses the best successful repeat after the min3 cluster passed: `confirmed_H=74.47`; `H_mean=74.45` remains stability evidence.
- `local-v3-022` and `trial003-tune-026` are intentionally not promoted by this record; their min3 repeats did not reproduce their strongest single-run values.
- This ledger record confirms `local-v3-054` under `GTPJ-v3`; it is not an automatic mutation of the canonical v3 result and does not activate current code aliases.
