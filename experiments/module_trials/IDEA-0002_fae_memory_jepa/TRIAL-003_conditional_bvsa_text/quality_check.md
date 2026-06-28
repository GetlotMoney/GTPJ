# Quality Check

```text
runtime: local unit tests only
decision: pass_code_verified_not_run
promotion_decision: not_applicable
evidence_level: code_verified_not_run
confirmation_status: not_run
```

## Scope

Code and config preparation for `TRIAL-003_conditional_bvsa_text`.

## Findings

- Branch-local config enables `bvsa_text_mode: conditional`.
- Frozen v3 baseline config is not modified.
- No raw logs, checkpoints, generated figures, or cache files were added.
- No training result has been produced.

## Quality Checks

- [x] Base version is explicit: `v3`.
- [x] Config copy exists at `attempts/ATTEMPT-001/config.yaml`.
- [x] Result status is explicitly `not_run`.
- [x] Class order, seen/unseen split, label mapping, logits shape, and metric calculation are unchanged.
- [x] GitHub directory contains only lightweight records.
- [ ] External log artifact id/URI/hash/size are absent because Runner has not started.

## Must Fix Before Training

- Commit a pre-run freeze.
- Start Runner only from a clean worktree.
- Record attempt manifest/result/quality after the run.
