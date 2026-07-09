# ATTEMPT-010 Quality Check

status: `workflow_smoke_complete`
formal_confirmation_status: `incomplete`
promotion_decision: `blocked`

## Gate

- [x] Runner Monitor allow.
- [x] Interface Checker allow.
- [x] Evidence Quality Checker allow for runner start.
- [x] Named Codex thread runtime gate passed; no right-sidebar temporary agents were used.
- [x] Server batch launched on lab4090 and produced real `summary.csv` / `summary.jsonl`.
- [x] User-requested stop was recorded in server `batch_status.json`.
- [x] Server processes stopped; GPU 0/1 returned idle.
- [x] Artifact URI/hash/size recorded in `result.yaml`.
- [x] Partial per-candidate stats recorded for completed DR-020 repeats.
- [ ] Formal 20-job top4 confirmation.
- [ ] DR-020 min5 exact repeat.
- [ ] DR-051 / DR-041 / DR-047 repeats.
- [ ] Promotion gate.
- [ ] Checkpoint retention audit for skipped jobs.

## GZSL 语义

本轮不改变数据集、split、class order、label mapping、logits shape 或 U/S/H/ZS 计算。已完成的 4 条结果全部来自同一个 source candidate：`DR-020 direction_sample_h48_w0.525_a0.003`，seed 固定为 5。

## 质量结论

这次可以作为 workflow smoke 闭环证据：正式 gate、服务器 runner、summary 采集、停止与账本回写均已验证。它不能作为 ATTEMPT-010 的正式 confirmation 证据，因为 20 个计划 job 中只有 4 个完成，且 top4 候选中的 3 个没有完成任何 repeat。
