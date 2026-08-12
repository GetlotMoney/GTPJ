# 两轮对抗式代码审核规范

## 目的

代码能运行不等于代码正确。固定用两个不同的只读子 Agent 依次找错，可以减少实现者和单一 Reviewer 共享盲区的风险，同时不再使用旧的一轮/三轮分档、命名审核线程和多文件审核包。

## 哪些改动必须审核

以下改动都按代码修改处理，必须完成两轮审核：

- 模型、forward、loss、训练入口、数据读取、数据划分、评估、label/class order、指标计算；
- workflow、helper、脚本、测试、配置 schema/解析/生成逻辑、模板和训练配置生成逻辑；
- 会改变配置解释方式或正式运行门槛的规范文件。

普通说明文档、账本值，或已审核代码明确支持的普通超参数/seed 修改，只要不改 schema、解析/生成逻辑、数据/划分、评估语义、工作流门槛，也不打开未审核代码路径，就可以只做机器检查。

## 固定顺序

1. Implementer 完成代码和目标机器测试，确定本次 `reviewed_code_id`。
2. 只读子 Agent A 做第 1 轮，主动寻找需求偏差、实现错误、接口、shape、梯度、数据与评估边界问题。
3. Implementer 修复问题并重跑测试；A 复核到 `pass`。
4. 不同的只读子 Agent B 才能开始第 2 轮。B 检查同一份最终代码，重点寻找反例、隐藏耦合、回归、测试盲区和结论污染。
5. 两轮均为 `pass` 且 `unresolved_blockers: 0`，代码才算完成并允许正式训练。

其他只读工作可以并行，但第 2 轮不能与第 1 轮并行。若第 2 轮促成被审核代码再次修改，旧结论全部失效；仍由 A、B 按上述顺序重新审核最终代码，不增加第三个 Reviewer。

## 审核必须绑定最终代码

两轮必须写相同的 `reviewed_code_id`：

- 已有冻结提交：`commit:<40位SHA>`；
- 尚未提交：`diff_sha256:<64位SHA>`，哈希对象是 `git diff HEAD --binary -- <审核文件列表>` 输出的原始字节，它同时覆盖 staged 和 unstaged tracked 修改；Windows 下统一在 Git Bash 中管道给 `sha256sum`，避免 PowerShell 文本管道改变换行。

范围内的 untracked 文件或仓库外文件不会出现在 tracked diff 中，必须另用 `reviewed_extra_files` 按规范化路径排序，逐项记录文件 SHA-256；两轮的列表和哈希必须完全相同。只改审核记录、不改被审核代码时，代码身份不变；任何被审核代码或额外文件变化都会让旧结论失效。

## 从审核差异到正式运行提交

普通开发任务可以用 diff 身份完成审核，但正式 Runner 最终只能使用已冻结的 `commit:<sha>`。如果两轮审核发生在提交前，freeze 后由 Coordinator 只读完成一次等价确认：提交中的审核范围内容必须与已审核 tracked diff 和 `reviewed_extra_files` 完全相同，不能漏文件、夹带代码或改变内容。确认后记录：

```text
frozen_run_commit: <40位SHA>
freeze_equivalence: pass
```

不一致时旧审核失效，针对最终提交重新执行第 1 轮和第 2 轮。影响运行的额外文件必须进入 commit，或由现有数据/配置冻结身份单独锁定；否则不能正式开跑。

## 最小记录

每轮复用当前任务输出或现有实验质量记录，不默认新建审核包。至少记录：

```text
round: 1 | 2
reviewer_id:
reviewed_code_id:
reviewed_extra_files:        # 无则写 []；否则为排序后的 path=SHA256
previous_round_ref:          # 第 2 轮必填
files_reviewed:
machine_test_ref:
findings:
unresolved_blockers: 0
decision: pass | blocked
uncovered_scope:
```

Reviewer 只读，不修改文件、不启动正式训练、不 push、不删除数据。主助手自审不能替代任一轮，同一个子 Agent 不能重复计算为两轮。

## 开跑前检查

正式训练前，Coordinator 只检查以下事项：

- 两个不同的真实子 Agent；
- 第 2 轮晚于第 1 轮收口；
- 两轮 `reviewed_code_id` 相同并对应最终代码；
- 两轮 `reviewed_extra_files` 完全相同，并覆盖审核范围内的 untracked 与仓库外文件；
- 第 2 轮的 `previous_round_ref` 指向已收口的第 1 轮；
- 机器测试引用有效；
- 两轮均 `decision: pass` 且 `unresolved_blockers: 0`；
- 正式 Runner 的 `frozen_run_commit` 已记录，且 `freeze_equivalence: pass`。

任一项缺失就停止正式训练，只修真实阻断。当前阶段由 Coordinator 按记录检查，不为这条规则新增控制器、状态机或多文件证据包；自动校验只有在反复出现漏审时才另立任务。

## 历史兼容

旧的 `run-ai-cross-review` 生成入口已退役，不能再创建旧式审核包；`validate-ai-cross-review` 只用于只读校验已经存在的历史包。新代码一律使用本规范的两轮子 Agent 审核，除非 owner 在当前任务中明确要求特殊审计。
