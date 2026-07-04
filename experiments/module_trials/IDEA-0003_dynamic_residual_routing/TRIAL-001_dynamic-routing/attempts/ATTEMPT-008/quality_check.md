# ATTEMPT-008 Quality Check

decision: not_confirmed
promotion_decision: blocked

## Checks

- [x] 6/6 jobs completed.
- [x] All jobs fixed source seed=5.
- [x] GZSL split、class order、label mapping、logits shape 和 U/S/H/ZS 语义未改变。
- [x] Raw logs 和 checkpoints 留在 Warehouse/runtime，不进入 Git。
- [x] Summary、events、plan 和 retained checkpoints 记录了 SHA256。
- [x] Checkpoint retention 已执行，仅保留 Top-3 model checkpoints。
- [x] mean/min/max/range 已报告。
- [ ] `mean_H>=74.60` 未通过。

## Boundary

`ATTEMPT-008` 的 best single 是 H=74.76，但正式结论按 min6 mean 判定。该结果不能 promotion，不能开新 `vX`。
