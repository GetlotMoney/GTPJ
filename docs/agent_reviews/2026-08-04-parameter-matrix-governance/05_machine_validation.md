# 机器验证记录

- 日期：2026-08-04
- 目的：确认正式参数表规则能运行，且不会破坏已有工作流。

## 已通过

`python -m py_compile workflow\\gtpj_workflow.py tests\\test_gtpj_workflow.py`

第一次实现的参数表专项测试共 7 项通过，已有流程回归测试共 5 项通过。

`python workflow\\gtpj_workflow.py validate`

`python workflow\\gtpj_workflow.py validate-workflow-consistency`

`python workflow\\gtpj_workflow.py audit-boundary`

`git diff --check`

第一次检查时，后续独立审核发现基础提交相对目标提交仍有两处空白格式问题，因此原先“以上命令均通过”的说法不完整，不能作为最终放行依据。

## 2026-08-05 修复后复验

- `python -m unittest -v`：199 项全部通过。
- 新增边界覆盖：完成行不能重复开跑、旧摘要不能冒充正式结果、CSV 多余单元格拒绝、普通 Attempt 建表入口、Warehouse 路径和清单身份、正式批次全部冻结字段核对、相同结果幂等同步与不同结果防覆盖。
- `python -m py_compile workflow\gtpj_workflow.py`：通过。
- `python workflow\gtpj_workflow.py validate`：通过。
- `python workflow\gtpj_workflow.py validate-workflow-consistency`：通过。
- `python workflow\gtpj_workflow.py audit-boundary`：通过。
- `git diff --check`：通过。

最终是否放行以新的三轮审核包为准。

第二次命名 Codex 复核随后又发现三条绕过路径：训练后补冻结手续、远端 manifest 不可访问时只靠自报哈希、历史模式夹带晋级字段。修复后增加了启动收据、真实 manifest 本地收据和历史降级持久化；上述 199 项是这些修复后的最终全量回归结果。

## 验证范围说明

本次未启动训练，也没有伪造历史 18 个 Attempt 的逐任务参数行；历史数据仍按迁移队列处理。
