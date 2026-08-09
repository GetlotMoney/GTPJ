# GTPJ-v4 Baseline Quality Check

```text
quality_check_mode: STRICT_MIN3_AUTO_PROMOTION
decision: PASS_CONFIRMED_CONFIG
status: legacy_config_only_not_framework_version
promotion_decision: confirmed_config_only
promote_to:
evidence_level: baseline_grade
best_observed_H: 74.47
confirmed_H: 74.47
H_mean: 74.45
confirmation_status: confirmed
active_main_update: not_activated
```

## Scope

- Parent baseline: `GTPJ-v3 / tag v3 / best_observed_H=74.27 / confirmed_H=pending`
- Source confirmation: `CONFIRM-001_local_v3_054_min3`
- Source candidate: `local-v3-054`
- Historical tag target: `GTPJ-v4 / tag v4` (config-only legacy tag)
- Evidence status: `baseline_grade`; `confirmed_H=74.47` is the highest successful repeat after the min3 cluster passed, and `H_mean=74.45` is retained as stability evidence.

## Findings

- Min3 repeats are `H=74.46`, `H=74.42`, and `H=74.47`.
- All three repeats exceeded the v3 accepted reference `H=74.27`.
- The promoted configuration changes only `pse_outer_ratio`, `clip_a_self_outer_ratio`, and `local_weight`; model/training code remains the v3 frozen path.
- Raw logs and receipts remain outside GitHub in Warehouse.
- Label mapping, seen/unseen split, class order, logits shape, and metric calculation are recorded as unchanged.
- `config/versions/v4.yaml`, `experiments/v4/config.yaml`, and `experiments/v4/baseline/config.yaml` are identical.

## Promotion Gate

- [x] Parent version and parent tag are explicit: `v3`.
- [x] Source confirmation, source run, and source config are explicit.
- [x] Baseline H, confirmed config H, delta H, U/S/ZS, seed, and best epoch are explicit.
- [x] Source config and v4 config snapshots are explicit and have the same SHA256.
- [x] External artifact ids, URIs, sha256, and sizes are recorded through the source manifest.
- [x] Artifact boundary passes: no raw logs, checkpoints, generated figures, or cache files are tracked.
- [x] Evaluation contract is unchanged.
- [x] Owner standing min3 rule authorizes automatic promotion without a second approval.
- [x] Current rule correction: pure tuning creates a confirmed config/reference, not a formal framework version.

## Decision

PASS_CONFIRMED_CONFIG.

`GTPJ-v4` is a historical config-only tag for the current strongest confirmed config. It is not a formal framework version and does not automatically switch active code aliases.
