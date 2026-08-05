# 机器验证记录

- 日期：2026-08-04
- 目的：确认正式参数表规则能运行，且不会破坏已有工作流。

## 已通过

`python -m py_compile workflow\\gtpj_workflow.py tests\\test_gtpj_workflow.py`

参数表专项测试共 7 项通过，覆盖：真实参数行读取、动态路由建表和回写、阅读版过期检查、跨版本重复判断、Top-Rank 解析、结果回写门禁，以及多行逐步冻结。

已有流程回归测试共 5 项通过，覆盖调参结果记录、工作目录状态、动态路由计划和运行产物。

`python workflow\\gtpj_workflow.py validate`

`python workflow\\gtpj_workflow.py validate-workflow-consistency`

`python workflow\\gtpj_workflow.py audit-boundary`

`git diff --check`

以上命令均通过。

## 验证范围说明

本次未启动训练，也没有伪造历史 18 个 Attempt 的逐任务参数行；历史数据仍按迁移队列处理。
