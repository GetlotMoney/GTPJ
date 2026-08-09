# ATTEMPT-011 Work Items

## Planned

| Type | Count | 说明 |
|---|---:|---|
| search | 120 | 复用 H76 100 组搜索框架，并新增 20 个 top4 周边微调点。 |
| same-seed repeat | 40 | DR-020 / DR-051 / DR-041 / DR-047 各 seed=5 exact repeat 10 次。 |
| ablation | 40 | 四个 top4 候选各 10 个机制/参数 ablation。 |

## Acceptance

- 4 个 batch 合计 200 jobs 必须有明确 completed / failed / skipped 结论。
- 每个 top4 候选单独统计 repeat 的 best / mean / min / max / range。
- ablation 只作为机制支持证据，不能单独触发 promotion。
