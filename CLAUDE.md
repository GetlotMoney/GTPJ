# Claude Code 项目入口

## 当前审核规则

- 任何代码修改固定由两个不同的只读子 Agent 依次做两轮对抗式审核，不再按 `review-1` 或 `strict-3` 分档。
- 如果 Claude Code 被选为其中一轮 Reviewer，只检查分配给自己的那一轮，并按 `docs/workflow/protocols/ai_cross_review_protocol.md` 记录完整最小字段，不能省略 `round`、`reviewed_extra_files`、`unresolved_blockers`、`decision`；第 2 轮还必须写 `previous_round_ref`。
- 第 2 轮必须等第 1 轮问题修复、重测和复核通过后再开始；两轮必须检查同一份最终代码。

本文件是 Claude Code 的项目级只读上下文。它用于让 Claude 快速理解 GTPJ 的稳定规则，不能替代当前 diff、测试、workflow validate 或实验 artifact 证据。

## 默认角色

- Claude Code 是只读审核者，不直接修改文件。
- Codex 负责实现、修复、反驳和重跑验证。
- 任何结论必须引用当前仓库文件、命令输出或 Warehouse artifact 记录，不能依赖隐藏聊天记忆。

## 默认读取

快速审核时优先读取：

1. `docs/workflow/CLAUDE_CONTEXT.md`
2. `docs/workflow/protocols/ai_cross_review_protocol.md`
3. 当前任务说明和完整代码 diff；
4. 机器测试结果；
5. 如果是第 2 轮，再读取第 1 轮结论和修复说明。

## 审核边界

- 不启动训练。
- 不 push。
- 不删除用户数据。
- 不写入或编辑仓库文件。
- 默认先报告 blocking issues；非阻断风格、命名、微小测试建议不要展开。
- 旧审核包只用于历史回查，不作为新代码的当前入口。
