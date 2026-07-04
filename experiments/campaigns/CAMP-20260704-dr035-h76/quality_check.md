# Quality Check

campaign_id: `CAMP-20260704-dr035-h76`
decision: pre_run_allow_after_freeze

## Pre-run Checks

- [x] 任务进入 formal evidence 范围，使用真实 temporary agents。
- [x] 服务器资源只读检查通过。
- [x] GZSL hard rules 已由 Interface Checker 放行。
- [x] Evidence Quality Checker 要求的 campaign / attempt 证据目录已规划。
- [x] helper 新增 profile 已通过 `pytest` 和本地 debug plan 生成检查。
- [ ] 本地 freeze commit 尚未写入。
- [ ] 服务器尚未同步到 freeze commit。
- [ ] ATTEMPT-008 / ATTEMPT-009 尚未启动。

## Decision Boundary

`ATTEMPT-008` 可以产生 min6 exact repeat evidence。`ATTEMPT-009` 只能产生 score search / tune evidence；任何单次高分都必须再进入独立 repeat。
