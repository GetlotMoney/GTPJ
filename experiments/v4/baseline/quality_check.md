# GTPJ-v4 Baseline Quality Check

```text
quality_check_mode: STRICT_MIN3_AUTO_PROMOTION
decision: PASS_BASELINE_GRADE
status: confirmed
promotion_decision: promote
promote_to: v4
evidence_level: baseline_grade
best_observed_H: 74.47
confirmed_H: 74.45
confirmation_status: confirmed
active_main_update: not_activated
```

## Scope

- Parent baseline: `GTPJ-v3 / tag v3 / best_observed_H=74.27 / confirmed_H=pending`
- Source confirmation: `CONFIRM-001_local_v3_054_min3`
- Source candidate: `local-v3-054`
- Formal tag target: `GTPJ-v4 / tag v4`
- Evidence status: `baseline_grade`; `confirmed_H=74.45` is the mean of 3 clean server repeats.

## Findings

- Min3 repeats are `H=74.46`, `H=74.42`, and `H=74.47`.
- All three repeats exceeded the v3 accepted reference `H=74.27`.
- The promoted configuration changes only `pse_outer_ratio`, `clip_a_self_outer_ratio`, and `local_weight`.
- Raw logs and receipts remain outside GitHub in Warehouse.
- Label mapping, seen/unseen split, class order, logits shape, and metric calculation are recorded as unchanged.
- `config/versions/v4.yaml`, `experiments/v4/config.yaml`, and `experiments/v4/baseline/config.yaml` are identical.

## Promotion Gate

- [x] Parent version and parent tag are explicit: `v3`.
- [x] Source confirmation, source run, and source config are explicit.
- [x] Baseline H, v4 confirmed H, delta H, U/S/ZS, seed, and best epoch are explicit.
- [x] Source config and v4 config snapshots are explicit and have the same SHA256.
- [x] External artifact ids, URIs, sha256, and sizes are recorded through the source manifest.
- [x] Artifact boundary passes: no raw logs, checkpoints, generated figures, or cache files are tracked.
- [x] Evaluation contract is unchanged.
- [x] Owner standing min3 rule authorizes automatic promotion without a second approval.
- [x] Promotion creates a formal version and tag; it does not run `activate-version`.

## Decision

PASS_BASELINE_GRADE.

`GTPJ-v4` is a confirmed formal version. It is the current strongest confirmed version, but it does not automatically switch active code aliases.
