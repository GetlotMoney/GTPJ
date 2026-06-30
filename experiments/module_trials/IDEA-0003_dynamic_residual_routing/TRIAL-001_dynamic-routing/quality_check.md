# Quality Check

```text
runtime: local pre-run
quality_check_mode: STRICT
decision: allow
promotion_decision: not_applicable
evidence_level: pre_run
confirmation_status: pending
```

## Scope

Files checked:

- `model/MyModel.py`
- `train_GTPJ_CUB.py`
- `workflow/gtpj_workflow.py`
- `tests/test_fae_memory_jepa.py`
- `tests/test_gtpj_workflow.py`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/config.yaml`

## Findings

- Config defaults are anchored to v5 values and dynamic routing is default-off in the trial config.
- Runner writes lightweight status under `.gtpj_runtime/batches` and copies per-job logs/configs/generated training artifacts into Warehouse.
- Failed jobs are recorded as `failed` and do not block the rest of the batch.
- Top2 repeats wait until exploration jobs are completed/failed/skipped, then copy the frozen top-ranked config.
- `docs/diagrams/` is unrelated pre-existing untracked local content and must remain excluded from this branch.

## Blocking Issues

None after revision.

Initial Quality Checker blocking issues and fixes:

- Runner setup exceptions could leave jobs `running`; fixed with `try/except` that records `failed`, summary row, event, and error receipt.
- Warehouse root was only recorded in plan; fixed with `warehouse_attempt_dir`, artifact copy, and `artifact_manifest.json`.
- Ledger was not final while worktree was dirty; final commit/push will be the pre-run freeze source.

## Quality Checklist

- [x] Code snapshot and base version are explicit.
- [x] Config copy is saved in the trial directory.
- [x] Runtime batch status is lightweight and ignored by Git.
- [x] Raw logs/checkpoints are copied to Warehouse by the server runner.
- [x] No eval/class order/logits shape change is declared or observed.
- [x] seen/unseen split, label mapping, class order, and metric calculation are unchanged.
- [x] GitHub does not include raw logs, checkpoints, or generated runtime outputs.

## Promotion Gate

Not applicable in this branch. This trial does not create `v6` and does not switch `main`.

## Verification

```bash
python -m pytest tests/test_fae_memory_jepa.py -q
python -m pytest tests/test_gtpj_workflow.py -q -k dynamic_routing
python -m py_compile model/MyModel.py workflow/gtpj_workflow.py train_GTPJ_CUB.py
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py audit-boundary
git diff --check
```
