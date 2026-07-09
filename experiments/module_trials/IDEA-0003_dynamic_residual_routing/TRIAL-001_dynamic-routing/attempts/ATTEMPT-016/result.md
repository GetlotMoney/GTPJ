# ATTEMPT-016 Result

当前状态：completed / not restored。服务器 runtime 已重新同步到本地，`RUN-20260708-0005-h76-hotspot-top2-restore10-exact-repeat-2gpu` 为 10 completed / 0 failed / 0 skipped。

本轮是 ATTEMPT-015 两个 H>=75 单次候选的 exact repeat：`A015DR004` restore target H=75.04，`A015DR035` restore target H=75.00。两个候选各完成 5 次 same-seed repeat，均未达到各自 restore target。

| Candidate | Source H | Best repeat H | Mean | Min | Max | Range | Restored |
|---|---:|---:|---:|---:|---:|---:|---|
| A015DR004 | 75.04 | 74.84 | 74.66 | 74.47 | 74.84 | 0.37 | no; near miss only |
| A015DR035 | 75.00 | 74.85 | 74.65 | 74.44 | 74.85 | 0.41 | no; near miss only |

Overall best 是 `DR-008` / `A015DR035`，H=74.85，U=72.33，S=77.56，ZS=81.75，best_epoch=49。`h_ge_75_count=0`，`restored_candidates=[]`。

结论：ATTEMPT-016 收口为 `stopped_repeat_unstable` / `not_restored`，promotion 保持 blocked。
