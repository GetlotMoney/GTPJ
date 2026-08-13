# GTPJ 工作流内核

本文件是精简后的硬规则层，应该保持短而稳定。

## 当前执行内核：SYS-WORKFLOW-V6

正式实验和论文实验统一使用下面这条最短闭环：

```text
唯一实验提交 + 配置/参数表 + 一次开跑检查
-> 直接训练到独立 RUN 目录
-> 回填全部指标和结论
```

必须保留：准确 commit、clean checkout、配置快照、数据/划分身份、seed、评估口径、逐 RUN 的 U/S/H/ZS、日志和不覆盖历史结果。

默认只执行上述最短闭环。只有当前实验出现可说明、可验证的真实风险时，才增加直接解决该风险的最小机制。

审核规则：机器测试优先。普通说明文档、账本值，或已审核代码明确支持的普通超参数/seed 修改，只要不改 schema、解析/生成逻辑、数据/划分、评估语义、工作流门槛，也不打开未审核代码路径，就默认 0 次独立审核；其他配置、模板和工作流规则修改按代码修改处理。任何代码修改，包括模型、训练、数据、评估、workflow、helper、模板和训练配置生成逻辑，都固定执行下面 2 轮对抗式只读审核：

1. 第 1 轮由子 Agent A 检查需求对应、实现正确性、接口、shape、梯度、数据与评估边界，并主动尝试证明代码有错。实现者修复并重跑机器测试后，由 A 复核到通过。
2. 第 2 轮由不同的子 Agent B 检查与第 1 轮相同的最终代码，重点寻找反例、隐藏耦合、回归、测试盲区和结论污染。

同一个子 Agent 不能计算为两轮，主助手自审不能替代子 Agent。其他只读角色可以并行，但第 2 轮必须等待第 1 轮问题修复、重测和 A 复核通过后再启动。若第 2 轮导致被审核代码改变，两轮都要针对最终代码重新执行；仍使用 A、B，不增加第三个 Reviewer。

两轮必须绑定同一个 `reviewed_code_id`：有冻结提交时写准确 commit；尚未提交时写包含 staged/unstaged tracked diff 的 SHA-256，并用 `reviewed_extra_files` 记录范围内 untracked 或仓库外文件的排序后路径与 SHA-256。每轮至少记录 `round`、`reviewer_id`、`reviewed_code_id`、`reviewed_extra_files`、`files_reviewed`、`machine_test_ref`、发现、`unresolved_blockers`、`decision` 和 `uncovered_scope`；第 2 轮另写 `previous_round_ref`。两轮都为 `decision: pass`、`unresolved_blockers: 0` 后，代码才允许正式训练。记录复用当前任务输出或现有实验质量记录，默认不新建审核包。

正式 Runner 最终只能绑定已冻结的 `commit:<sha>`。若两轮先审核 diff，freeze 后由 Coordinator 只读确认该 commit 的审核范围内容与已审核 diff、`reviewed_extra_files` 完全一致，并记录 `frozen_run_commit` 和 `freeze_equivalence: pass`；staging/commit 漏文件、夹带代码或内容变化都会使旧审核失效。影响运行的额外文件必须进入 commit 或已有的数据/配置冻结身份，否则阻断。

时间规则：参数实验准备不超过 10 分钟；代码或评估实验准备不超过 30 分钟。达到上限仍不能训练时，停止扩建流程，报告唯一阻断和最小修复。

旧版完整规则统一保存在 `archive/specs/WORKFLOW_PRE_V6_ARCHIVE.md`，只供历史回查，不再作为新代码入口。
