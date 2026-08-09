# ATTEMPT-014 Work Items

| Work item | Type | Count | 说明 |
|---|---|---:|---|
| RESTORE-001 | exact_repeat | 100 | 20 个 ATTEMPT-011 source candidates，每个 seed=5 exact repeat 最多 5 次。 |

## Stop Rule

每个候选独立判断。达到自己的 `restore_target_H` 后，只跳过该候选尚未启动的 repeat；不得因为一个候选命中就停止整个 100-job batch。

## Evidence Target

结果写回：

```text
attempts/ATTEMPT-014/manifest.yaml
attempts/ATTEMPT-014/result.yaml
attempts/ATTEMPT-014/result.md
attempts/ATTEMPT-014/quality_check.md
attempts/ATTEMPT-014/agent_summary.md
ATTEMPTS.md
```
