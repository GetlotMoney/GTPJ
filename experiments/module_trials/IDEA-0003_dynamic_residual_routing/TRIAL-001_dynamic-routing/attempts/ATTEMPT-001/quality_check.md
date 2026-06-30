# ATTEMPT-001 Quality Check

```text
attempt_id: ATTEMPT-001
run_id: RUN-20260630-0005-dynroute50-2gpu
decision: revise
promotion_decision: rejected
checkpoint_retention: applied
```

## Checks

- [x] Batch completed: 50 completed / 0 failed.
- [x] `summary.csv`, `summary.jsonl`, `batch_status.json`, `plan.json`, and `events.jsonl` were copied into Warehouse summary storage.
- [x] Artifact hashes were recorded in the attempt manifest.
- [x] Analysis was run with `analyze-dynamic-routing-batch --top-k 12`.
- [x] Best dynamic single and repeat means were compared against v4 confirmed H=74.45 and v5 repeat mean H=74.44.
- [x] Promotion is rejected in the ledger.
- [x] Model checkpoint retention was applied after the experiment.

## Retention Result

Retained model checkpoints:

- DR-001 H=74.40
- DR-008 H=74.39
- DR-023 H=74.38

Deleted model checkpoint files: 97.

Non-model artifacts were retained.
