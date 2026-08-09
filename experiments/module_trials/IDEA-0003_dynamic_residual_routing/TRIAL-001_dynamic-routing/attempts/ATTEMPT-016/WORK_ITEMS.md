# ATTEMPT-016 Work Items

| Work item | Type | Count | 说明 |
|---|---|---:|---|
| RESTORE-001 | exact_repeat | 5 | A015DR004 / ATTEMPT-015 DR-004，restore_target_H=75.04 |
| RESTORE-002 | exact_repeat | 5 | A015DR035 / ATTEMPT-015 DR-035，restore_target_H=75.00 |

## Stop Rule

每个候选独立判断。某个候选任一 clean repeat 达到自己的 `restore_target_H` 后，只跳过该候选尚未启动的 repeat；另一个候选继续跑到 restored 或 5 次上限。

