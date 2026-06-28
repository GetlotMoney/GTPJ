# GTPJ-v3 Baseline Quality Check

```text
quality_check_mode: STRICT_WITH_OWNER_STOCHASTIC_OVERRIDE
decision: PASS_OWNER_ACCEPTED_STOCHASTIC_UNCONFIRMED
status: owner_accepted_stochastic_unconfirmed
promotion_decision: blocked
promote_to: v3
owner_override: true
evidence_level: valid_single_run
best_observed_H: 74.27
confirmed_H: pending
confirmation_status: needs_confirmation
```

## Scope

- Parent baseline: `GTPJ-v2 / tag v2 / best_observed_H=74.29 / confirmed_H=pending`
- Accepted trial: `TRIAL-002_strict_conditional_jepa`
- Accepted attempt for best observed result: `ATTEMPT-004`
- Formal tag target: `GTPJ-v3 / tag v3`
- Evidence status: `valid_single_run`; `H=74.27` is `best_observed_H`, not `confirmed_H`.

## Findings

- ATTEMPT-004 metrics are `U=71.22`, `S=77.60`, `H=74.27`, `ZS=81.38`, `best_epoch=33`.
- Clean seed-42 reruns after the freeze reached `H=74.14` and `H=74.01`.
- The mixed rerun evidence is explicitly accepted by the owner as stochastic variance for a formal tag.
- Artifact registration is complete for log, best checkpoint, full checkpoint, and runner console receipt.
- Raw logs and checkpoints remain outside GitHub in Warehouse.
- Label mapping, seen/unseen split, class order, logits shape, and metric calculation are recorded as unchanged.
- `config/versions/v3.yaml`, `experiments/v3/config.yaml`, and `experiments/v3/baseline/config.yaml` are frozen from the strict conditional JEPA config.

## Promotion Gate

- [x] Parent version and parent tag are explicit: `v2`.
- [x] Source trial, source attempt, source run commit, and source record path are explicit.
- [x] Baseline H, v3 H, delta H, U/S/ZS, seed, and best epoch are explicit.
- [x] Source config and v3 config snapshots are explicit and have the same SHA256.
- [x] External log artifact id, URI, sha256, and size are recorded.
- [x] Artifact boundary passes: no raw logs, checkpoints, generated figures, or cache files are tracked.
- [x] Evaluation contract is unchanged.
- [x] Owner explicitly accepted stochastic variance and requested a formal tag on 2026-06-28.
- [x] Owner override and missing strict confirmation are explicitly recorded.
- [ ] Independent clean confirmation / multi-seed stability remains recommended.
- [ ] Baseline-grade promotion evidence remains blocked until confirmation passes.

## Decision

PASS_OWNER_ACCEPTED_STOCHASTIC_UNCONFIRMED.

`GTPJ-v3` is accepted as a formal owner tag with stochastic variance explicitly recorded. The remaining confirmation risk is preserved before any confirmed or baseline-grade manuscript claim.
