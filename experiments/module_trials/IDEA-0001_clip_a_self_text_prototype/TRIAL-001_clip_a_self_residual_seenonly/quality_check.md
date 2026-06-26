# Quality Check

```text
runtime:
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: blocked
```

## Scope

- Code layer: `train_GTPJ_CUB.py`, `model/MyModel.py`
- Trial ledger: `experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly/`
- Parameter sweep: ATTEMPT-002 to ATTEMPT-006 under the same TRIAL-001 implementation line
- Clean confirmation: ATTEMPT-007 reruns ATTEMPT-003 config from pre-run freeze commit `2820b17`

## Findings

- Interface semantics remain unchanged across all five attempts.
- ATTEMPT-003 is the best setting: `H=74.27`, `U=71.76`, `S=76.97`, `ZS=81.72`.
- ATTEMPT-007 clean confirmation reached `H=73.69`, `U=70.82`, `S=76.80`, `ZS=80.91`; it does not confirm ATTEMPT-003.
- The sweep itself ran on a dirty worktree because attempt-local configs and ledger rows were added before execution.
- ATTEMPT-007 did start from a clean pre-run freeze commit, so its negative confirmation is valid evidence.
- No code-path change occurred after the original TRIAL-001 implementation snapshot.

## Quality Check

- [x] Code snapshot and base version are explicit.
- [x] Attempt-local configs are saved in the trial directory.
- [x] External log and checkpoint artifacts are registered in Warehouse.
- [x] Result semantics are explicit and unchanged.
- [x] No new raw logs, checkpoints, or generated figures are tracked in Git.

## Interface Precheck

```text
shape_probe_ok
switch_off_max_abs_diff: 0.0
switch_on_logits: [2, 150]
switch_on_logits_200: [2, 200]
loss_keys: loss, loss_CE, loss_consist, loss_jepa, loss_jepa_neg, loss_msdn, loss_msdn_gate, loss_topo
```

## Artifact Check

- [x] `log:v1:module_trial:TRIAL-001:attempt-003` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-003:best` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-003:full` exists in Warehouse.
- [x] `receipt:v1:module_trial:TRIAL-001:attempt-003:runner_console` exists in Warehouse.
- [x] `log:v1:module_trial:TRIAL-001:attempt-007` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-007:best` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-007:full` exists in Warehouse.
- [x] `receipt:v1:module_trial:TRIAL-001:attempt-007:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.

## Promotion Gate

- [x] parent_version / parent_tag remain `v1`.
- [x] baseline H, best-attempt H, and delta H are explicit.
- [x] U/S/ZS, best epoch, and seed are explicit.
- [x] trial config path for the best setting is explicit.
- [x] class order, seen/unseen split, logits shape, and metric calculation are unchanged.
- [x] clean confirmation of the best setting has been completed as ATTEMPT-007.
- [ ] clean confirmation did not reproduce ATTEMPT-003; promotion remains blocked.
- [ ] promotion review has not upgraded `trial_decision` to `promote`.

## Decision

PASS_REVISE.

The sweep produced a higher observed setting, but ATTEMPT-007 clean confirmation did not reproduce it. Promotion remains blocked, and TRIAL-001 should stay in revise.
