# Quality Checker Memory

## Standing Lessons

- 不只看 H 分数；必须看证据链完整性和边界。
- GitHub 只保存轻量记录；raw logs、checkpoints、generated figures 留在 Warehouse。
- memory 只能提示风险，不能当证据。

## Recurrent Failure Modes

- 结果提升但 manifest/result/quality/artifact hash 不完整。
- GitHub 中混入日志、权重、cache 或生成大文件。
- 只看一次 best run，缺 confirmation 或 variance 判断。

## Required Checks

- `manifest.yaml`
- `result.yaml`
- `result.md`
- `quality_check.md`
- `agent_summary.md`
- Warehouse artifact id/URI/hash/size
- `audit-boundary`

## Update Rules

证据链、artifact 边界或质量门问题重复出现时更新本文件。
