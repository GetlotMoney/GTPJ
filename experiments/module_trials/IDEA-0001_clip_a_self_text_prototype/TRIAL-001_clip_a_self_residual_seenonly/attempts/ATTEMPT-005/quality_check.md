# Quality Check

```text
runtime:
quality_check_mode: STRICT
decision: PASS_REJECT
promotion_decision: not_applicable
```

## Scope

- Code path: unchanged from the TRIAL-001 implementation snapshot in `train_GTPJ_CUB.py` and `model/MyModel.py`
- Attempt config: `experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly/attempts/ATTEMPT-005/config.yaml`
- This run only changed trial-local parameters; no eval path, split, class order, or logits semantics changed.

## Findings

- Interface contract remains the same as the validated TRIAL-001 implementation.
- The run used `conda:dvsr_gpu` with `--no-capture-output` to avoid the earlier `conda run` Unicode wrapper failure.
- The working tree was dirty only because attempt-local configs and ledger rows were added before execution.

## Quality Check

- [x] Code branch and code snapshot recorded.
- [x] Attempt-local config saved in the attempt directory.
- [x] External log and checkpoints copied to Warehouse.
- [x] Evaluation semantics unchanged.
- [x] No raw artifacts newly tracked in Git.

## Interface Precheck

```text
shape_probe_ok
switch_off_max_abs_diff: 0.0
switch_on_logits: [2, 150]
switch_on_logits_200: [2, 200]
loss_keys: loss, loss_CE, loss_consist, loss_jepa, loss_jepa_neg, loss_msdn, loss_msdn_gate, loss_topo
```

## Artifact Check

- [x] `log:v1:module_trial:TRIAL-001:attempt-005` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-005:best` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-005:full` exists in Warehouse.
- [x] `receipt:v1:module_trial:TRIAL-001:attempt-005:runner_console` exists in Warehouse.

## Decision

Valid evidence, but this setting underperformed the current best ATTEMPT-003. H=72.69 vs baseline 73.93 (-1.24).
