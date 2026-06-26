# CONFIRM-001_v1_seed5 Result

## Summary

Kind: `confirmation`.
Baseline H: `73.93`; observed H: `73.77`; delta H: `-0.16`.

## Metrics

| U | S | H | ZS | Best epoch |
|---:|---:|---:|---:|---:|
| 71.35 | 76.35 | 73.77 | 81.24 | 32 |

## Evidence

```text
log_artifact_id: log:v1:confirmation:CONFIRM-001:attempt-001
log_uri: warehouse://gtpj/runs/v1/confirmation/CONFIRM-001/attempt-001/logs/training_log_CUB_2026-06-26_14-19-01.txt
log_sha256: b00c62d59ac96929a1b9482dff3b4b2a19b3da0510b886a9caf28d9abb9fc5d3
best_checkpoint_artifact_id: checkpoint:v1:confirmation:CONFIRM-001:attempt-001:best
full_checkpoint_artifact_id: checkpoint:v1:confirmation:CONFIRM-001:attempt-001:full
```

## Warning

`conda run` emitted a UnicodeEncodeError after the training script completed. The final training log contains `Training Finished!` and the complete `Best Results @ Epoch 32` block, so metrics are recorded from the training log.

## Decision

keep
