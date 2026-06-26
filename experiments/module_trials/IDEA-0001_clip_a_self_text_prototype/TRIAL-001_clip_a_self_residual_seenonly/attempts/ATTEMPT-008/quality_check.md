# ATTEMPT-008 Quality Check

```text
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: blocked
```

## Scope

- Repeat clean confirmation of the ATTEMPT-003 config.
- No training-code, model-code, loss, split, class-order, label-mapping, or evaluation-semantics change.
- Run environment: `conda:dvsr_gpu`.

## Findings

- ATTEMPT-008 config is byte-identical to ATTEMPT-003 and ATTEMPT-007: sha256 `2970fa444cdee33f5690198018f39bd10c801d53c74d03eec8886ecc8fe63622`.
- Run started from clean pre-run freeze commit `8b6acac45b83cca1a255d00782d4eba7a272c4fb`.
- Training log shows `resume_from: ''`; no resume/checkpoint carryover evidence was found.
- ATTEMPT-008 reached `H=73.88`, which is `-0.39` below ATTEMPT-003 and `+0.19` above ATTEMPT-007.
- ATTEMPT-008 remains `-0.05` below the authoritative v1 baseline `H=73.93`.
- Additional train/eval cache fingerprints were captured after the run; all recorded cache mtimes precede the ATTEMPT-008 launch time.
- A real read-only Quality Checker subagent (`019f047d-13f1-7b81-820e-ef7fc34fcfc7`, Banach) independently found no evidence of config, training-code, resume/checkpoint, or artifact pollution between ATTEMPT-003 and ATTEMPT-007.

## Artifact Check

- [x] `log:v1:module_trial:TRIAL-001:attempt-008` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-008:best` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-008:full` exists in Warehouse.
- [x] `receipt:v1:module_trial:TRIAL-001:attempt-008:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] Raw logs and checkpoints are not tracked in Git.

## Promotion Gate

- [x] Config identity against ATTEMPT-003 and ATTEMPT-007 is recorded.
- [x] Clean pre-run freeze commit is recorded.
- [x] U/S/H/ZS, best epoch, and seed are recorded.
- [x] External artifacts are registered with sha256 and size.
- [ ] ATTEMPT-008 did not reproduce ATTEMPT-003.
- [ ] Promotion remains blocked.

## Decision

PASS_REVISE.

ATTEMPT-008 strengthens the conclusion that ATTEMPT-003 is not promotion-grade evidence. The available evidence points more toward run-to-run variance or high-point instability than parameter pollution.
