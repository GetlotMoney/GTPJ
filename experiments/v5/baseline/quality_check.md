# GTPJ-v5 Baseline Quality Check

```text
quality_check_mode: OWNER_ACTIVATION_WITH_REPEAT_EVIDENCE
decision: PASS_OWNER_ACTIVATION_WITH_WARNING
status: owner_activated_provisional
promotion_decision: blocked
owner_activation_decision: owner_activate
promote_to: v5
evidence_level: confirmation_grade
best_observed_H: 74.54
confirmed_H: 74.44
confirmation_status: owner_activated_provisional
active_main_update: activated
```

## Scope

- Parent confirmed reference: `GTPJ-v4 / tag v4 / confirmed_H=74.45`.
- Source trial: `TRIAL-003_conditional_bvsa_text`.
- Source batch: `RUN-20260630-0002-trial003-main100-2gpu`.
- Source config: `trial003-main100-069`.
- Formal tag target: `GTPJ-v5 / tag v5`.
- Evidence status: same-config repeat evidence exists, but repeat mean does not exceed v4 confirmed reference.

## Findings

- `all_text_cond` enters BVSA when `bvsa_text_mode=conditional`; BVSA `local_score` has shape `[B, C]` and gradient reaches ICSA.
- Source config `trial003-main100-069` produced `H=74.43`.
- Frozen repeats 091-095 produced `H=74.49 / 74.43 / 74.35 / 74.41 / 74.54`.
- Best observed repeat is `H=74.54`, but repeat mean is `H=74.44`.
- The repeat mean is slightly below `GTPJ-v4 confirmed_H=74.45`; this is an owner activation, not a stronger confirmed-baseline claim.
- Raw logs, receipts, checkpoints, generated figures, and cache files remain outside GitHub.
- Label mapping, seen/unseen split, class order, logits shape, and metric calculation are recorded as unchanged.
- `config/versions/v5.yaml`, `experiments/v5/config.yaml`, `experiments/v5/baseline/config.yaml`, and `config/GTPJ_cub_gzsl.yaml` are identical.

## Promotion Gate

- [x] Parent version and parent tag are explicit: `v4`.
- [x] Source trial, source batch, source config, and repeat jobs are explicit.
- [x] Best observed H, repeat mean H, U/S/ZS, seed, and best epoch are explicit.
- [x] Local v5 config snapshots are identical and hashed.
- [x] External artifact ids, URIs, sha256, and sizes are recorded in `manifest.yaml`.
- [x] Artifact boundary passes: no raw logs, checkpoints, generated figures, or cache files are tracked.
- [x] Evaluation contract is unchanged.
- [x] Owner explicitly requested activation as the new mainline.
- [x] Evidence caveat is explicit: v4 remains the stronger confirmed reference by repeat mean.

## Decision

PASS_OWNER_ACTIVATION_WITH_WARNING.

`GTPJ-v5` is now the active mainline and future tuning base. `GTPJ-v4` remains the stronger confirmed reference until v5 or a later candidate clears it by repeat evidence.
