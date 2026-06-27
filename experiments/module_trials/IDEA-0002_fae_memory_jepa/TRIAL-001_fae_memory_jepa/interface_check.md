# Interface Check: TRIAL-001_fae_memory_jepa

```text
review_round: Review 2
role: Interface Checker
agent_instance_type: sub_agent
decision: allow
runner_status: allowed_after_clean_pre_run_freeze_commit
```

## Inputs Checked

- `model/MyModel.py`
- `train_GTPJ_CUB.py`
- `tests/test_fae_memory_jepa.py`
- `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-001_fae_memory_jepa/implementation.md`
- `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-001_fae_memory_jepa/attempts/ATTEMPT-001/config.yaml`
- `docs/workflow/code_interface_contract.md`
- `docs/workflow/innovation_code_review_protocol.md`

## Contract Verdict

| Check | Verdict | Evidence |
|---|---|---|
| Baseline-off switch | allow | `jepa_context_mode` defaults to `embed`; invalid values raise `ValueError`. |
| Switch-on path | allow | `fae_memory` requires `use_fae=True` and builds context from keep-token FAE memory. |
| Target leakage guard | allow | Target is detached pre-FAE `patch_z`; FAE context is recomputed from keep tokens only. |
| Selected patch alignment | allow | Selected patches, selected indices, mask, target, and FAE geometry share the same selected token set. |
| Positive gradient path | allow | Unit test checks JEPA positive loss reaches FAE, visual projection, text projection, and CLIP-A-self adapter. |
| Negative gradient detach | allow | Unit test checks negative JEPA alone does not backpropagate into FAE. |
| Train logits shape | allow | Unit test checks train logits `[B, 150]` and `logits_200` `[B, 200]`. |
| Eval logits shape | allow | Unit test checks eval logits `[B, 200]`. |
| Label mapping / split / class order | allow | No evaluator, dataset split, class index, or `_global_to_seen_labels` logic changed. |
| Metric semantics | allow | GZSL U/S/H/ZS evaluator path is unchanged. |

## Findings

- The implementation matches Review 1's requested mode split: `embed` preserves old AG-JEPA behavior, while `fae_memory` changes only the auxiliary JEPA visual context.
- The new auxiliary outputs from `CrossModalTransformer.forward` are used only for JEPA loss bookkeeping and do not replace scoring tensors.
- `geometry_for_indices` centralizes full-grid and selected-token FAE geometry construction, reducing mismatch risk between main FAE and JEPA FAE context.
- The formal Runner is still blocked until the worktree is clean and the pre-run freeze commit is created.

## Blocking Issues

None after the current code diff and tests.

## Non-Blocking Issues

- Post-run Review 3 must verify that the training log, manifest, result, and Warehouse artifact hashes all refer to the same run.
- A single ATTEMPT-001 run can establish `best_observed_H`, not `confirmed_H` or `baseline_grade`.

## Evidence Refs

- `model/MyModel.py`
- `tests/test_fae_memory_jepa.py`
- `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-001_fae_memory_jepa/code.diff`

```text
memory_used: yes
memory_sources: docs/workflow/agents/shared_roles/interface_checker/memory.md
verified_against_current_repo: yes
```
