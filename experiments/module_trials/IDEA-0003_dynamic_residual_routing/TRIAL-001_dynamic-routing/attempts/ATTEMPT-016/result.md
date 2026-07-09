# ATTEMPT-016 Result

当前状态：running。服务器 Runner 仍在运行，当前 4 completed / 2 running / 4 pending / 0 failed。

已完成的 4 个 job 全部属于 `A015DR004`。当前 best 是 `DR-003`，H=74.84，U=72.82，S=76.97，ZS=81.91，best_epoch=50。它低于 restore target H=75.04，只能记录为 `near_miss_not_restored`，不能算 restored，不能 confirmation，不能 promotion。

| Candidate | Source H | Best repeat H | Mean | Min | Max | Range | Restored |
|---|---:|---:|---:|---:|---:|---:|---|
| A015DR004 | 75.04 | 74.84 | 74.66 | 74.47 | 74.84 | 0.37 | no; near miss only, repeat 5 running |
| A015DR035 | 75.00 | pending | pending | pending | pending | pending | first repeat running |

promotion 当前保持 blocked。
