# ATTEMPT-014 Task Start Card

能不能开工：可以做前置准备；服务器启动需等本地 gate 和服务器预检通过。

任务类型：confirmation / exact_repeat restore campaign。

基于版本/分支：v5，当前本地分支 `codex/workflow-closeout-speed-fixes`。

comparison_reference：ATTEMPT-011 source singles；ATTEMPT-013 不作为 confirmation evidence。

GitHub 写入：`attempts/ATTEMPT-014/` 和后续 `ATTEMPTS.md`。

Research/Warehouse 写入：服务器运行后写 Warehouse；当前未产生 raw artifact。

agents 模式：`role_only`，server frozen runner，不创建线程。

runner_scope：100 jobs，20 candidates x 5 exact repeats。

formal_runner_allowed：pre-run gate 后可允许；当前未启动。

promotion gate：blocked。

下一步最小动作：生成本地 frozen plan 并验证。
