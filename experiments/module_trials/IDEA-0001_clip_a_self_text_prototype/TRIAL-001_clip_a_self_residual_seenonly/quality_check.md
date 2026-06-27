# Quality Check

```text
runtime:
quality_check_mode: STRICT
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

- Code layer: `train_GTPJ_CUB.py`, `model/MyModel.py`
- Trial ledger: `experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly/`
- Current recorded sweep: `ATTEMPT-009` through `ATTEMPT-020`
- Failed startup: `ATTEMPT-021`, not valid result evidence

## Findings

- `ATTEMPT-019` is the current best observed setting: `H=74.29`, `U=71.32`, `S=77.52`, `ZS=81.59`.
- The result improves over the authoritative v1 baseline by `+0.36 H`.
- The U/S gap is large: `S - U = 6.20`, so the result is seen-heavy.
- `ATTEMPT-019` started from a clean run commit (`453acc0`) and has complete artifact registration.
- No code-path change occurred during `ATTEMPT-009` through `ATTEMPT-020`; these are trial-internal parameter attempts.
- `ATTEMPT-021` failed before epochs began. It is documented in `docs/workflow/issues/2026-06-27-trial001-batch-runner-and-tag-boundary.md` and is excluded from result evidence.

## Artifact Check

- [x] `log:v1:module_trial:TRIAL-001:attempt-019` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-019:best` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-019:full` exists in Warehouse.
- [x] `receipt:v1:module_trial:TRIAL-001:attempt-019:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] No raw logs, checkpoints, generated figures, or feature caches are tracked in Git.
- [x] Owner accepted `ATTEMPT-019` as `GTPJ-v2` current mainline code evidence on 2026-06-27.

## Promotion Gate

- [x] parent_version / parent_tag remain `v1`.
- [x] baseline H, current best H, and delta H are explicit.
- [x] U/S/ZS, best epoch, and seed are explicit.
- [x] current best config path is explicit.
- [x] class order, seen/unseen split, logits shape, and metric calculation are unchanged.
- [x] artifact boundary is complete for the current best attempt.
- [x] owner activation review records the current best as `best_observed_H`.
- [ ] promotion remains blocked until `evidence_level: baseline_grade`.
- [ ] `ATTEMPT-019` has not yet been clean-confirmed; this is a follow-up requirement.
- [ ] seen-heavy behavior needs follow-up analysis.

## Decision

PASS_OWNER_ACTIVATED_UNCONFIRMED.

`ATTEMPT-019` is accepted as the current best observed experiment record for TRIAL-001 and is
owner-activated as `GTPJ-v2` current mainline code. Clean confirmation and seen-bias analysis remain
required follow-ups before any confirmed/baseline-grade claim.
