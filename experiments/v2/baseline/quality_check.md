# GTPJ-v2 Baseline Quality Check

```text
quality_check_mode: STRICT_WITH_OWNER_OVERRIDE
decision: PASS_OWNER_ACTIVATED_UNCONFIRMED
promotion_decision: blocked
promote_to: v2
owner_override: true
evidence_level: valid_single_run
best_observed_H: 74.29
confirmed_H: pending
confirmation_status: needs_confirmation
```

## Scope

- Parent baseline: `GTPJ-v1 / tag v1 / H=73.93`
- Promoted trial: `TRIAL-001_clip_a_self_residual_seenonly`
- Promoted attempt: `ATTEMPT-019`
- Active mainline target: `GTPJ-v2 / tag v2`
- Evidence status: `valid_single_run`; `H=74.29` is `best_observed_H`, not `confirmed_H`.

## Findings

- `ATTEMPT-019` metrics are `U=71.32`, `S=77.52`, `H=74.29`, `ZS=81.59`, `best_epoch=33`.
- `H` improves over `GTPJ-v1` by `+0.36`.
- Artifact registration is complete for log, best checkpoint, full checkpoint, and runner console receipt.
- Raw logs and checkpoints remain outside GitHub in Warehouse.
- Label mapping, seen/unseen split, class order, logits shape, and metric calculation are recorded as unchanged.
- `config/versions/v2.yaml`, `experiments/v2/config.yaml`, and `experiments/v2/baseline/config.yaml` are frozen from ATTEMPT-019.

## Promotion Gate

- [x] Parent version and parent tag are explicit: `v1`.
- [x] Source trial, source attempt, source run commit, and source record commit are explicit.
- [x] Baseline H, v2 H, delta H, U/S/ZS, seed, and best epoch are explicit.
- [x] Source config and v2 config snapshots are explicit and have the same SHA256.
- [x] External log artifact id, URI, sha256, and size are recorded.
- [x] Artifact boundary passes: no raw logs, checkpoints, generated figures, or cache files are tracked.
- [x] Evaluation contract is unchanged.
- [x] Owner explicitly requested that the current best result become the current mainline code on 2026-06-27.
- [x] Owner override and missing confirmation are explicitly recorded.
- [ ] Independent clean confirmation is still recommended.
- [ ] Baseline-grade promotion evidence is blocked until clean confirmation passes.
- [ ] Seen-heavy behavior still needs follow-up analysis.

## Decision

PASS_OWNER_ACTIVATED_UNCONFIRMED.

`GTPJ-v2` is accepted as the current mainline code by owner decision. The remaining confirmation
and U/S-gap risks are preserved as blocking follow-up requirements before any confirmed/baseline-grade claim.
