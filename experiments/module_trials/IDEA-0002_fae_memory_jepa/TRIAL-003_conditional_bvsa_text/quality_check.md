# Quality Check

```text
runtime: local unit tests plus server main100 batch
decision: pass_owner_activation_with_warning
promotion_decision: owner_activate
promote_to: v5
evidence_level: confirmation_grade
confirmation_status: owner_activated_provisional
```

## Scope

Code, config, and post-run evidence for `TRIAL-003_conditional_bvsa_text`.

## Findings

- Branch-local config enables `bvsa_text_mode: conditional`.
- The active v5 config enables `bvsa_text_mode: conditional`, `sgmp_text_mode: conditional`, and `jepa_text_mode: conditional`.
- Legacy config names are retained only as marked aliases for older configs/checkpoints.
- Tests cover framework-only keys, legacy-only keys, and framework-key priority on conflicts.
- No raw logs, checkpoints, generated figures, or cache files were added.
- The main100 run produced best observed `H=74.54` and frozen-repeat mean `H=74.44`.
- `GTPJ-v4 confirmed_H=74.45` remains the stronger confirmed reference.

## Quality Checks

- [x] Base version is explicit: `v3`.
- [x] Config copy exists at `attempts/ATTEMPT-001/config.yaml`.
- [x] Result status is explicitly `owner_activated_provisional`.
- [x] Class order, seen/unseen split, label mapping, logits shape, and metric calculation are unchanged.
- [x] `config/versions/v5.yaml`, `experiments/v5/config.yaml`, `experiments/v5/baseline/config.yaml`, and `config/GTPJ_cub_gzsl.yaml` are synchronized.
- [x] Main config and trial config expose PSE/ICSA/FGVD/BVSA/SGMP names first, with old names marked as legacy aliases.
- [x] GitHub directory contains only lightweight records.
- [x] External log artifact id/URI/hash/size are recorded in `experiments/v5/baseline/manifest.yaml`.

## Follow-up

- Future v5 tuning should use `config/versions/v5.yaml`.
- Future confirmation should compare repeat mean against `GTPJ-v4 confirmed_H=74.45`.
