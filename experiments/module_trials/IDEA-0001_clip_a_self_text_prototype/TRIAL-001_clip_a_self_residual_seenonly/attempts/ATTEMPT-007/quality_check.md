# Quality Check

```text
runtime:
quality_check_mode: STRICT
decision: PASS_REVISE_NOT_CONFIRMED
promotion_decision: blocked
```

## Scope

- Code path: unchanged from the TRIAL-001 implementation line in `train_GTPJ_CUB.py` and `model/MyModel.py`
- Attempt config: `experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly/attempts/ATTEMPT-007/config.yaml`
- Confirmation target: `ATTEMPT-003`
- Pre-run freeze commit: `2820b17c222bd2084292d5249d429dce95d1e060`

## Findings

- The run started from a clean pre-run freeze commit.
- The config is byte-identical to ATTEMPT-003 and has the same sha256: `2970fa444cdee33f5690198018f39bd10c801d53c74d03eec8886ecc8fe63622`.
- Interface semantics remain unchanged: no eval path, split, class order, label mapping, logits shape, or metric calculation change was introduced.
- ATTEMPT-007 reached H=73.69, which does not confirm ATTEMPT-003 H=74.27.

## Quality Check

- [x] Code branch and run commit recorded.
- [x] Attempt-local config saved in the attempt directory.
- [x] External log and checkpoints copied to Warehouse.
- [x] Evaluation semantics unchanged.
- [x] No raw logs, checkpoints, generated figures, or caches are tracked in Git.
- [x] Result is downgraded to `not_confirmed` rather than used for promotion.

## Interface Check

```text
class_order: unchanged
seen_unseen_split: unchanged
label_mapping: unchanged
logits_shape: unchanged
metric_calculation: unchanged
loss_path: unchanged from TRIAL-001
```

## Artifact Check

- [x] `log:v1:module_trial:TRIAL-001:attempt-007` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-007:best` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-007:full` exists in Warehouse.
- [x] `receipt:v1:module_trial:TRIAL-001:attempt-007:runner_console` exists in Warehouse.

## Decision

PASS_REVISE_NOT_CONFIRMED.

ATTEMPT-007 is valid evidence, but it blocks promotion because the clean confirmation did not reproduce ATTEMPT-003.
