# Runner Memory

## Standing Lessons

- Runner 只按冻结配置运行，不自行改参数、代码或实验语义。
- GPU Runner 必须串行并持有 lock。
- GTPJ 训练默认使用 `dvsr_gpu` 环境。

## Recurrent Failure Modes

- 用系统 Python 启动训练导致环境错误。
- 运行前新增 attempt config 或账本但没有 pre-run freeze commit。
- 把 debug/smoke 输出误当有效实验结果。

## Required Checks

- conda/env 是否为 `dvsr_gpu`
- GPU lock 状态
- run_commit 是否明确
- config、seed、dataset、split 是否冻结
- raw logs/checkpoints 是否写入 Warehouse 而不是 GitHub。

## Update Rules

环境、GPU、run_commit 或 frozen config 问题重复出现时更新本文件。
