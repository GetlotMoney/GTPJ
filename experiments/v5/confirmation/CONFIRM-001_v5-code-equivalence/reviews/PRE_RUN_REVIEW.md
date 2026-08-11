# V5-CONFIRM-001 开跑前审核记录

## 为什么做三路审核

这次同时触及历史代码复现、今天代码正式确认、双 GPU 调度和论文结论依据，出错会造成 15 次高成本训练白跑，因此使用三路独立审核。

## 审核候选

`e612bd011d258163dd36074913c246883a4f4c44`

## 三路结论

| 检查方向 | 审核者 | 结论 | 主要证据 |
|---|---|---|---|
| 服务器运行与恢复 | `/root/r5_recovery_audit` | PASS | bundle 三提交、只读数据、波次失败总闸、早期失败证据均通过 |
| 科学含义 | `/root/scientific_semantics_review` | PASS | 三份配置、实际训练提交、GZSL 指标和 15 项身份一致 |
| 证据与发布可靠性 | `/root/release_reliability_review` | PASS | 启动门、GPU 锁、永久领取、审核后白名单和结果清单闭环 |

## 机器验证

- `python -m unittest tests.test_v5_code_equivalence_server -v`：18/18 通过。
- `python -m py_compile tools/run_v5_code_equivalence_server.py`：通过。
- 服务器真实预检：三份配置、完整 bundle、约 10GB 数据哈希、bwrap 只读数据探针、GPU 0/1 空闲全部通过。

## 最终决定

三路均无剩余阻断，允许只在审核候选之后追加本审核记录和开跑门文件；训练代码、配置、数据清单、参数矩阵、运行计划和控制器不得再改。

## R2 增量审核

- 审核候选：`5e99a20fa2c284391d09bb9d34f35238eacf8df9`。
- 触发原因：R1 的旧 V5 在训练前因无可写临时目录退出；R2 仅增加 bubblewrap 内部私有 `/tmp`，并为全部任务换用新编号。
- 服务器运行与恢复：`/root/r5_recovery_audit`，**PASS**。R1 原始证据与封存表一致，R2 编号与 R1 无交集，正式数据仍只读。
- 科学含义：`/root/scientific_semantics_review`，**PASS**。模型、训练入口、评估、数据清单和三份配置均未改变；R1 没有指标，R2 仍是三组各五次、统一 `seed=5`。
- 证据与发布可靠性：`/root/release_reliability_review`，**PASS**。15 个 R2 身份唯一，计划与两张实验表一致，服务器永久领取无冲突。
- 机器验证：专项测试 18/18、Python 编译、参数矩阵、实验基点、框架台账和服务器私有临时目录探针全部通过；GPU 0/1 空闲。
- 最终决定：允许在候选之后只修改审核记录和启动门文件，再生成绑定最终提交的精确代码包；不允许再改训练代码、配置、数据清单、参数矩阵、运行计划或控制器。
